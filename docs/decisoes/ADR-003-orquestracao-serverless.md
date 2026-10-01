# ADR-003: Workflows + Cloud Run Jobs em vez de Composer/Dataflow

**Status:** aceita

## Contexto
O volume é de milhões de linhas, não de bilhões. Cloud Composer custa centenas de dólares por mês parado,
e Dataflow tem custo mínimo por worker sempre ligado.

## Decisão
- Cada etapa é um Cloud Run Job da mesma imagem (`python -m alfab <comando>`).
- Cloud Workflows encadeia as etapas com dependência, injeta o mesmo `run_id` em todas e repete erros
  transitórios de API. O Cloud Run Job tem `max_retries` próprio (ingest/publish = 1; dbt = 0).
- Cloud Scheduler dispara o batch a cada 6 h e o micro-lote a cada 5 min.
- Tudo escala a zero.

## Consequências
- Custo de orquestração dentro do free tier na cadência pretendida (ver a tabela de FinOps).
- Sem uma UI de DAG como a do Airflow. A visibilidade vem do console do Workflows, de
  `ops.pipeline_runs` e de `ops.vw_saude_pipeline`.
- dbt não tem retry no nível do job, porque falha de qualidade é determinística. Erros transitórios de
  SQL são repetidos pelo próprio dbt-bigquery (`job_retries`).
