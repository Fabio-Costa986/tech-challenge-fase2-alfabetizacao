# Evidências de execução

Coletado em 2026-10-01 20:47 UTC por `python -m alfab evidencias` no projeto `midyear-cursor-510311-v9`.

## Contagem de linhas por tabela

External tables da Bronze mostram linhas vazias: os dados estão no GCS (ver ops.source_watermarks.exported_rows).

| tabela | tipo | linhas | MiB | modificada |
|---|---|---|---|---|
| bronze.alunos | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:30.742000+00:00 |
| bronze.dicionario | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:50.065000+00:00 |
| bronze.diretorio_municipio | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:53.581000+00:00 |
| bronze.eventos_quarentena | TABLE | 50 | 0.02 | 2026-10-01 19:40:16.677000+00:00 |
| bronze.eventos_raw | TABLE | 1206 | 0.26 | 2026-10-01 18:54:54.946000+00:00 |
| bronze.meta_alfabetizacao_brasil | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:41.005000+00:00 |
| bronze.meta_alfabetizacao_municipio | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:47.141000+00:00 |
| bronze.meta_alfabetizacao_uf | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:44.154000+00:00 |
| bronze.municipio | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:35.087000+00:00 |
| bronze.uf | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:37.872000+00:00 |
| silver.alunos | TABLE | 3867999 | 812.77 | 2026-10-01 19:43:19.088000+00:00 |
| silver.dicionario | TABLE | 27 | 0.0 | 2026-10-01 19:42:55.654000+00:00 |
| silver.diretorio_municipio | TABLE | 5571 | 0.42 | 2026-10-01 19:42:55.591000+00:00 |
| silver.eventos | TABLE | 1125 | 0.18 | 2026-10-01 19:40:21.368000+00:00 |
| silver.indicador_municipio | TABLE | 23995 | 4.79 | 2026-10-01 19:43:16.196000+00:00 |
| silver.indicador_uf | TABLE | 145 | 0.03 | 2026-10-01 19:43:15.229000+00:00 |
| silver.join_thresholds | TABLE | 8 | 0.0 | 2026-10-01 19:42:56.391000+00:00 |
| silver.meta_linha_base | TABLE | 10788 | 1.73 | 2026-10-01 19:43:16.374000+00:00 |
| silver.meta_trajetoria | TABLE | 75254 | 10.18 | 2026-10-01 19:43:21.032000+00:00 |
| silver.rede_map | TABLE | 14 | 0.0 | 2026-10-01 19:43:09.527000+00:00 |
| silver.rede_recortes | TABLE | 9 | 0.0 | 2026-10-01 19:42:57.166000+00:00 |
| silver.rede_sinonimos | TABLE | 8 | 0.0 | 2026-10-01 19:43:00.036000+00:00 |
| silver.uf_ibge | TABLE | 27 | 0.0 | 2026-10-01 19:42:59.980000+00:00 |
| gold.agg_microdado_recorte | TABLE | 33417 | 5.14 | 2026-10-01 19:54:00.328000+00:00 |
| gold.cenario_universalizacao | TABLE | 12728 | 2.05 | 2026-10-01 19:54:02.235000+00:00 |
| gold.evolucao_temporal | TABLE | 24171 | 4.43 | 2026-10-01 19:54:05.449000+00:00 |
| gold.fct_alfabetizacao_brasil | TABLE | 8 | 0.0 | 2026-10-01 19:54:07.892000+00:00 |
| gold.fct_alfabetizacao_municipio | TABLE | 23995 | 5.22 | 2026-10-01 19:54:11.582000+00:00 |
| gold.fct_alfabetizacao_uf | TABLE | 145 | 0.03 | 2026-10-01 19:54:13.444000+00:00 |
| gold.meta_vs_resultado | TABLE | 37755 | 5.19 | 2026-10-01 19:54:15.475000+00:00 |
| gold.ml_features_municipio | TABLE | 23995 | 4.13 | 2026-10-01 19:54:17.778000+00:00 |
| gold.resultado_oficial | TABLE | 24171 | 2.72 | 2026-10-01 19:54:19.393000+00:00 |
| gold.validacao_cruzada_microdado | TABLE | 24143 | 3.25 | 2026-10-01 19:54:22.051000+00:00 |
| gold.vw_eventos_tempo_real | VIEW | 0 | 0.0 | 2026-10-01 19:54:23.348000+00:00 |
| gold.vw_indicador_consolidado | VIEW | 0 | 0.0 | 2026-10-01 19:54:22.495000+00:00 |
| ops.dq_results | TABLE | 616 | 0.15 | 2026-10-01 19:49:34.471000+00:00 |
| ops.join_match_rate | TABLE | 48 | 0.01 | 2026-10-01 19:43:34.156000+00:00 |
| ops.pipeline_runs | TABLE | 75 | 0.02 | 2026-10-01 20:41:10.616000+00:00 |
| ops.source_watermarks | TABLE | 8 | 0.0 | 2026-10-01 14:20:36.768000+00:00 |
| ops.stream_watermark | TABLE | 3 | 0.0 | 2026-10-01 20:41:29.973000+00:00 |
| ops.vw_custo_por_execucao | VIEW | 0 | 0.0 | 2026-10-01 12:41:51.022000+00:00 |
| ops.vw_latencia_streaming | VIEW | 0 | 0.0 | 2026-10-01 12:41:53.621000+00:00 |
| ops.vw_resumo_qualidade | VIEW | 0 | 0.0 | 2026-10-01 12:41:53.009000+00:00 |
| ops.vw_saude_pipeline | VIEW | 0 | 0.0 | 2026-10-01 12:41:52.216000+00:00 |

## Snapshots da Bronze (histórico preservado)

| entity | run_id | source_last_modified | exported_rows | bronze_uri |
|---|---|---|---|---|
| diretorio_municipio | 20261001T131455Z-325f14 | 2026-06-22 13:22:40.251000+00:00 | 5571 | gs://midyear-cursor-510311-v9-alfab-lake/bronze/diretorio_municipio/ingestion_date=2026-10-01/run_id=20261001T131455Z-325f14/part-*.parquet |
| dicionario | 20261001T131455Z-325f14 | 2026-01-14 14:25:34.055000+00:00 | 27 | gs://midyear-cursor-510311-v9-alfab-lake/bronze/dicionario/ingestion_date=2026-10-01/run_id=20261001T131455Z-325f14/part-*.parquet |
| meta_alfabetizacao_municipio | 20261001T131455Z-325f14 | 2026-01-14 14:24:49.565000+00:00 | 10704 | gs://midyear-cursor-510311-v9-alfab-lake/bronze/meta_alfabetizacao_municipio/ingestion_date=2026-10-01/run_id=20261001T131455Z-325f14/part-*.parquet |
| meta_alfabetizacao_uf | 20261001T131455Z-325f14 | 2026-03-24 14:32:05.261000+00:00 | 81 | gs://midyear-cursor-510311-v9-alfab-lake/bronze/meta_alfabetizacao_uf/ingestion_date=2026-10-01/run_id=20261001T131455Z-325f14/part-*.parquet |
| meta_alfabetizacao_brasil | 20261001T131455Z-325f14 | 2026-03-24 14:32:06.062000+00:00 | 3 | gs://midyear-cursor-510311-v9-alfab-lake/bronze/meta_alfabetizacao_brasil/ingestion_date=2026-10-01/run_id=20261001T131455Z-325f14/part-*.parquet |
| uf | 20261001T131455Z-325f14 | 2026-01-14 14:25:37.597000+00:00 | 145 | gs://midyear-cursor-510311-v9-alfab-lake/bronze/uf/ingestion_date=2026-10-01/run_id=20261001T131455Z-325f14/part-*.parquet |
| municipio | 20261001T131455Z-325f14 | 2026-01-14 14:24:49.600000+00:00 | 23995 | gs://midyear-cursor-510311-v9-alfab-lake/bronze/municipio/ingestion_date=2026-10-01/run_id=20261001T131455Z-325f14/part-*.parquet |
| alunos | 20261001T131455Z-325f14 | 2026-01-14 14:25:50.902000+00:00 | 3867999 | gs://midyear-cursor-510311-v9-alfab-lake/bronze/alunos/ingestion_date=2026-10-01/run_id=20261001T131455Z-325f14/part-*.parquet |

## Últimas execuções (ops.pipeline_runs)

| run_id | pipeline | step | status | duration_s | rows_in | rows_out | bytes_billed | error |
|---|---|---|---|---|---|---|---|---|
| 20261001T193739Z-f0dbac | batch | publish.gold | SUCCEEDED | 26.5 |  | 204528 |  |  |
| 20261001T193739Z-f0dbac | batch | dbt.gold | SUCCEEDED | 48.7 |  |  |  |  |
| 20261001T193739Z-f0dbac | batch | dbt.silver | SUCCEEDED | 63.1 |  |  |  |  |
| 20261001T193739Z-f0dbac | batch | bronze.diretorio_municipio | SUCCEEDED | 0.2 | 5571 | 0 |  |  |
| 20261001T193739Z-f0dbac | batch | bronze.dicionario | SUCCEEDED | 0.2 | 27 | 0 |  |  |
| 20261001T193739Z-f0dbac | batch | bronze.meta_alfabetizacao_municipio | SUCCEEDED | 0.2 | 10704 | 0 |  |  |
| 20261001T193739Z-f0dbac | batch | bronze.meta_alfabetizacao_uf | SUCCEEDED | 0.2 | 81 | 0 |  |  |
| 20261001T193739Z-f0dbac | batch | bronze.meta_alfabetizacao_brasil | SUCCEEDED | 0.2 | 3 | 0 |  |  |
| 20261001T193739Z-f0dbac | batch | bronze.uf | SUCCEEDED | 0.2 | 145 | 0 |  |  |
| 20261001T193739Z-f0dbac | batch | bronze.municipio | SUCCEEDED | 0.2 | 23995 | 0 |  |  |
| 20261001T194006Z-9f48ed | stream | microbatch.silver.eventos | SUCCEEDED | 18.1 | 656 | 36 | 157286400 |  |
| 20261001T193739Z-f0dbac | batch | bronze.alunos | SUCCEEDED | 0.2 | 3867999 | 0 |  |  |
| 20261001T181116Z-7a2b68 | stream | simulator | SUCCEEDED | 202.1 |  | 40 |  |  |
| 20261001T172800Z-b20784 | batch | dbt.silver | FAILED | 57.8 |  |  |  | QualityGateFailed: 1 regra(s) bloqueante(s) reprovada(s) em silver: ['unique_combination_indicador_municipio_ano__id_mun |
| 20261001T173612Z-046868 | stream | microbatch.silver.eventos | SUCCEEDED | 15.4 | 1167 | 542 | 115343360 |  |
| 20261001T172800Z-b20784 | batch | bronze.diretorio_municipio | SUCCEEDED | 0.2 | 5571 | 0 |  |  |
| 20261001T172800Z-b20784 | batch | bronze.dicionario | SUCCEEDED | 0.3 | 27 | 0 |  |  |
| 20261001T172800Z-b20784 | batch | bronze.meta_alfabetizacao_municipio | SUCCEEDED | 0.2 | 10704 | 0 |  |  |
| 20261001T172800Z-b20784 | batch | bronze.meta_alfabetizacao_uf | SUCCEEDED | 0.2 | 81 | 0 |  |  |
| 20261001T172800Z-b20784 | batch | bronze.meta_alfabetizacao_brasil | SUCCEEDED | 0.1 | 3 | 0 |  |  |
| 20261001T172800Z-b20784 | batch | bronze.uf | SUCCEEDED | 0.2 | 145 | 0 |  |  |
| 20261001T172800Z-b20784 | batch | bronze.municipio | SUCCEEDED | 0.3 | 23995 | 0 |  |  |
| 20261001T172800Z-b20784 | batch | bronze.alunos | SUCCEEDED | 0.2 | 3867999 | 0 |  |  |
| 20261001T172948Z-a82cf3 | stream | simulator | SUCCEEDED | 65.6 |  | 600 |  |  |
| 20261001T171320Z-a32410 | stream | microbatch.silver.eventos | SUCCEEDED | 14.7 | 550 | 547 | 115343360 |  |
| 20261001T165323Z-bec55e | stream | simulator | SUCCEEDED | 63.1 |  | 600 |  |  |
| 20261001T162153Z-ca83f9 | batch | publish.gold | SUCCEEDED | 24.9 |  | 204528 |  |  |
| 20261001T162153Z-ca83f9 | batch | dbt.gold | SUCCEEDED | 53.7 |  |  |  |  |
| 20261001T162153Z-ca83f9 | batch | dbt.silver | SUCCEEDED | 75.9 |  |  |  |  |
| 20261001T162153Z-ca83f9 | batch | bronze.diretorio_municipio | SUCCEEDED | 0.3 | 5571 | 0 |  |  |
| 20261001T162153Z-ca83f9 | batch | bronze.dicionario | SUCCEEDED | 0.2 | 27 | 0 |  |  |
| 20261001T162153Z-ca83f9 | batch | bronze.meta_alfabetizacao_municipio | SUCCEEDED | 0.2 | 10704 | 0 |  |  |
| 20261001T162153Z-ca83f9 | batch | bronze.meta_alfabetizacao_uf | SUCCEEDED | 0.2 | 81 | 0 |  |  |
| 20261001T162153Z-ca83f9 | batch | bronze.meta_alfabetizacao_brasil | SUCCEEDED | 0.2 | 3 | 0 |  |  |
| 20261001T162153Z-ca83f9 | batch | bronze.uf | SUCCEEDED | 0.2 | 145 | 0 |  |  |
| 20261001T162153Z-ca83f9 | batch | bronze.municipio | SUCCEEDED | 0.2 | 23995 | 0 |  |  |
| 20261001T162153Z-ca83f9 | batch | bronze.alunos | SUCCEEDED | 0.2 | 3867999 | 0 |  |  |
| 20261001T161436Z-9e8b7f | batch | dbt.silver | SUCCEEDED | 92.6 |  |  |  |  |
| 20261001T161436Z-9e8b7f | batch | bronze.diretorio_municipio | SUCCEEDED | 0.4 | 5571 | 0 |  |  |
| 20261001T161436Z-9e8b7f | batch | bronze.dicionario | SUCCEEDED | 0.2 | 27 | 0 |  |  |
| 20261001T161436Z-9e8b7f | batch | bronze.meta_alfabetizacao_municipio | SUCCEEDED | 0.2 | 10704 | 0 |  |  |
| 20261001T161436Z-9e8b7f | batch | bronze.meta_alfabetizacao_uf | SUCCEEDED | 0.2 | 81 | 0 |  |  |
| 20261001T161436Z-9e8b7f | batch | bronze.meta_alfabetizacao_brasil | SUCCEEDED | 0.2 | 3 | 0 |  |  |
| 20261001T161436Z-9e8b7f | batch | bronze.uf | SUCCEEDED | 0.2 | 145 | 0 |  |  |
| 20261001T161436Z-9e8b7f | batch | bronze.municipio | SUCCEEDED | 0.2 | 23995 | 0 |  |  |
| 20261001T161436Z-9e8b7f | batch | bronze.alunos | SUCCEEDED | 0.2 | 3867999 | 0 |  |  |
| 20261001T140713Z-bb3655 | batch | dbt.gold | FAILED | 58.1 |  |  |  | DbtExecutionError: erros de execução: ['status_meta_distingue_sem_meta_de_nao_atingiu'] |
| 20261001T140713Z-bb3655 | batch | dbt.silver | SUCCEEDED | 71.2 |  |  |  |  |
| 20261001T140713Z-bb3655 | batch | bronze.diretorio_municipio | SUCCEEDED | 0.2 | 5571 | 0 |  |  |
| 20261001T140713Z-bb3655 | batch | bronze.dicionario | SUCCEEDED | 0.2 | 27 | 0 |  |  |
| 20261001T140713Z-bb3655 | batch | bronze.meta_alfabetizacao_municipio | SUCCEEDED | 0.2 | 10704 | 0 |  |  |
| 20261001T140713Z-bb3655 | batch | bronze.meta_alfabetizacao_uf | SUCCEEDED | 0.2 | 81 | 0 |  |  |
| 20261001T140713Z-bb3655 | batch | bronze.meta_alfabetizacao_brasil | SUCCEEDED | 0.2 | 3 | 0 |  |  |
| 20261001T140713Z-bb3655 | batch | bronze.uf | SUCCEEDED | 0.2 | 145 | 0 |  |  |
| 20261001T140713Z-bb3655 | batch | bronze.municipio | SUCCEEDED | 0.2 | 23995 | 0 |  |  |
| 20261001T140713Z-bb3655 | batch | bronze.alunos | SUCCEEDED | 0.2 | 3867999 | 0 |  |  |
| 20261001T133227Z-c655ab | batch | dbt.gold | FAILED | 51.3 |  |  |  | DbtExecutionError: erros de execução: ['resultado_oficial'] |
| 20261001T133227Z-c655ab | batch | dbt.silver | SUCCEEDED | 72.6 |  |  |  |  |
| 20261001T133227Z-c655ab | batch | bronze.diretorio_municipio | SUCCEEDED | 0.1 | 5571 | 0 |  |  |
| 20261001T133227Z-c655ab | batch | bronze.dicionario | SUCCEEDED | 0.1 | 27 | 0 |  |  |

## Qualidade por execução (inclui reprovações)

| run_id | fault_injection | executado_em | aprovados | bloqueantes_reprovados | informativos_alertados | erros |
|---|---|---|---|---|---|---|
| 20261001T193739Z-f0dbac | none | 2026-10-01 19:43:36.440512+00:00 | 92 | 0 | 4 | 0 |
| 20261001T172800Z-b20784 | duplicate_keys | 2026-10-01 17:37:10.304743+00:00 | 59 | 1 | 1 | 0 |
| 20261001T162153Z-ca83f9 | none | 2026-10-01 16:30:44.108597+00:00 | 92 | 0 | 4 | 0 |
| 20261001T161436Z-9e8b7f | none | 2026-10-01 16:23:06.877535+00:00 | 63 | 0 | 1 | 0 |
| 20261001T140713Z-bb3655 | none | 2026-10-01 14:18:02.094442+00:00 | 87 | 0 | 4 | 0 |
| debug-local | none | 2026-10-01 14:01:33.783442+00:00 | 37 | 0 | 4 | 0 |
| 20261001T133227Z-c655ab | none | 2026-10-01 13:41:33.155511+00:00 | 77 | 2 | 4 | 0 |
| 20261001T131455Z-325f14 | none | 2026-10-01 13:26:13.976120+00:00 | 62 | 1 | 1 | 0 |

## Taxa de correspondência dos joins (última medição)

| join_name | severidade | total | matched | match_rate | min_rate | reprovado |
|---|---|---|---|---|---|---|
| alunos__diretorio | bloqueante | 10392 | 10392 | 1.0 | 0.99 | False |
| alunos__indicador_uf | bloqueante | 143 | 141 | 0.986 | 0.95 | False |
| indicador_municipio__diretorio | bloqueante | 23995 | 23995 | 1.0 | 0.99 | False |
| indicador_municipio__meta_municipio | bloqueante | 10680 | 10464 | 0.9798 | 0.5 | False |
| indicador_municipio__meta_municipio | informativa | 10680 | 10464 | 0.9798 | 0.9 | False |
| indicador_uf__meta_uf | bloqueante | 73 | 72 | 0.9863 | 0.95 | False |
| indicador_uf__uf | bloqueante | 145 | 145 | 1.0 | 1.0 | False |
| meta_municipio__diretorio | bloqueante | 10704 | 10704 | 1.0 | 0.99 | False |

## Latência do streaming (últimas janelas)

| janela_5min | eventos | p50_ingestao_s | p95_ingestao_s | p99_ingestao_s | p95_ponta_a_ponta_s |
|---|---|---|---|---|---|
| 2026-10-01 18:10:00+00:00 | 36 | 5.097 | 7.651 | 12.256 | 5328.687 |
| 2026-10-01 17:30:00+00:00 | 542 | 0.058 | 25.574 | 30.731 | 385.465 |
| 2026-10-01 16:50:00+00:00 | 547 | 0.14 | 21.434 | 24.406 | 1195.107 |
