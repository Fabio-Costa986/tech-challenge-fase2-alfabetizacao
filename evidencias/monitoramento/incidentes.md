# Alertas disparados (Cloud Monitoring)

Fonte: API `monitoring.googleapis.com/v3/projects/<projeto>/alerts`, consultada em 2026-10-01. Canal: e-mail do grupo.

## Tempo entre a falha e a abertura do incidente

Política `alfab: etapa do pipeline FALHOU` (log-based metric `alfab/step_failed`). Horários em UTC.

| run_id | etapa | falha registrada (ops.pipeline_runs) | incidente aberto | tempo até o alerta |
|---|---|---|---|---|
| `20261001T131455Z-325f14` | dbt.silver | 13:26:15 | 13:30:47 | **4 min 31 s** |
| `20261001T133227Z-c655ab` | dbt.gold | 13:47:31 | 13:51:10 | **3 min 38 s** |
| `20261001T140713Z-bb3655` | dbt.gold | 14:24:10 | 14:28:25 | **4 min 14 s** |
| `20261001T172800Z-b20784` | dbt.silver | 17:37:12 | 17:41:32 | **4 min 19 s** |

## Todos os incidentes

| estado | aberto | fechado | política | job |
|---|---|---|---|---|
| CLOSED | 2026-10-01T13:30:47Z | 2026-10-01T13:31:36Z | alfab: execuÃ§Ã£o de Cloud Run Job falhou | alfab-dbt-silver |
| CLOSED | 2026-10-01T13:30:47Z | 2026-10-01T13:31:15Z | alfab: etapa do pipeline FALHOU | alfab-dbt-silver |
| CLOSED | 2026-10-01T13:51:10Z | 2026-10-01T13:52:26Z | alfab: etapa do pipeline FALHOU | alfab-dbt-gold |
| CLOSED | 2026-10-01T13:51:59Z | 2026-10-01T13:52:48Z | alfab: execuÃ§Ã£o de Cloud Run Job falhou | alfab-dbt-gold |
| CLOSED | 2026-10-01T14:28:25Z | 2026-10-01T14:29:17Z | alfab: etapa do pipeline FALHOU | alfab-dbt-gold |
| CLOSED | 2026-10-01T14:28:54Z | 2026-10-01T14:30:14Z | alfab: execuÃ§Ã£o de Cloud Run Job falhou | alfab-dbt-gold |
| CLOSED | 2026-10-01T17:41:32Z | 2026-10-01T17:42:29Z | alfab: etapa do pipeline FALHOU | alfab-dbt-silver |
| CLOSED | 2026-10-01T17:42:03Z | 2026-10-01T17:43:26Z | alfab: execuÃ§Ã£o de Cloud Run Job falhou | alfab-dbt-silver |
