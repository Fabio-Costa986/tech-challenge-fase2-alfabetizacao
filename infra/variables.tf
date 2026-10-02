variable "project_id" {
  description = "ID do projeto GCP"
  type        = string
}

variable "region" {
  description = "Região de Cloud Run, Workflows e Scheduler"
  type        = string
  default     = "us-central1"
}

variable "bq_location" {
  description = "Localização dos datasets e do bucket. US: mesma do dataset público da Base dos Dados (sem egress, joins permitidos)."
  type        = string
  default     = "US"
}

variable "bronze_bucket" {
  description = "Nome globalmente único do bucket do lake"
  type        = string
}

variable "alert_email" {
  description = "E-mail que recebe os alertas do pipeline"
  type        = string
}

variable "alert_webhook_url" {
  description = "Webhook opcional (Google Chat/Discord/Slack) para alertas. Vazio = desativado."
  type        = string
  default     = ""
  sensitive   = true
}

variable "image" {
  description = "Imagem do container (Artifact Registry). Placeholder até o primeiro build."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "bronze_retention_days" {
  description = "Retention policy do bucket: objetos não podem ser apagados antes disso (histórico da Bronze)."
  type        = number
  default     = 30
}

variable "batch_schedule" {
  description = "Cron do pipeline batch (fuso America/Sao_Paulo). A cada 6h: barato porque o watermark pula fonte inalterada."
  type        = string
  default     = "0 */6 * * *"
}

variable "microbatch_schedule" {
  description = "Cron do micro-lote de streaming"
  type        = string
  default     = "*/5 * * * *"
}

variable "max_bytes_billed" {
  description = "Limite de bytes faturados por query (guarda-corpo de FinOps)"
  type        = number
  default     = 53687091200
}

variable "billing_account" {
  description = "ID da conta de faturamento para o budget. Vazio = budget não é criado."
  type        = string
  default     = ""
}

variable "budget_amount_usd" {
  description = "Orçamento mensal (USD) com alertas em 50/90/100%"
  type        = number
  default     = 20
}

variable "deletion_protection" {
  description = "Protege tabelas Bronze/ops contra destroy acidental"
  type        = bool
  default     = true
}

variable "schedulers_paused" {
  description = "Cria os Cloud Scheduler pausados. Ativar (false) só depois do deploy da imagem real e de um pipeline bem-sucedido."
  type        = bool
  default     = true
}
