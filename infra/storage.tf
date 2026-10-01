# Lake: Bronze imutável (Parquet ZSTD) + snapshots da base de ML.
resource "google_storage_bucket" "lake" {
  name                        = var.bronze_bucket
  location                    = var.bq_location # US: compatível com EXPORT DATA a partir de datasets US
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  # Histórico preservado: nenhum objeto pode ser apagado/sobrescrito antes do prazo.
  # Não travada (is_locked=false) para o ambiente acadêmico poder ser desmontado depois.
  retention_policy {
    retention_period = var.bronze_retention_days * 86400
    is_locked        = false
  }

  lifecycle_rule {
    condition {
      age            = 30
      matches_prefix = ["bronze/"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age            = 90
      matches_prefix = ["bronze/"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  labels = { app = "alfab" }

  depends_on = [google_project_service.apis]
}
