# Regras de qualidade de dados

Toda regra é um teste dbt versionado. **Bloqueante** usa `severity: error` (padrão do projeto, em
[dbt/dbt_project.yml](../dbt/dbt_project.yml)). Quando reprova, o `dbt build` sai com falha, o job termina
com código 3, o Workflow para e **a camada seguinte não é publicada**. **Informativa** usa
`severity: warn`: ela é registrada e alertada, mas não para o fluxo.

Todo resultado (pass, fail, warn, error) vai para `ops.dq_results` pelo hook `on-run-end`
([dbt/macros/log_dq_results.sql](../dbt/macros/log_dq_results.sql)). O hook roda **também quando a
execução falha**, então a reprovação fica registrada.

## Portões

| Portão | Onde roda | Se reprovar |
|---|---|---|
| Completude da Bronze | `ingest-bronze`: linhas exportadas = linhas da origem | Job falha; Silver não roda |
| Silver | `dbt build --select tag:seeds tag:silver tag:quality` | Workflow para; Gold não é construída |
| Gold (Write-Audit-Publish) | `dbt build --select tag:gold` em `gold_staging` | `publish-gold` não roda; `gold` continua com a última versão aprovada |

## Catálogo

| Categoria (enunciado) | Regra | Modelo(s) | Tipo | Limiar e justificativa |
|---|---|---|---|---|
| Duplicidade | `unique_combination` no grão de cada tabela | todas as Silver e Gold | Bloqueante | 0. É o grão oficial da fonte (o mesmo do `schema.yml` da Base dos Dados) |
| Ausentes | `not_null` em chaves | Silver | Bloqueante | 0. Chave nula não junta com nada |
| Ausentes | `null_rate_below` em medidas | `taxa_alfabetizacao`, `proficiencia`, `alfabetizado` | Informativa | 10% (município), 5% (UF), 2%/1% (alunos avaliados). Ajustar ao baseline medido no profiling |
| Domínio | `between` 0–100 em taxas e metas; proficiência > 0 | Silver | Bloqueante | Fora disso o valor é impossível |
| Fallback explícito | `no_unknown_category` (DESCONHECIDO = 0) | rede, série, presença, preenchimento, alfabetizado | Bloqueante | Um código novo da fonte precisa ser mapeado conscientemente, nunca absorvido por um `else` |
| Códigos assumidos | `assert_codigos_alunos_no_dicionario` | dicionário | Bloqueante | O código usado como "presente/preenchido/alfabetizado" precisa ter essa descrição no dicionário oficial |
| Chaves de relacionamento | `relationships` UF → `uf_ibge` | `indicador_uf` | Bloqueante | 27 UFs fixas |
| **Taxa de match dos joins** | `join_match_rate` + `assert_join_match_*` | 7 junções (abaixo) | Bloqueante/Informativa | [seeds/join_thresholds.csv](../dbt/seeds/join_thresholds.csv) |
| Consistência entre tabelas | taxa da tabela de meta = taxa da tabela de indicador | UF: bloqueante; município: informativa | — | 0,1 p.p.: as duas tabelas vêm da mesma publicação do Inep, então a diferença esperada é só de arredondamento |
| Consistência agregada | Brasil oficial ≈ UFs ponderadas por alunos | `fct_alfabetizacao_brasil` | Informativa | 1 p.p. |
| Validação cruzada | microdado recalculado ≈ taxa publicada | UF com ≥ 5.000 avaliados e Brasil com cobertura completa: bloqueante; UF < 5.000 e município (n ≥ 30): informativa | — | 0,5 p.p. (bloqueante); 2 p.p. (informativa). Critério de porte/cobertura calibrado após a 1ª execução (ver investigação H2) |
| Vazamento de alvo | `assert_ml_sem_vazamento` | `ml_features_municipio` | Bloqueante | Nenhuma coluna gap/status/atingiu/diff; exatamente 1 alvo |
| Origem do dado | `accepted_values` origem = OFICIAL | fatos e features | Bloqueante | Simulado nunca entra na base oficial de ML |

## Taxa de correspondência das junções

O modelo [join_match_rate](../dbt/models/quality/join_match_rate.sql) mede cada junção a cada execução
e **acumula o histórico** (modelo incremental em `ops.join_match_rate`). **`total = 0` também reprova**:
significa que os dois lados não têm nenhuma chave em comum, que é o sintoma típico de "rede" representada
de formas diferentes.

| Junção | Limiar | Tipo | Por quê |
|---|---|---|---|
| indicador_municipio → diretório | 99% | Bloqueante | Código IBGE de 7 dígitos; queda indica chave corrompida |
| meta_municipio → diretório | 99% | Bloqueante | Idem |
| alunos → diretório | 99% | Bloqueante | Microdado sem município some da validação cruzada |
| indicador_uf → UFs | 100% | Bloqueante | Universo fechado de 27 |
| indicador_uf → meta_uf (mesma rede e ano) | 95% | Bloqueante | Toda UF tem meta pactuada na rede pública |
| indicador_municipio → meta_municipio | 50% / 90% | Bloqueante / Informativa | Nem todo município pactuou meta. Abaixo de 50% o problema é a chave; abaixo de 90%, a adesão (investigar) |
| alunos → indicador_uf (ano, UF, recorte) | 95% | Bloqueante | Sem isso a validação cruzada perde o sentido |

> Os limiares partem de premissas sobre a fonte. Depois do primeiro `python -m alfab profile` e da
> primeira execução, eles devem ser recalibrados com o baseline medido, e a decisão registrada aqui.

## Demonstração de falha

O pipeline tem dois modos de injeção de falha, controlados pela var `fault_injection` (CLI
`--fault-injection` ou argumento do Workflow):

| Modo | O que faz | Regra que deve reprovar |
|---|---|---|
| `duplicate_keys` | Duplica ~1% das linhas de `silver.indicador_municipio` | `unique_combination_indicador_municipio_*` (bloqueante) |
| `unmapped_rede` | Remove a tradução de um código de rede | `no_unknown_category_*rede_canonica` (bloqueante) e taxa de match |

```bash
make demo-falha
# ou: gcloud workflows run alfab-pipeline-batch --location us-central1 --data='{"fault_injection":"duplicate_keys"}'
```

Evidências a guardar em `evidencias/qualidade/`: a execução do Workflow como FAILED, a linha `fail` em
`ops.dq_results`, a linha FAILED em `ops.pipeline_runs`, o e-mail do alerta e o `last_modified` de
`gold.*` inalterado.
