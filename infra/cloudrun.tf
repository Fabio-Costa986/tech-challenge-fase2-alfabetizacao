resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "alfab"
  format        = "DOCKER"
  description   = "Imagem única do pipeline (jobs + event-ingestor)"
  depends_on    = [google_project_service.apis]

  cleanup_policies {
    id     = "manter-10-ultimas"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }
}

locals {
  common_env = {
    GCP_PROJECT_ID   = var.project_id
    BQ_LOCATION      = var.bq_location
    GCP_REGION       = var.region
    BRONZE_BUCKET    = var.bronze_bucket
    PUBSUB_TOPIC     = google_pubsub_topic.eventos.name
    MAX_BYTES_BILLED = tostring(var.max_bytes_billed)
  }

  # nome => (args da CLI, retries do Cloud Run, timeout, memória)
  jobs = {
    "ingest-bronze" = { args = ["ingest-bronze"], retries = 1, timeout = "1800s", memory = "2Gi" }
    "dbt-silver"    = { args = ["dbt", "--layer", "silver"], retries = 0, timeout = "3600s", memory = "2Gi" }
    "dbt-gold"      = { args = ["dbt", "--layer", "gold"], retries = 0, timeout = "3600s", memory = "2Gi" }
    "publish-gold"  = { args = ["publish-gold"], retries = 1, timeout = "900s", memory = "1Gi" }
    "microbatch"    = { args = ["microbatch"], retries = 1, timeout = "600s", memory = "1Gi" }
    "simulator"     = { args = ["simulate", "--n", "600", "--rate", "10"], retries = 0, timeout = "1800s", memory = "1Gi" }
    "export-ml"     = { args = ["export-ml"], retries = 1, timeout = "900s", memory = "1Gi" }
  }
}

resource "google_cloud_run_v2_job" "job" {
  for_each            = local.jobs
  name                = "alfab-${each.key}"
  location            = var.region
  deletion_protection = false
  labels              = { app = "alfab" }

  template {
    task_count = 1
    template {
      service_account = google_service_account.pipeline.email
      max_retries     = each.value.retries
      timeout         = each.value.timeout
      containers {
        image = var.image
        args  = each.value.args
        resources {
          limits = { cpu = "1", memory = each.value.memory }
        }
        dynamic "env" {
          for_each = local.common_env
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_service" "ingestor" {
  name                = "alfab-event-ingestor"
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL" # autenticação obrigatória (sem allUsers invoker)
  labels              = { app = "alfab" }

  template {
    service_account = google_service_account.ingestor.email
    scaling {
      min_instance_count = 0 # escala a zero: custo só quando há eventos
      max_instance_count = 3
    }
    containers {
      image = var.image
      args  = ["serve"]
      resources {
        limits   = { cpu = "1", memory = "512Mi" }
        cpu_idle = true
      }
      dynamic "env" {
        for_each = local.common_env
        content {
          name  = env.key
          value = env.value
        }
      }
      startup_probe {
        http_get {
          path = "/healthz"
        }
      }
    }
  }

  # A API devolve um bloco `scaling` no nível do serviço (não declarado aqui): evita diff perpétuo.
  lifecycle {
    ignore_changes = [scaling]
  }

  depends_on = [google_project_service.apis]
}
