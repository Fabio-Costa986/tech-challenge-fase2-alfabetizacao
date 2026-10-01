# Uma service account por papel, com o mínimo necessário. Nenhuma chave é gerada:
# os serviços usam a identidade anexada (metadata server).

resource "google_service_account" "pipeline" {
  account_id   = "alfab-pipeline"
  display_name = "alfab - jobs batch/dbt/micro-lote/simulador"
}

resource "google_service_account" "ingestor" {
  account_id   = "alfab-ingestor"
  display_name = "alfab - event-ingestor (Cloud Run service)"
}

resource "google_service_account" "pubsub_push" {
  account_id   = "alfab-pubsub-push"
  display_name = "alfab - identidade OIDC do push do Pub/Sub"
}

resource "google_service_account" "orchestrator" {
  account_id   = "alfab-orchestrator"
  display_name = "alfab - Workflows e Cloud Scheduler"
}

# --- pipeline: executa queries, escreve nos datasets, lê/escreve o lake, publica eventos
resource "google_project_iam_member" "pipeline_roles" {
  for_each = toset([
    "roles/bigquery.jobUser",
    "roles/bigquery.dataEditor",
    "roles/logging.logWriter",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_storage_bucket_iam_member" "pipeline_lake" {
  bucket = google_storage_bucket.lake.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_pubsub_topic_iam_member" "pipeline_publish" {
  topic  = google_pubsub_topic.eventos.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.pipeline.email}"
}

# --- ingestor: só grava nas duas tabelas de entrada de eventos
resource "google_bigquery_table_iam_member" "ingestor_raw" {
  for_each   = { raw = google_bigquery_table.eventos_raw.table_id, quarentena = google_bigquery_table.eventos_quarentena.table_id }
  project    = var.project_id
  dataset_id = google_bigquery_dataset.ds["bronze"].dataset_id
  table_id   = each.value
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.ingestor.email}"
}

resource "google_project_iam_member" "ingestor_log" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.ingestor.email}"
}

# --- push do Pub/Sub: pode invocar apenas o ingestor
resource "google_cloud_run_v2_service_iam_member" "push_invoker" {
  name     = google_cloud_run_v2_service.ingestor.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.pubsub_push.email}"
}

# O agente de serviço do Pub/Sub emite o token OIDC e usa a DLQ
locals {
  pubsub_agent = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "pubsub_token_creator" {
  service_account_id = google_service_account.pubsub_push.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = local.pubsub_agent
}

resource "google_pubsub_topic_iam_member" "dlq_publisher" {
  topic  = google_pubsub_topic.dlq.id
  role   = "roles/pubsub.publisher"
  member = local.pubsub_agent
}

resource "google_pubsub_subscription_iam_member" "dlq_subscriber" {
  subscription = google_pubsub_subscription.push.id
  role         = "roles/pubsub.subscriber"
  member       = local.pubsub_agent
}

# --- orquestrador: dispara jobs (com override de env: run_id) e workflows
resource "google_project_iam_member" "orchestrator_roles" {
  for_each = toset([
    "roles/run.developer", # jobs.runWithOverrides (injeta ALFAB_RUN_ID)
    "roles/workflows.invoker",
    "roles/logging.logWriter",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

resource "google_service_account_iam_member" "orchestrator_act_as_pipeline" {
  service_account_id = google_service_account.pipeline.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.orchestrator.email}"
}
