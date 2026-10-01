# Demonstração de falha: regra bloqueante interrompe o pipeline

Execução do Cloud Workflows `b2078429-4134-4fbe-843b-cb64a9a49e07` (run_id `20261001T172800Z-b20784`), disparada com
`{"fault_injection": "duplicate_keys"}`: a Silver duplica de propósito ~1% das linhas de `indicador_municipio`.

| Evidência | Resultado |
|---|---|
| Estado do workflow | **FAILED** (início 2026-10-01T17:28:00Z, fim 2026-10-01T17:37:21Z) |
| Etapa que falhou | `dbt.silver`, código de saída 3 (regra bloqueante) |
| Regra reprovada | `unique_combination_indicador_municipio_ano__id_municipio__rede_codigo` (303 chaves duplicadas) |
| Dado ruim na Silver | 24298 linhas para 23995 chaves distintas |
| Etapas `dbt.gold` e `publish.gold` | **não executaram** |
| Gold publicada (10 tabelas: `modified` e `published_run_id`) | **idêntica ao estado anterior** (ver `demo_falha_gold_antes.json`) |
| Resultado persistido | `ops.pipeline_runs` (linha FAILED) e `ops.dq_results` (1 fail, 59 pass, 3 skipped, 1 warn) |

## Etapas registradas em ops.pipeline_runs
| etapa | status | duração (s) | erro |
|---|---|---|---|
| dbt.silver | FAILED | 57.8 | QualityGateFailed: 1 regra(s) bloqueante(s) reprovada(s) em silver: ['unique_combination_indicador_municipio_ano__id_municipio__rede_codigo'] |
