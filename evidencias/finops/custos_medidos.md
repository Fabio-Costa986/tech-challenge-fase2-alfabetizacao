# Estimativa de custo (medida)

Gerado em 2026-10-01 20:47 UTC por `python -m alfab finops`. Janela de medição: 7 dias. Cadência projetada (produção): 120 execuções batch/mês (a cada 6 h) e micro-lote a cada 5 min. Preços de lista (US) conferidos em 2026-09-30.

Duas leituras do mesmo desenho: **preço de lista** (sem nenhum nível gratuito: é o custo se a franquia já estiver consumida por outras cargas) e **com o nível gratuito mensal** do GCP.

| Serviço | Unidade | Quantidade medida | Como foi medida | Preço unitário | Custo mensal de lista (US$) | Com nível gratuito (US$) |
|---|---|---:|---|---|---:|---:|
| BigQuery: ingestão da fonte (EXPORT DATA) | GiB faturado por ingestão completa | 0,3193 | INFORMATION_SCHEMA.JOBS, label camada=bronze (dry run das 8 entidades: 0.25 GiB). Só ocorre quando a fonte muda: 1/mês | US$ 6.25/TiB | 0.00 | 0.00 |
| BigQuery: Silver + Gold + testes (dbt) | GiB faturado por execução | 2,005 | INFORMATION_SCHEMA.JOBS por run_id, mediana de 2 execuções publicadas; 120 execuções/mês | US$ 6.25/TiB (1 TiB/mês grátis no total) | 1.47 | 0.00 |
| BigQuery: armazenamento | GiB-mês (lógico ativo) | 0,8739 | soma de size_bytes em <dataset>.__TABLES__ (bronze, silver, gold_staging, gold, ops) | US$ 0.02/GiB (10 GiB grátis) | 0.02 | 0.00 |
| Cloud Storage: Bronze Parquet ZSTD | GiB-mês | 0,05596 | soma de 18 objetos em gs://midyear-cursor-510311-v9-alfab-lake (1 snapshot das 8 entidades) | US$ 0.026/GiB | 0.00 | 0.00 |
| Pub/Sub + streaming insert (eventos) | GiB/mês | 0,001384 | 1206 entregas em 7d em bronze.eventos_raw (payload + ~200 B de envelope), x 30/7 | US$ 40.0/TiB (10 GiB grátis) + US$ 0.05/GiB | 0.00 | 0.00 |
| Cloud Run Jobs (batch + micro-lote) | vCPU-s/mês | 156.507 | ops.pipeline_runs: 148 s por batch publicado x 120/mês; 16.1 s por micro-lote (média de 3) x 8640/mês; 1 vCPU, 2 GiB. Não inclui o tempo de inicialização do container | US$ 1.8e-05/vCPU-s + US$ 2e-06/GiB-s (180,000 vCPU-s grátis) | 3.44 | 0.00 |
| Workflows + Cloud Scheduler | passos/mês | 1.440 | 12 passos (workflows/pipeline_batch.yaml) x 120/mês; 2 jobs do Scheduler | US$ 0,01/1.000 passos (5.000 grátis); US$ 0,10/job (3 grátis) | 0.21 | 0.00 |

**Total projetado: US$ 5.15/mês a preço de lista; US$ 0.00/mês com o nível gratuito.**
