# Notificação + métricas + alertas. Tudo aqui é provisionado de verdade por `terraform apply`.

resource "google_monitoring_notification_channel" "email" {
  display_name = "alfab - e-mail do grupo"
  type         = "email"
  labels       = { email_address = var.alert_email }
  depends_on   = [google_project_service.apis]
}

resource "google_monitoring_notification_channel" "webhook" {
  count        = var.alert_webhook_url == "" ? 0 : 1
  display_name = "alfab - webhook"
  type         = "webhook_tokenauth"
  labels       = { url = var.alert_webhook_url }
}

locals {
  channels = concat(
    [google_monitoring_notification_channel.email.id],
    [for c in google_monitoring_notification_channel.webhook : c.id],
  )
}

# ------------------------------------------------------------- métricas baseadas em log
# Os jobs emitem JSON estruturado (src/alfab/observability.py): jsonPayload.event, status, pipeline...
resource "google_logging_metric" "step_failed" {
  name   = "alfab/step_failed"
  filter = "resource.type=\"cloud_run_job\" AND jsonPayload.event=\"step_finished\" AND jsonPayload.status=\"FAILED\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    labels {
      key        = "step"
      value_type = "STRING"
    }
  }
  label_extractors = { step = "EXTRACT(jsonPayload.step)" }
}

resource "google_logging_metric" "batch_succeeded" {
  name   = "alfab/batch_pipeline_succeeded"
  filter = "resource.type=\"workflows.googleapis.com/Workflow\" AND jsonPayload.event=\"workflow_succeeded\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

resource "google_logging_metric" "rows_processed" {
  name            = "alfab/rows_out"
  filter          = "resource.type=\"cloud_run_job\" AND jsonPayload.event=\"step_finished\" AND jsonPayload.status=\"SUCCEEDED\""
  value_extractor = "EXTRACT(jsonPayload.rows_out)"
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "DISTRIBUTION"
    labels {
      key        = "step"
      value_type = "STRING"
    }
  }
  label_extractors = { step = "EXTRACT(jsonPayload.step)" }
  bucket_options {
    exponential_buckets {
      num_finite_buckets = 30
      growth_factor      = 4
      scale              = 1
    }
  }
}

resource "google_logging_metric" "stream_latency_p95" {
  name            = "alfab/stream_latency_p95_s"
  filter          = "resource.type=\"cloud_run_job\" AND jsonPayload.event=\"stream_microbatch\""
  value_extractor = "EXTRACT(jsonPayload.latencia_ingestao_p95_s)"
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "DISTRIBUTION"
  }
  bucket_options {
    exponential_buckets {
      num_finite_buckets = 20
      growth_factor      = 2
      scale              = 0.1
    }
  }
}

resource "google_logging_metric" "quarantine_rate" {
  name            = "alfab/stream_quarantine_rate"
  filter          = "resource.type=\"cloud_run_job\" AND jsonPayload.event=\"stream_microbatch\""
  value_extractor = "EXTRACT(jsonPayload.quarantine_rate)"
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "DISTRIBUTION"
  }
  bucket_options {
    linear_buckets {
      num_finite_buckets = 20
      width              = 0.05
      offset             = 0
    }
  }
}

# ------------------------------------------------------------- alertas
resource "google_monitoring_alert_policy" "step_failed" {
  display_name          = "alfab: etapa do pipeline FALHOU"
  combiner              = "OR"
  notification_channels = local.channels
  documentation {
    content   = "Uma etapa registrou status=FAILED. Ver ops.pipeline_runs (coluna error) e ops.vw_resumo_qualidade. Código 3 = regra bloqueante de qualidade; 1 = erro de execução."
    mime_type = "text/markdown"
  }
  conditions {
    display_name = "step_failed > 0"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.step_failed.name}\" AND resource.type=\"cloud_run_job\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_SUM"
      }
      trigger { count = 1 }
    }
  }
  alert_strategy { auto_close = "86400s" }
}

resource "google_monitoring_alert_policy" "job_execution_failed" {
  display_name          = "alfab: execução de Cloud Run Job falhou"
  combiner              = "OR"
  notification_channels = local.channels
  documentation {
    content = "Cobre falhas que acontecem antes do log estruturado (imagem, OOM, timeout)."
  }
  conditions {
    display_name = "completed_execution_count{result=failed} > 0"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/job/completed_execution_count\" AND resource.type=\"cloud_run_job\" AND metric.labels.result=\"failed\" AND resource.labels.job_name=starts_with(\"alfab-\")"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }
  alert_strategy { auto_close = "86400s" }
}

resource "google_monitoring_alert_policy" "batch_absent" {
  display_name          = "alfab: pipeline batch sem sucesso há 13h"
  combiner              = "OR"
  notification_channels = local.channels
  documentation {
    content = "Falha silenciosa: o batch roda a cada 6h; 13h sem workflow_succeeded significa que duas execuções seguidas não concluíram (ou o Scheduler parou)."
  }
  conditions {
    display_name = "ausência de batch_pipeline_succeeded"
    condition_absent {
      filter   = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.batch_succeeded.name}\" AND resource.type=\"workflows.googleapis.com/Workflow\""
      duration = "46800s"
      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }
}

resource "google_monitoring_alert_policy" "stream_backlog" {
  display_name          = "alfab: backlog do streaming > 5 min"
  combiner              = "OR"
  notification_channels = local.channels
  conditions {
    display_name = "oldest_unacked_message_age > 300s"
    condition_threshold {
      filter          = "metric.type=\"pubsub.googleapis.com/subscription/oldest_unacked_message_age\" AND resource.type=\"pubsub_subscription\" AND resource.labels.subscription_id=\"${google_pubsub_subscription.push.name}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 300
      duration        = "300s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }
}

resource "google_monitoring_alert_policy" "dlq_not_empty" {
  display_name          = "alfab: mensagens na dead-letter queue"
  combiner              = "OR"
  notification_channels = local.channels
  documentation {
    content = "Mensagens que falharam 5 entregas (ingestor retornou 5xx). Inspecionar a subscription alfab-eventos-dlq-inspect."
  }
  conditions {
    display_name = "num_undelivered_messages > 0"
    condition_threshold {
      filter          = "metric.type=\"pubsub.googleapis.com/subscription/num_undelivered_messages\" AND resource.type=\"pubsub_subscription\" AND resource.labels.subscription_id=\"${google_pubsub_subscription.dlq_inspect.name}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }
}

resource "google_monitoring_alert_policy" "stream_latency" {
  display_name          = "alfab: latência p95 de ingestão do streaming > 60s"
  combiner              = "OR"
  notification_channels = local.channels
  conditions {
    display_name = "p95 > 60s"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.stream_latency_p95.name}\" AND resource.type=\"cloud_run_job\""
      comparison      = "COMPARISON_GT"
      threshold_value = 60
      duration        = "0s"
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
        cross_series_reducer = "REDUCE_MAX"
      }
    }
  }
}

resource "google_monitoring_alert_policy" "quarantine_rate" {
  display_name          = "alfab: taxa de quarentena do streaming > 10%"
  combiner              = "OR"
  notification_channels = local.channels
  conditions {
    display_name = "quarantine_rate > 0.10"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.quarantine_rate.name}\" AND resource.type=\"cloud_run_job\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.10
      duration        = "0s"
      aggregations {
        alignment_period     = "900s"
        per_series_aligner   = "ALIGN_PERCENTILE_50"
        cross_series_reducer = "REDUCE_MAX"
      }
    }
  }
}

# ------------------------------------------------------------- FinOps
resource "google_billing_budget" "budget" {
  count           = var.billing_account == "" ? 0 : 1
  billing_account = var.billing_account
  display_name    = "alfab - orçamento mensal"

  budget_filter {
    projects = ["projects/${data.google_project.this.number}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.budget_amount_usd)
    }
  }

  dynamic "threshold_rules" {
    for_each = [0.5, 0.9, 1.0]
    content {
      threshold_percent = threshold_rules.value
    }
  }

  all_updates_rule {
    monitoring_notification_channels = [google_monitoring_notification_channel.email.id]
    disable_default_iam_recipients   = false
  }
}
