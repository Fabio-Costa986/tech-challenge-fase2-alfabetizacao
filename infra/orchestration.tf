resource "google_workflows_workflow" "batch" {
  name            = "alfab-pipeline-batch"
  region          = var.region
  description     = "Bronze -> Silver (portão de qualidade) -> Gold staging (portão) -> publicação"
  service_account = google_service_account.orchestrator.email
  call_log_level  = "LOG_ERRORS_ONLY"
  labels          = { app = "alfab" }
  source_contents = templatefile("${path.module}/../workflows/pipeline_batch.yaml", {
    project = var.project_id
    region  = var.region
  })
  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "batch" {
  name        = "alfab-batch"
  region      = var.region
  description = "Dispara o workflow batch (o watermark pula fontes inalteradas)"
  schedule    = var.batch_schedule
  time_zone   = "America/Sao_Paulo"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "https://workflowexecutions.googleapis.com/v1/${google_workflows_workflow.batch.id}/executions"
    body        = base64encode(jsonencode({ argument = jsonencode({}) }))
    headers     = { "Content-Type" = "application/json" }
    oauth_token {
      service_account_email = google_service_account.orchestrator.email
    }
  }
}

resource "google_cloud_scheduler_job" "microbatch" {
  name        = "alfab-microbatch"
  region      = var.region
  description = "Micro-lote Bronze -> Silver dos eventos de streaming"
  schedule    = var.microbatch_schedule
  time_zone   = "America/Sao_Paulo"

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.job["microbatch"].name}:run"
    oauth_token {
      service_account_email = google_service_account.orchestrator.email
    }
  }
}
