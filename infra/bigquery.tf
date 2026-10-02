locals {
  datasets = {
    bronze       = "Bronze: external tables sobre Parquet imutável + eventos brutos do streaming"
    silver       = "Silver: dados tratados, tipados, decodificados e integrados"
    gold_staging = "Gold em auditoria: construída e testada pelo dbt antes da publicação"
    gold         = "Gold publicada: só recebe tabelas que passaram em todos os testes bloqueantes"
    ops          = "Observabilidade: execuções, qualidade, watermarks e views de monitoramento"
  }
  region_qualifier = "region-${lower(var.bq_location)}"
}

resource "google_bigquery_dataset" "ds" {
  for_each                   = local.datasets
  dataset_id                 = each.key
  description                = each.value
  location                   = var.bq_location
  delete_contents_on_destroy = false
  labels                     = { app = "alfab", camada = each.key }
  depends_on                 = [google_project_service.apis]
}

# ---------------------------------------------------------------- ops (append-only)
resource "google_bigquery_table" "pipeline_runs" {
  dataset_id          = google_bigquery_dataset.ds["ops"].dataset_id
  table_id            = "pipeline_runs"
  description         = "Uma linha por etapa executada. Acumula execuções (nunca sobrescreve)."
  deletion_protection = var.deletion_protection
  time_partitioning {
    type  = "DAY"
    field = "started_at"
  }
  clustering = ["pipeline", "step"]
  schema = jsonencode([
    { name = "run_id", type = "STRING", mode = "REQUIRED" },
    { name = "pipeline", type = "STRING", mode = "REQUIRED", description = "batch | stream" },
    { name = "step", type = "STRING", mode = "REQUIRED" },
    { name = "started_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "ended_at", type = "TIMESTAMP" },
    { name = "duration_s", type = "FLOAT64" },
    { name = "rows_in", type = "INT64" },
    { name = "rows_out", type = "INT64" },
    { name = "bytes_billed", type = "INT64" },
    { name = "status", type = "STRING", description = "SUCCEEDED | FAILED" },
    { name = "error", type = "STRING" },
    { name = "details", type = "STRING", description = "JSON com métricas específicas da etapa" },
  ])
}

resource "google_bigquery_table" "dq_results" {
  dataset_id          = google_bigquery_dataset.ds["ops"].dataset_id
  table_id            = "dq_results"
  description         = "Resultado de cada teste de qualidade (dbt on-run-end). Inclui reprovações."
  deletion_protection = var.deletion_protection
  time_partitioning {
    type  = "DAY"
    field = "executed_at"
  }
  schema = jsonencode([
    { name = "run_id", type = "STRING" },
    { name = "invocation_id", type = "STRING" },
    { name = "executed_at", type = "TIMESTAMP" },
    { name = "test_name", type = "STRING" },
    { name = "unique_id", type = "STRING" },
    { name = "attached_node", type = "STRING" },
    { name = "severidade", type = "STRING", description = "bloqueante | informativa" },
    { name = "status", type = "STRING", description = "pass | fail | warn | error | skipped" },
    { name = "failures", type = "INT64" },
    { name = "message", type = "STRING" },
    { name = "execution_time_s", type = "FLOAT64" },
    { name = "fault_injection", type = "STRING" },
  ])
}

resource "google_bigquery_table" "source_watermarks" {
  dataset_id          = google_bigquery_dataset.ds["ops"].dataset_id
  table_id            = "source_watermarks"
  description         = "last_modified da fonte por entidade a cada ingestão efetiva (detecção de atualização)."
  deletion_protection = var.deletion_protection
  schema = jsonencode([
    { name = "entity", type = "STRING", mode = "REQUIRED" },
    { name = "source_table", type = "STRING" },
    { name = "source_last_modified", type = "TIMESTAMP" },
    { name = "source_num_rows", type = "INT64" },
    { name = "run_id", type = "STRING" },
    { name = "bronze_uri", type = "STRING" },
    { name = "exported_rows", type = "INT64" },
    { name = "ingested_at", type = "TIMESTAMP" },
  ])
}

resource "google_bigquery_table" "stream_watermark" {
  dataset_id          = google_bigquery_dataset.ds["ops"].dataset_id
  table_id            = "stream_watermark"
  deletion_protection = var.deletion_protection
  schema = jsonencode([
    { name = "run_id", type = "STRING" },
    { name = "watermark", type = "TIMESTAMP" },
    { name = "processed_at", type = "TIMESTAMP" },
  ])
}

# ---------------------------------------------------------------- streaming
resource "google_bigquery_table" "eventos_raw" {
  dataset_id          = google_bigquery_dataset.ds["bronze"].dataset_id
  table_id            = "eventos_raw"
  description         = "Eventos válidos como chegaram (com duplicatas: entrega at-least-once). Somente INSERT."
  deletion_protection = var.deletion_protection
  time_partitioning {
    type  = "DAY"
    field = "ingested_at"
  }
  clustering = ["event_type"]
  schema = jsonencode([
    { name = "event_id", type = "STRING", mode = "REQUIRED" },
    { name = "event_type", type = "STRING", mode = "REQUIRED" },
    { name = "produced_at", type = "TIMESTAMP", mode = "REQUIRED", description = "carimbo do PRODUTOR" },
    { name = "ingested_at", type = "TIMESTAMP", mode = "REQUIRED", description = "carimbo do INGESTOR" },
    { name = "origem_dado", type = "STRING", mode = "REQUIRED" },
    { name = "id_municipio", type = "STRING" },
    { name = "rede", type = "STRING" },
    { name = "ano", type = "INT64" },
    { name = "payload", type = "STRING" },
    { name = "pubsub_message_id", type = "STRING" },
    { name = "pubsub_publish_time", type = "TIMESTAMP" },
    { name = "delivery_attempt", type = "INT64" },
  ])
}

resource "google_bigquery_table" "eventos_quarentena" {
  dataset_id          = google_bigquery_dataset.ds["bronze"].dataset_id
  table_id            = "eventos_quarentena"
  description         = "Eventos rejeitados (estrutura, domínio ou referência) com o motivo."
  deletion_protection = var.deletion_protection
  time_partitioning {
    type  = "DAY"
    field = "received_at"
  }
  schema = jsonencode([
    { name = "event_id", type = "STRING" },
    { name = "pubsub_message_id", type = "STRING" },
    { name = "pubsub_publish_time", type = "TIMESTAMP" },
    { name = "received_at", type = "TIMESTAMP" },
    { name = "raw_data", type = "STRING" },
    { name = "motivo_rejeicao", type = "STRING" },
    { name = "delivery_attempt", type = "INT64" },
  ])
}

resource "google_bigquery_table" "silver_eventos" {
  dataset_id          = google_bigquery_dataset.ds["silver"].dataset_id
  table_id            = "eventos"
  description         = "Eventos deduplicados por event_id (MERGE do micro-lote). origem_dado = SIMULADO."
  deletion_protection = var.deletion_protection
  time_partitioning {
    type  = "DAY"
    field = "ingested_at"
  }
  clustering = ["id_municipio", "event_type"]
  schema = jsonencode([
    { name = "event_id", type = "STRING", mode = "REQUIRED" },
    { name = "event_type", type = "STRING" },
    { name = "produced_at", type = "TIMESTAMP" },
    { name = "ingested_at", type = "TIMESTAMP" },
    { name = "silver_processed_at", type = "TIMESTAMP" },
    { name = "origem_dado", type = "STRING" },
    { name = "id_municipio", type = "STRING" },
    { name = "rede", type = "STRING" },
    { name = "ano", type = "INT64" },
    { name = "payload", type = "JSON" },
    { name = "_run_id", type = "STRING" },
  ])
}

# ---------------------------------------------------------------- views de monitoramento
resource "google_bigquery_table" "vw_latencia_streaming" {
  dataset_id          = google_bigquery_dataset.ds["ops"].dataset_id
  table_id            = "vw_latencia_streaming"
  deletion_protection = false
  view {
    use_legacy_sql = false
    query          = <<-SQL
      -- Latência medida entre dois relógios diferentes: produtor (produced_at) e ingestor (ingested_at)
      SELECT
        TIMESTAMP_SECONDS(DIV(UNIX_SECONDS(ingested_at), 300) * 300) AS janela_5min,
        COUNT(*) AS eventos,
        APPROX_QUANTILES(TIMESTAMP_DIFF(ingested_at, produced_at, MILLISECOND), 100)[OFFSET(50)] / 1000 AS p50_ingestao_s,
        APPROX_QUANTILES(TIMESTAMP_DIFF(ingested_at, produced_at, MILLISECOND), 100)[OFFSET(95)] / 1000 AS p95_ingestao_s,
        APPROX_QUANTILES(TIMESTAMP_DIFF(ingested_at, produced_at, MILLISECOND), 100)[OFFSET(99)] / 1000 AS p99_ingestao_s,
        APPROX_QUANTILES(TIMESTAMP_DIFF(silver_processed_at, produced_at, MILLISECOND), 100)[OFFSET(95)] / 1000 AS p95_ponta_a_ponta_s
      FROM `${var.project_id}.silver.eventos`
      WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
      GROUP BY janela_5min
    SQL
  }
  depends_on = [google_bigquery_table.silver_eventos]
}

resource "google_bigquery_table" "vw_saude_pipeline" {
  dataset_id          = google_bigquery_dataset.ds["ops"].dataset_id
  table_id            = "vw_saude_pipeline"
  deletion_protection = false
  view {
    use_legacy_sql = false
    query          = <<-SQL
      SELECT
        pipeline, step,
        MAX(IF(status = 'SUCCEEDED', ended_at, NULL)) AS ultimo_sucesso,
        MAX(IF(status = 'FAILED', ended_at, NULL)) AS ultima_falha,
        TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(IF(status = 'SUCCEEDED', ended_at, NULL)), MINUTE) / 60 AS horas_desde_sucesso,
        COUNTIF(status = 'FAILED') AS falhas_7d,
        COUNT(*) AS execucoes_7d,
        APPROX_QUANTILES(duration_s, 100)[OFFSET(50)] AS duracao_p50_s,
        SUM(rows_out) AS linhas_saida_7d,
        SUM(bytes_billed) AS bytes_faturados_7d
      FROM `${var.project_id}.ops.pipeline_runs`
      WHERE started_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
      GROUP BY pipeline, step
    SQL
  }
  depends_on = [google_bigquery_table.pipeline_runs]
}

resource "google_bigquery_table" "vw_custo_por_execucao" {
  dataset_id          = google_bigquery_dataset.ds["ops"].dataset_id
  table_id            = "vw_custo_por_execucao"
  deletion_protection = false
  view {
    use_legacy_sql = false
    query          = <<-SQL
      -- Custo atribuído por label run_id (todo job do pipeline é rotulado)
      SELECT
        (SELECT value FROM UNNEST(labels) WHERE key = 'run_id') AS run_id,
        (SELECT value FROM UNNEST(labels) WHERE key = 'camada') AS camada,
        MIN(creation_time) AS inicio,
        COUNT(*) AS jobs,
        SUM(total_bytes_processed) AS bytes_processados,
        SUM(total_bytes_billed) AS bytes_faturados,
        ROUND(SUM(total_bytes_billed) / POW(1024, 4) * 6.25, 6) AS custo_on_demand_usd
      FROM `${var.project_id}`.`${local.region_qualifier}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
      WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        AND EXISTS (SELECT 1 FROM UNNEST(labels) WHERE key = 'app' AND value = 'alfab')
      GROUP BY run_id, camada
    SQL
  }
}

resource "google_bigquery_table" "vw_resumo_qualidade" {
  dataset_id          = google_bigquery_dataset.ds["ops"].dataset_id
  table_id            = "vw_resumo_qualidade"
  deletion_protection = false
  view {
    use_legacy_sql = false
    query          = <<-SQL
      SELECT run_id, fault_injection, MIN(executed_at) AS executado_em,
        COUNTIF(status = 'pass') AS aprovados,
        COUNTIF(status = 'fail' AND severidade = 'bloqueante') AS bloqueantes_reprovados,
        COUNTIF(status = 'warn') AS informativos_alertados,
        COUNTIF(status = 'error') AS erros,
        ARRAY_AGG(IF(status IN ('fail', 'warn', 'error'), STRUCT(test_name, severidade, status, failures), NULL)
                  IGNORE NULLS LIMIT 50) AS reprovacoes
      FROM `${var.project_id}.ops.dq_results`
      GROUP BY run_id, fault_injection
    SQL
  }
  depends_on = [google_bigquery_table.dq_results]
}
