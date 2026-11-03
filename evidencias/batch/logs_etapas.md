# Logs das etapas batch (Cloud Logging)

Exportado em 2026-11-03 00:50 UTC por `python scripts/coletar_logs_gcp.py`, a partir da API `logging.googleapis.com`, filtro `jsonPayload.event="step_finished"`. Período: desde 2026-11-02T00:00:00Z. Horários em UTC.

| horário do log | job | run_id | etapa | status | duração (s) | linhas saída | erro |
|---|---|---|---|---|---|---|---|
| 2026-11-02 22:59:29 | alfab-ingest-bronze | `20261102T225805Z-230ae9` | bronze.alunos | **SUCCEEDED** | 0.223 |  |  |
| 2026-11-02 22:59:30 | alfab-ingest-bronze | `20261102T225805Z-230ae9` | bronze.municipio | **SUCCEEDED** | 0.176 |  |  |
| 2026-11-02 22:59:30 | alfab-ingest-bronze | `20261102T225805Z-230ae9` | bronze.uf | **SUCCEEDED** | 0.239 |  |  |
| 2026-11-02 22:59:31 | alfab-ingest-bronze | `20261102T225805Z-230ae9` | bronze.meta_alfabetizacao_brasil | **SUCCEEDED** | 0.194 |  |  |
| 2026-11-02 22:59:31 | alfab-ingest-bronze | `20261102T225805Z-230ae9` | bronze.meta_alfabetizacao_uf | **SUCCEEDED** | 0.189 |  |  |
| 2026-11-02 22:59:31 | alfab-ingest-bronze | `20261102T225805Z-230ae9` | bronze.meta_alfabetizacao_municipio | **SUCCEEDED** | 0.167 |  |  |
| 2026-11-02 22:59:31 | alfab-ingest-bronze | `20261102T225805Z-230ae9` | bronze.dicionario | **SUCCEEDED** | 0.229 |  |  |
| 2026-11-02 22:59:32 | alfab-ingest-bronze | `20261102T225805Z-230ae9` | bronze.diretorio_municipio | **SUCCEEDED** | 0.203 |  |  |
| 2026-11-02 23:02:11 | alfab-dbt-silver | `20261102T225805Z-230ae9` | dbt.silver | **SUCCEEDED** | 62.93 |  |  |
| 2026-11-02 23:05:25 | alfab-dbt-gold | `20261102T225805Z-230ae9` | dbt.gold | **SUCCEEDED** | 52.877 |  |  |
| 2026-11-02 23:08:21 | alfab-publish-gold | `20261102T225805Z-230ae9` | publish.gold | **SUCCEEDED** | 27.471 | 204528 |  |
| 2026-11-02 23:37:52 | alfab-ingest-bronze | `20261102T233638Z-1e9916` | bronze.alunos | **SUCCEEDED** | 0.19 |  |  |
| 2026-11-02 23:37:53 | alfab-ingest-bronze | `20261102T233638Z-1e9916` | bronze.municipio | **SUCCEEDED** | 0.246 |  |  |
| 2026-11-02 23:37:53 | alfab-ingest-bronze | `20261102T233638Z-1e9916` | bronze.uf | **SUCCEEDED** | 0.141 |  |  |
| 2026-11-02 23:37:53 | alfab-ingest-bronze | `20261102T233638Z-1e9916` | bronze.meta_alfabetizacao_brasil | **SUCCEEDED** | 0.173 |  |  |
| 2026-11-02 23:37:54 | alfab-ingest-bronze | `20261102T233638Z-1e9916` | bronze.meta_alfabetizacao_uf | **SUCCEEDED** | 0.2 |  |  |
| 2026-11-02 23:37:54 | alfab-ingest-bronze | `20261102T233638Z-1e9916` | bronze.meta_alfabetizacao_municipio | **SUCCEEDED** | 0.276 |  |  |
| 2026-11-02 23:37:54 | alfab-ingest-bronze | `20261102T233638Z-1e9916` | bronze.dicionario | **SUCCEEDED** | 0.205 |  |  |
| 2026-11-02 23:37:54 | alfab-ingest-bronze | `20261102T233638Z-1e9916` | bronze.diretorio_municipio | **SUCCEEDED** | 0.233 |  |  |
| 2026-11-02 23:40:15 | alfab-dbt-silver | `20261102T233638Z-1e9916` | dbt.silver | **FAILED** | 44.875 |  | QualityGateFailed: 1 regra(s) bloqueante(s) reprovada(s) em silver: ['assert_avaliados_completos'] |
| 2026-11-02 23:42:53 | alfab-ingest-bronze | `20261102T234111Z-6ef6e8` | bronze.alunos | **SUCCEEDED** | 0.181 |  |  |
| 2026-11-02 23:42:54 | alfab-ingest-bronze | `20261102T234111Z-6ef6e8` | bronze.municipio | **SUCCEEDED** | 0.196 |  |  |
| 2026-11-02 23:42:54 | alfab-ingest-bronze | `20261102T234111Z-6ef6e8` | bronze.uf | **SUCCEEDED** | 0.193 |  |  |
| 2026-11-02 23:42:54 | alfab-ingest-bronze | `20261102T234111Z-6ef6e8` | bronze.meta_alfabetizacao_brasil | **SUCCEEDED** | 0.183 |  |  |
| 2026-11-02 23:42:55 | alfab-ingest-bronze | `20261102T234111Z-6ef6e8` | bronze.meta_alfabetizacao_uf | **SUCCEEDED** | 0.191 |  |  |
| 2026-11-02 23:42:55 | alfab-ingest-bronze | `20261102T234111Z-6ef6e8` | bronze.meta_alfabetizacao_municipio | **SUCCEEDED** | 0.208 |  |  |
| 2026-11-02 23:42:55 | alfab-ingest-bronze | `20261102T234111Z-6ef6e8` | bronze.dicionario | **SUCCEEDED** | 0.194 |  |  |
| 2026-11-02 23:42:55 | alfab-ingest-bronze | `20261102T234111Z-6ef6e8` | bronze.diretorio_municipio | **SUCCEEDED** | 0.149 |  |  |
| 2026-11-02 23:45:29 | alfab-dbt-silver | `20261102T234111Z-6ef6e8` | dbt.silver | **SUCCEEDED** | 57.395 |  |  |
| 2026-11-02 23:48:33 | alfab-dbt-gold | `20261102T234111Z-6ef6e8` | dbt.gold | **SUCCEEDED** | 39.815 |  |  |
| 2026-11-02 23:49:57 | alfab-publish-gold | `20261102T234111Z-6ef6e8` | publish.gold | **SUCCEEDED** | 24.977 | 204528 |  |
| 2026-11-03 00:26:11 | alfab-ingest-bronze | `20261103T002534Z-7e1e21` | bronze.alunos | **SUCCEEDED** | 0.199 |  |  |
| 2026-11-03 00:26:12 | alfab-ingest-bronze | `20261103T002534Z-7e1e21` | bronze.municipio | **SUCCEEDED** | 0.173 |  |  |
| 2026-11-03 00:26:12 | alfab-ingest-bronze | `20261103T002534Z-7e1e21` | bronze.uf | **SUCCEEDED** | 0.181 |  |  |
| 2026-11-03 00:26:12 | alfab-ingest-bronze | `20261103T002534Z-7e1e21` | bronze.meta_alfabetizacao_brasil | **SUCCEEDED** | 0.213 |  |  |
| 2026-11-03 00:26:12 | alfab-ingest-bronze | `20261103T002534Z-7e1e21` | bronze.meta_alfabetizacao_uf | **SUCCEEDED** | 0.196 |  |  |
| 2026-11-03 00:26:13 | alfab-ingest-bronze | `20261103T002534Z-7e1e21` | bronze.meta_alfabetizacao_municipio | **SUCCEEDED** | 0.218 |  |  |
| 2026-11-03 00:26:13 | alfab-ingest-bronze | `20261103T002534Z-7e1e21` | bronze.dicionario | **SUCCEEDED** | 0.192 |  |  |
| 2026-11-03 00:26:13 | alfab-ingest-bronze | `20261103T002534Z-7e1e21` | bronze.diretorio_municipio | **SUCCEEDED** | 0.196 |  |  |
| 2026-11-03 00:28:40 | alfab-dbt-silver | `20261103T002534Z-7e1e21` | dbt.silver | **SUCCEEDED** | 51.568 |  |  |
| 2026-11-03 00:30:06 | alfab-dbt-gold | `20261103T002534Z-7e1e21` | dbt.gold | **SUCCEEDED** | 37.93 |  |  |
| 2026-11-03 00:31:36 | alfab-publish-gold | `20261103T002534Z-7e1e21` | publish.gold | **SUCCEEDED** | 24.916 | 204528 |  |
