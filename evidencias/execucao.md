# Evidências de execução

Coletado em 2026-11-02 23:10 UTC por `python -m alfab evidencias` no projeto `midyear-cursor-510311-v9`.

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
| silver.alunos | TABLE | 3867999 | 812.77 | 2026-11-02 23:01:49.184000+00:00 |
| silver.dicionario | TABLE | 27 | 0.0 | 2026-11-02 23:01:22.625000+00:00 |
| silver.diretorio_municipio | TABLE | 5571 | 0.42 | 2026-11-02 23:01:22.733000+00:00 |
| silver.eventos | TABLE | 1125 | 0.18 | 2026-10-01 19:40:21.368000+00:00 |
| silver.indicador_municipio | TABLE | 23995 | 4.79 | 2026-11-02 23:01:44.328000+00:00 |
| silver.indicador_uf | TABLE | 145 | 0.03 | 2026-11-02 23:01:43.672000+00:00 |
| silver.join_thresholds | TABLE | 8 | 0.0 | 2026-11-02 23:01:22.814000+00:00 |
| silver.meta_linha_base | TABLE | 10788 | 1.73 | 2026-11-02 23:01:46.230000+00:00 |
| silver.meta_trajetoria | TABLE | 75254 | 10.18 | 2026-11-02 23:01:48.644000+00:00 |
| silver.rede_map | TABLE | 14 | 0.0 | 2026-11-02 23:01:37.691000+00:00 |
| silver.rede_recortes | TABLE | 9 | 0.0 | 2026-11-02 23:01:28.424000+00:00 |
| silver.rede_sinonimos | TABLE | 8 | 0.0 | 2026-11-02 23:01:26.261000+00:00 |
| silver.uf_ibge | TABLE | 27 | 0.0 | 2026-11-02 23:01:26.056000+00:00 |
| gold.agg_microdado_recorte | TABLE | 33417 | 5.14 | 2026-11-02 23:07:55.654000+00:00 |
| gold.cenario_universalizacao | TABLE | 12728 | 2.05 | 2026-11-02 23:07:59.451000+00:00 |
| gold.evolucao_temporal | TABLE | 24171 | 4.43 | 2026-11-02 23:08:02.678000+00:00 |
| gold.fct_alfabetizacao_brasil | TABLE | 8 | 0.0 | 2026-11-02 23:08:04.558000+00:00 |
| gold.fct_alfabetizacao_municipio | TABLE | 23995 | 5.22 | 2026-11-02 23:08:06.337000+00:00 |
| gold.fct_alfabetizacao_uf | TABLE | 145 | 0.03 | 2026-11-02 23:08:08.376000+00:00 |
| gold.meta_vs_resultado | TABLE | 37755 | 5.19 | 2026-11-02 23:08:10.649000+00:00 |
| gold.ml_features_municipio | TABLE | 23995 | 4.05 | 2026-11-02 23:08:14.137000+00:00 |
| gold.ml_features_municipio_fase3_20261102 | SNAPSHOT | 23995 | 4.05 | 2026-11-02 23:09:25.446000+00:00 |
| gold.resultado_oficial | TABLE | 24171 | 2.72 | 2026-11-02 23:08:16.682000+00:00 |
| gold.validacao_cruzada_microdado | TABLE | 24143 | 3.25 | 2026-11-02 23:08:19.456000+00:00 |
| gold.vw_eventos_tempo_real | VIEW | 0 | 0.0 | 2026-11-02 23:08:20.914000+00:00 |
| gold.vw_indicador_consolidado | VIEW | 0 | 0.0 | 2026-11-02 23:08:19.897000+00:00 |
| ops.dq_results | TABLE | 809 | 0.2 | 2026-11-02 23:05:25.010000+00:00 |
| ops.join_match_rate | TABLE | 64 | 0.01 | 2026-11-02 23:02:06.667000+00:00 |
| ops.pipeline_runs | TABLE | 87 | 0.03 | 2026-10-30 23:52:02.860000+00:00 |
| ops.source_watermarks | TABLE | 9 | 0.0 | 2026-10-30 23:52:01.672000+00:00 |
| ops.stream_watermark | TABLE | 3 | 0.0 | 2026-10-01 20:41:29.973000+00:00 |
| ops.vw_custo_por_execucao | VIEW | 0 | 0.0 | 2026-10-01 12:41:51.022000+00:00 |
| ops.vw_latencia_streaming | VIEW | 0 | 0.0 | 2026-10-01 12:41:53.621000+00:00 |
| ops.vw_resumo_qualidade | VIEW | 0 | 0.0 | 2026-10-01 12:41:53.009000+00:00 |
| ops.vw_saude_pipeline | VIEW | 0 | 0.0 | 2026-10-01 12:41:52.216000+00:00 |

## Snapshots da Bronze (histórico preservado)

| entity | run_id | source_last_modified | exported_rows | bronze_uri |
|---|---|---|---|---|
| diretorio_municipio | 20261030T224956Z-6c238b | 2026-10-18 03:45:15.474000+00:00 | 5571 | gs://midyear-cursor-510311-v9-alfab-lake/bronze/diretorio_municipio/ingestion_date=2026-10-30/run_id=20261030T224956Z-6c238b/part-*.parquet |
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
| 20261102T230925Z-77d8ea | batch | export.ml_fase3 | SUCCEEDED | 7.5 |  |  | 10485760 |  |
| 20261102T225805Z-230ae9 | batch | publish.gold | SUCCEEDED | 27.5 |  | 204528 |  |  |
| 20261102T225805Z-230ae9 | batch | dbt.gold | SUCCEEDED | 52.9 |  |  |  |  |
| 20261102T225805Z-230ae9 | batch | dbt.silver | SUCCEEDED | 62.9 |  |  |  |  |
| 20261102T225805Z-230ae9 | batch | bronze.diretorio_municipio | SUCCEEDED | 0.2 | 5571 | 0 |  |  |
| 20261102T225805Z-230ae9 | batch | bronze.dicionario | SUCCEEDED | 0.2 | 27 | 0 |  |  |
| 20261102T225805Z-230ae9 | batch | bronze.meta_alfabetizacao_municipio | SUCCEEDED | 0.2 | 10704 | 0 |  |  |
| 20261102T225805Z-230ae9 | batch | bronze.meta_alfabetizacao_uf | SUCCEEDED | 0.2 | 81 | 0 |  |  |
| 20261102T225805Z-230ae9 | batch | bronze.meta_alfabetizacao_brasil | SUCCEEDED | 0.2 | 3 | 0 |  |  |
| 20261102T225805Z-230ae9 | batch | bronze.uf | SUCCEEDED | 0.2 | 145 | 0 |  |  |
| 20261102T225805Z-230ae9 | batch | bronze.municipio | SUCCEEDED | 0.2 | 23995 | 0 |  |  |
| 20261102T225805Z-230ae9 | batch | bronze.alunos | SUCCEEDED | 0.2 | 3867999 | 0 |  |  |
| 20261030T224956Z-6c238b | batch | publish.gold | SUCCEEDED | 22.9 |  | 204528 |  |  |
| 20261030T224956Z-6c238b | batch | dbt.gold | SUCCEEDED | 42.4 |  |  |  |  |
| 20261030T224956Z-6c238b | batch | dbt.silver | SUCCEEDED | 60.5 |  |  |  |  |
| 20261030T224956Z-6c238b | batch | bronze.diretorio_municipio | SUCCEEDED | 2.7 | 5571 | 5571 | 10485760 |  |
| 20261030T224956Z-6c238b | batch | bronze.dicionario | SUCCEEDED | 0.2 | 27 | 0 |  |  |
| 20261030T224956Z-6c238b | batch | bronze.meta_alfabetizacao_municipio | SUCCEEDED | 0.1 | 10704 | 0 |  |  |
| 20261030T224956Z-6c238b | batch | bronze.meta_alfabetizacao_uf | SUCCEEDED | 0.2 | 81 | 0 |  |  |
| 20261030T224956Z-6c238b | batch | bronze.meta_alfabetizacao_brasil | SUCCEEDED | 0.1 | 3 | 0 |  |  |
| 20261030T224956Z-6c238b | batch | bronze.uf | SUCCEEDED | 0.2 | 145 | 0 |  |  |
| 20261030T224956Z-6c238b | batch | bronze.municipio | SUCCEEDED | 0.2 | 23995 | 0 |  |  |
| 20261030T224956Z-6c238b | batch | bronze.alunos | SUCCEEDED | 0.2 | 3867999 | 0 |  |  |

## Qualidade por execução (inclui reprovações)

| run_id | fault_injection | executado_em | aprovados | bloqueantes_reprovados | informativos_alertados | erros |
|---|---|---|---|---|---|---|
| 20261102T225805Z-230ae9 | none | 2026-11-02 23:02:09.503009+00:00 | 93 | 0 | 4 | 0 |
| 20261030T224956Z-6c238b | none | 2026-10-30 22:53:38.116702+00:00 | 92 | 0 | 4 | 0 |
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
| indicador_municipio__meta_municipio | informativa | 10680 | 10464 | 0.9798 | 0.9 | False |
| indicador_municipio__meta_municipio | bloqueante | 10680 | 10464 | 0.9798 | 0.5 | False |
| indicador_uf__meta_uf | bloqueante | 73 | 72 | 0.9863 | 0.95 | False |
| indicador_uf__uf | bloqueante | 145 | 145 | 1.0 | 1.0 | False |
| meta_municipio__diretorio | bloqueante | 10704 | 10704 | 1.0 | 0.99 | False |

## Latência do streaming (últimas janelas)

_(sem linhas)_
