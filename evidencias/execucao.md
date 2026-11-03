# Evidências de execução

Coletado em 2026-11-03 00:51 UTC por `python -m alfab evidencias` no projeto `midyear-cursor-510311-v9`.

**Aceite ADR-008/009 verificado no GCP:** run_id `20261103T002534Z-7e1e21`; etapas de Silver, Gold e publicação concluídas, testes bloqueantes aprovados e Gold publicada sem meta futura.

## Contagem de linhas por tabela

External tables da Bronze mostram linhas vazias: os dados estão no GCS (ver ops.source_watermarks.exported_rows).

| tabela | tipo | linhas | MiB | modificada |
|---|---|---|---|---|
| bronze.alunos | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:30.742000+00:00 |
| bronze.dicionario | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:50.065000+00:00 |
| bronze.diretorio_municipio | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:53.581000+00:00 |
| bronze.eventos_quarentena | TABLE | 55 | 0.02 | 2026-11-03 00:03:09.795000+00:00 |
| bronze.eventos_raw | TABLE | 1206 | 0.26 | 2026-10-01 18:54:54.946000+00:00 |
| bronze.meta_alfabetizacao_brasil | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:41.005000+00:00 |
| bronze.meta_alfabetizacao_municipio | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:47.141000+00:00 |
| bronze.meta_alfabetizacao_uf | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:44.154000+00:00 |
| bronze.municipio | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:35.087000+00:00 |
| bronze.uf | EXTERNAL | 0 | 0.0 | 2026-10-01 13:19:37.872000+00:00 |
| silver.alunos | TABLE | 3867999 | 812.77 | 2026-11-03 00:28:23.332000+00:00 |
| silver.dicionario | TABLE | 27 | 0.0 | 2026-11-03 00:28:01.170000+00:00 |
| silver.diretorio_municipio | TABLE | 5571 | 0.42 | 2026-11-03 00:28:01.168000+00:00 |
| silver.eventos | TABLE | 1709 | 0.28 | 2026-11-03 00:03:14.454000+00:00 |
| silver.indicador_municipio | TABLE | 23995 | 4.79 | 2026-11-03 00:28:18.513000+00:00 |
| silver.indicador_uf | TABLE | 145 | 0.03 | 2026-11-03 00:28:18.229000+00:00 |
| silver.join_thresholds | TABLE | 8 | 0.0 | 2026-11-03 00:28:02.062000+00:00 |
| silver.meta_linha_base | TABLE | 10788 | 1.73 | 2026-11-03 00:28:19.212000+00:00 |
| silver.meta_trajetoria | TABLE | 75254 | 10.18 | 2026-11-03 00:28:22.718000+00:00 |
| silver.rede_map | TABLE | 14 | 0.0 | 2026-11-03 00:28:13.431000+00:00 |
| silver.rede_recortes | TABLE | 9 | 0.0 | 2026-11-03 00:28:00.759000+00:00 |
| silver.rede_sinonimos | TABLE | 8 | 0.0 | 2026-11-03 00:28:03.654000+00:00 |
| silver.uf_ibge | TABLE | 27 | 0.0 | 2026-11-03 00:28:03.798000+00:00 |
| gold.agg_microdado_recorte | TABLE | 33417 | 5.14 | 2026-11-03 00:31:14.761000+00:00 |
| gold.cenario_universalizacao | TABLE | 12728 | 2.05 | 2026-11-03 00:31:17.307000+00:00 |
| gold.evolucao_temporal | TABLE | 24171 | 4.43 | 2026-11-03 00:31:20.546000+00:00 |
| gold.fct_alfabetizacao_brasil | TABLE | 8 | 0.0 | 2026-11-03 00:31:22.488000+00:00 |
| gold.fct_alfabetizacao_municipio | TABLE | 23995 | 5.22 | 2026-11-03 00:31:24.196000+00:00 |
| gold.fct_alfabetizacao_uf | TABLE | 145 | 0.03 | 2026-11-03 00:31:25.917000+00:00 |
| gold.meta_vs_resultado | TABLE | 37755 | 5.19 | 2026-11-03 00:31:28.009000+00:00 |
| gold.ml_features_municipio | TABLE | 23995 | 4.05 | 2026-11-03 00:31:29.826000+00:00 |
| gold.ml_features_municipio_fase3_20261103_4531e38 | SNAPSHOT | 23995 | 4.05 | 2026-11-03 00:32:42.581000+00:00 |
| gold.resultado_oficial | TABLE | 24171 | 2.72 | 2026-11-03 00:31:32.001000+00:00 |
| gold.validacao_cruzada_microdado | TABLE | 24143 | 3.25 | 2026-11-03 00:31:34.728000+00:00 |
| gold.vw_eventos_tempo_real | VIEW | 0 | 0.0 | 2026-11-03 00:31:36.237000+00:00 |
| gold.vw_indicador_consolidado | VIEW | 0 | 0.0 | 2026-11-03 00:31:35.598000+00:00 |
| ops.dq_results | TABLE | 1068 | 0.26 | 2026-11-03 00:30:06.023000+00:00 |
| ops.join_match_rate | TABLE | 80 | 0.01 | 2026-11-03 00:28:36.587000+00:00 |
| ops.pipeline_runs | TABLE | 121 | 0.04 | 2026-11-03 00:00:32.116000+00:00 |
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
| 20261103T003232Z-114aed | batch | export.ml_fase3 | SUCCEEDED | 3.8 |  |  | 10485760 |  |
| 20261103T002534Z-7e1e21 | batch | publish.gold | SUCCEEDED | 24.9 |  | 204528 |  |  |
| 20261103T002534Z-7e1e21 | batch | dbt.gold | SUCCEEDED | 37.9 |  |  |  |  |
| 20261103T002534Z-7e1e21 | batch | dbt.silver | SUCCEEDED | 51.6 |  |  |  |  |
| 20261103T002534Z-7e1e21 | batch | bronze.diretorio_municipio | SUCCEEDED | 0.2 | 5571 | 0 |  |  |
| 20261103T002534Z-7e1e21 | batch | bronze.dicionario | SUCCEEDED | 0.2 | 27 | 0 |  |  |
| 20261103T002534Z-7e1e21 | batch | bronze.meta_alfabetizacao_municipio | SUCCEEDED | 0.2 | 10704 | 0 |  |  |
| 20261103T002534Z-7e1e21 | batch | bronze.meta_alfabetizacao_uf | SUCCEEDED | 0.2 | 81 | 0 |  |  |
| 20261103T002534Z-7e1e21 | batch | bronze.meta_alfabetizacao_brasil | SUCCEEDED | 0.2 | 3 | 0 |  |  |
| 20261103T002534Z-7e1e21 | batch | bronze.uf | SUCCEEDED | 0.2 | 145 | 0 |  |  |
| 20261103T002534Z-7e1e21 | batch | bronze.municipio | SUCCEEDED | 0.2 | 23995 | 0 |  |  |
| 20261103T002534Z-7e1e21 | batch | bronze.alunos | SUCCEEDED | 0.2 | 3867999 | 0 |  |  |
| 20261103T000245Z-0af026 | stream | microbatch.silver.eventos | SUCCEEDED | 31.7 | 620 | 36 | 146800640 |  |
| 20261102T235748Z-2875bb | stream | simulator | SUCCEEDED | 201.6 |  | 40 |  |  |
| 20261102T235607Z-8ad281 | stream | microbatch.silver.eventos | SUCCEEDED | 13.8 | 622 | 548 | 157286400 |  |
| 20261102T235246Z-38db44 | stream | simulator | SUCCEEDED | 62.5 |  | 600 |  |  |
| 20261102T234111Z-6ef6e8 | batch | publish.gold | SUCCEEDED | 25.0 |  | 204528 |  |  |
| 20261102T234111Z-6ef6e8 | batch | dbt.gold | SUCCEEDED | 39.8 |  |  |  |  |
| 20261102T234111Z-6ef6e8 | batch | dbt.silver | SUCCEEDED | 57.4 |  |  |  |  |
| 20261102T234111Z-6ef6e8 | batch | bronze.diretorio_municipio | SUCCEEDED | 0.1 | 5571 | 0 |  |  |
| 20261102T234111Z-6ef6e8 | batch | bronze.dicionario | SUCCEEDED | 0.2 | 27 | 0 |  |  |
| 20261102T234111Z-6ef6e8 | batch | bronze.meta_alfabetizacao_municipio | SUCCEEDED | 0.2 | 10704 | 0 |  |  |
| 20261102T234111Z-6ef6e8 | batch | bronze.meta_alfabetizacao_uf | SUCCEEDED | 0.2 | 81 | 0 |  |  |
| 20261102T234111Z-6ef6e8 | batch | bronze.meta_alfabetizacao_brasil | SUCCEEDED | 0.2 | 3 | 0 |  |  |
| 20261102T234111Z-6ef6e8 | batch | bronze.uf | SUCCEEDED | 0.2 | 145 | 0 |  |  |
| 20261102T234111Z-6ef6e8 | batch | bronze.municipio | SUCCEEDED | 0.2 | 23995 | 0 |  |  |
| 20261102T234111Z-6ef6e8 | batch | bronze.alunos | SUCCEEDED | 0.2 | 3867999 | 0 |  |  |
| 20261102T233638Z-1e9916 | batch | dbt.silver | FAILED | 44.9 |  |  |  | QualityGateFailed: 1 regra(s) bloqueante(s) reprovada(s) em silver: ['assert_avaliados_completos'] |
| 20261102T233638Z-1e9916 | batch | bronze.diretorio_municipio | SUCCEEDED | 0.2 | 5571 | 0 |  |  |
| 20261102T233638Z-1e9916 | batch | bronze.dicionario | SUCCEEDED | 0.2 | 27 | 0 |  |  |
| 20261102T233638Z-1e9916 | batch | bronze.meta_alfabetizacao_municipio | SUCCEEDED | 0.3 | 10704 | 0 |  |  |
| 20261102T233638Z-1e9916 | batch | bronze.meta_alfabetizacao_uf | SUCCEEDED | 0.2 | 81 | 0 |  |  |
| 20261102T233638Z-1e9916 | batch | bronze.meta_alfabetizacao_brasil | SUCCEEDED | 0.2 | 3 | 0 |  |  |
| 20261102T233638Z-1e9916 | batch | bronze.uf | SUCCEEDED | 0.1 | 145 | 0 |  |  |
| 20261102T233638Z-1e9916 | batch | bronze.municipio | SUCCEEDED | 0.2 | 23995 | 0 |  |  |
| 20261102T233638Z-1e9916 | batch | bronze.alunos | SUCCEEDED | 0.2 | 3867999 | 0 |  |  |
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

## Etapas efetivas do run_id de aceite `20261103T002534Z-7e1e21`

| run_id | started_at | step | status | duration_s | error |
|---|---|---|---|---|---|
| 20261103T002534Z-7e1e21 | 2026-11-03 00:26:11.667185+00:00 | bronze.alunos | SUCCEEDED | 0.2 |  |
| 20261103T002534Z-7e1e21 | 2026-11-03 00:26:12.094883+00:00 | bronze.municipio | SUCCEEDED | 0.17 |  |
| 20261103T002534Z-7e1e21 | 2026-11-03 00:26:12.304238+00:00 | bronze.uf | SUCCEEDED | 0.18 |  |
| 20261103T002534Z-7e1e21 | 2026-11-03 00:26:12.542588+00:00 | bronze.meta_alfabetizacao_brasil | SUCCEEDED | 0.21 |  |
| 20261103T002534Z-7e1e21 | 2026-11-03 00:26:12.801490+00:00 | bronze.meta_alfabetizacao_uf | SUCCEEDED | 0.2 |  |
| 20261103T002534Z-7e1e21 | 2026-11-03 00:26:13.043483+00:00 | bronze.meta_alfabetizacao_municipio | SUCCEEDED | 0.22 |  |
| 20261103T002534Z-7e1e21 | 2026-11-03 00:26:13.302776+00:00 | bronze.dicionario | SUCCEEDED | 0.19 |  |
| 20261103T002534Z-7e1e21 | 2026-11-03 00:26:13.543102+00:00 | bronze.diretorio_municipio | SUCCEEDED | 0.2 |  |
| 20261103T002534Z-7e1e21 | 2026-11-03 00:27:48.733325+00:00 | dbt.silver | SUCCEEDED | 51.57 |  |
| 20261103T002534Z-7e1e21 | 2026-11-03 00:29:28.635097+00:00 | dbt.gold | SUCCEEDED | 37.93 |  |
| 20261103T002534Z-7e1e21 | 2026-11-03 00:31:11.591144+00:00 | publish.gold | SUCCEEDED | 24.92 |  |

## Qualidade por execução (inclui reprovações)

| run_id | fault_injection | executado_em | aprovados | bloqueantes_reprovados | informativos_alertados | erros |
|---|---|---|---|---|---|---|
| 20261103T002534Z-7e1e21 | none | 2026-11-03 00:28:38.927336+00:00 | 93 | 0 | 4 | 0 |
| 20261102T234111Z-6ef6e8 | none | 2026-11-02 23:45:27.881740+00:00 | 93 | 0 | 4 | 0 |
| 20261102T233638Z-1e9916 | avaliado_inconsistente | 2026-11-02 23:40:13.975631+00:00 | 59 | 1 | 2 | 0 |
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

## ADR-008/009 — testes registrados em ops.dq_results

| run_id | executed_at | test_name | severidade | status | failures | fault_injection |
|---|---|---|---|---|---|---|
| 20261103T002534Z-7e1e21 | 2026-11-03 00:30:05.119168+00:00 | assert_ml_sem_vazamento | bloqueante | pass | 0 | none |
| 20261103T002534Z-7e1e21 | 2026-11-03 00:28:38.927336+00:00 | assert_avaliados_completos | bloqueante | pass | 0 | none |

## ADR-008 — reprovacoes controladas efetivamente registradas

| run_id | executado_em | falhas | silver_failed | gold_executada | publicacao_executada |
|---|---|---|---|---|---|
| 20261102T233638Z-1e9916 | 2026-11-02 23:40:13.975631+00:00 | 30 | 1 | 0 | 0 |

## ADR-009 — schema real da Gold ML publicada

| tabela | pos | coluna | tipo |
|---|---|---|---|
| ml_features_municipio | 1 | id_municipio | STRING |
| ml_features_municipio | 2 | rede_canonica | STRING |
| ml_features_municipio | 3 | ano_referencia | INT64 |
| ml_features_municipio | 4 | sigla_uf | STRING |
| ml_features_municipio | 5 | regiao | STRING |
| ml_features_municipio | 6 | capital_uf | BOOL |
| ml_features_municipio | 7 | feat_taxa_t | FLOAT64 |
| ml_features_municipio | 8 | feat_variacao_pp_t | FLOAT64 |
| ml_features_municipio | 9 | feat_media_portugues_t | FLOAT64 |
| ml_features_municipio | 10 | feat_prop_nivel_0_t | FLOAT64 |
| ml_features_municipio | 11 | feat_prop_nivel_1_t | FLOAT64 |
| ml_features_municipio | 12 | feat_prop_nivel_2_t | FLOAT64 |
| ml_features_municipio | 13 | feat_prop_nivel_3_t | FLOAT64 |
| ml_features_municipio | 14 | feat_prop_nivel_4_t | FLOAT64 |
| ml_features_municipio | 15 | feat_prop_nivel_5_t | FLOAT64 |
| ml_features_municipio | 16 | feat_prop_nivel_6_t | FLOAT64 |
| ml_features_municipio | 17 | feat_prop_nivel_7_t | FLOAT64 |
| ml_features_municipio | 18 | feat_prop_nivel_8_t | FLOAT64 |
| ml_features_municipio | 19 | feat_alunos_avaliados_ponderado_t | FLOAT64 |
| ml_features_municipio | 20 | feat_proficiencia_media_t | FLOAT64 |
| ml_features_municipio | 21 | feat_distancia_media_uf_pp_t | FLOAT64 |
| ml_features_municipio | 22 | alvo_taxa_t_mais_1 | FLOAT64 |
| ml_features_municipio | 23 | particao | STRING |
| ml_features_municipio | 24 | origem_dado | STRING |
| ml_features_municipio | 25 | _run_id | STRING |
| ml_features_municipio | 26 | _processed_at | TIMESTAMP |

## Fase 3 — exports de ML realmente executados

| run_id | started_at | status | snapshot | versao | gold_published_run_id | parquet_gcs | erro |
|---|---|---|---|---|---|---|---|
| 20261103T003232Z-114aed | 2026-11-03 00:32:46.648685+00:00 | SUCCEEDED | midyear-cursor-510311-v9.gold.ml_features_municipio_fase3_20261103_4531e38 | 2026-11-03-4531e38 | 20261103t002534z-7e1e21 | gs://midyear-cursor-510311-v9-alfab-lake/gold/ml/fase3/versao=2026-11-03-4531e38/part-*.parquet |  |
| 20261102T230925Z-77d8ea | 2026-11-02 23:09:25.393547+00:00 | SUCCEEDED | midyear-cursor-510311-v9.gold.ml_features_municipio_fase3_20261102 |  |  | gs://midyear-cursor-510311-v9-alfab-lake/gold/ml/fase3/versao=2026-11-02/part-*.parquet |  |
| 20261001T205055Z-d57ca8 | 2026-10-01 20:50:55.562686+00:00 | SUCCEEDED | midyear-cursor-510311-v9.gold.ml_features_municipio_fase3_20261001 |  |  | gs://midyear-cursor-510311-v9-alfab-lake/gold/ml/fase3/versao=2026-10-01/part-*.parquet |  |

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
| 2026-11-03 00:00:00+00:00 | 14 | 5.072 | 5.1 | 5.1 | 193.624 |
| 2026-11-02 23:55:00+00:00 | 22 | 5.073 | 5.733 | 5.8 | 313.643 |
| 2026-11-02 23:50:00+00:00 | 548 | 0.057 | 18.339 | 20.527 | 202.9 |
