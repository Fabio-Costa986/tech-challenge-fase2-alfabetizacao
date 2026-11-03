# Logs do streaming (Cloud Logging)

Exportado em 2026-11-03 00:50 UTC por `python scripts/coletar_logs_gcp.py`, a partir da API `logging.googleapis.com`. Período: desde 2026-11-02T00:00:00Z. Horários em UTC.

## Simulador e micro-lote (`step_finished`)

| horário do log | job | run_id | status | duração (s) | detalhes |
|---|---|---|---|---|---|
| 2026-11-02 23:53:54 | alfab-simulator | `20261102T235246Z-38db44` | **SUCCEEDED** | 62.541 | {"valido": 548, "invalido": 22, "invalido:campo_faltando": 6, "duplicata": 30, "invalido:municipio_inexistente": 5, "invalido:json_quebrado": 8, "invalido:taxa_fora_faixa": 1, "invalido:id_malformado": 2} |
| 2026-11-02 23:56:21 | alfab-microbatch | `20261102T235607Z-8ad281` | **SUCCEEDED** | 13.847 | lidas=622 únicas=589 inseridas=548 duplicatas=33 quarentena=5 p50=0.057s p95=18.339s |
| 2026-11-03 00:01:14 | alfab-simulator | `20261102T235748Z-2875bb` | **SUCCEEDED** | 201.598 | {"valido": 36, "invalido": 3, "invalido:json_quebrado": 1, "invalido:campo_faltando": 1, "invalido:id_malformado": 1, "duplicata": 1} |
| 2026-11-03 00:03:16 | alfab-microbatch | `20261103T000245Z-0af026` | **SUCCEEDED** | 31.715 | lidas=620 únicas=589 inseridas=36 duplicatas=31 quarentena=5 p50=5.072s p95=5.733s |

## Ingestor `alfab-event-ingestor`: eventos recebidos do Pub/Sub

Cada evento entregue pelo push do Pub/Sub gera um log: `event_ingested` (gravado em `bronze.eventos_raw`) ou `event_quarantined` (gravado em `bronze.eventos_quarentena`).

| dia | eventos ingeridos | eventos em quarentena |
|---|---|---|
| 2026-11-02 | 605 | 20 |
| 2026-11-03 | 15 | 0 |

Amostra de entradas (primeiras do período):

| horário do log | evento | event_id / message_id | latência de ingestão (s) |
|---|---|---|---|
| 2026-11-02 23:53:10 | event_ingested | `4548f21b-af03-4c05-8555-383dae10fc88` | 15.298 |
| 2026-11-02 23:53:10 | event_ingested | `2b961fde-dedf-4ba2-9edf-f339692fff62` | 8.761 |
| 2026-11-02 23:53:10 | event_ingested | `65aceb2e-387f-4418-92bb-7a2dc7142f9f` | 16.714 |
| 2026-11-02 23:53:10 | event_ingested | `7c718253-6983-4bf2-af3e-da8ed7d49e84` | 12.743 |
| 2026-11-02 23:53:10 | event_ingested | `6393b37c-f00c-4e4c-811f-943e06fcfe4d` | 16.24 |
| 2026-11-02 23:53:14 | event_quarantined | `22198064744399927` | — |
| 2026-11-02 23:53:14 | event_quarantined | `23059599638126748` | — |
| 2026-11-02 23:53:14 | event_quarantined | `23066133858057964` | — |

## Requisições HTTP de push recebidas pelo ingestor

| status HTTP | requisições |
|---|---|
| 204 | 640 |

204 = evento aceito (ingerido ou em quarentena, ambos com ACK). 403 = chamada sem a identidade OIDC do push, bloqueada. 5xx levaria o Pub/Sub a tentar de novo e, após 5 falhas, à fila de descarte.
