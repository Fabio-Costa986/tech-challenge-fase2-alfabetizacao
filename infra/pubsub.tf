resource "google_pubsub_topic" "eventos" {
  name                       = "alfab-eventos"
  message_retention_duration = "604800s" # 7 dias = horizonte de dedup do micro-lote
  labels                     = { app = "alfab" }
  depends_on                 = [google_project_service.apis]
}

resource "google_pubsub_topic" "dlq" {
  name   = "alfab-eventos-dlq"
  labels = { app = "alfab" }
}

# Subscription de inspeção da DLQ (mensagens que falharam N entregas). O alerta observa o backlog dela.
resource "google_pubsub_subscription" "dlq_inspect" {
  name                       = "alfab-eventos-dlq-inspect"
  topic                      = google_pubsub_topic.dlq.id
  message_retention_duration = "604800s"
  ack_deadline_seconds       = 60
}

# Push autenticado (OIDC) para o event-ingestor. Entrega at-least-once.
resource "google_pubsub_subscription" "push" {
  name                 = "alfab-eventos-push"
  topic                = google_pubsub_topic.eventos.id
  ack_deadline_seconds = 30

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.ingestor.uri}/pubsub/push"
    oidc_token {
      service_account_email = google_service_account.pubsub_push.email
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlq.id
    max_delivery_attempts = 5
  }

  expiration_policy {
    ttl = "" # nunca expira
  }
}
