# Validacao dos ajustes Silver/Gold (28/10/2026)

**Escopo aprovado:** (1) bloqueio de avaliados inconsistentes; (3) exclusao da
meta de t+1 sem data historica de publicacao da base de ML. **Item 2**
(cobertura minima da validacao cruzada) **nao foi alterado**.

**Base original da revisao:** ZIP/RAR recebido com HEAD `08efa0f`. O projeto original
na nuvem e suas evidencias de 01/10/2026 nao representam uma execucao desta
alteracao. O roteiro abaixo e um **plano de aceite**, nao um relatorio de
resultado GCP ja obtido.

## 1. Preparar e validar sem publicar

1. Conferir se a branch remota recebeu commits depois de `08efa0f` antes de
   substituir qualquer arquivo; preservar a pasta `.git` do clone existente.
2. Python 3.12, dependencias declaradas em `pyproject.toml`; usar `.env` local
   fora do Git (ver `README.md` e `.env.example`).
3. Executar `make test`, `python -m ruff check src tests` e `cd dbt && dbt parse
   --profiles-dir .`. O CI tambem realiza esses checks.
4. Testar `dbt build` no **ambiente GCP de homologacao**, nao em producao.
   Usar os mesmos seeds, mesmos snapshots Bronze e perfil de ambiente de
   testes da execucao aprovada para comparar os numeros.

## 2. Casos de aceite - Silver

| Cenario no ambiente de testes | Resultado esperado |
|---|---|
| Avaliado com classificacao preenchida e peso > 0 finito | Passa |
| Nao avaliado com peso e classificacao NULL | Passa (nao integra denominador) |
| Avaliado com `alfabetizado IS NULL` | `assert_avaliados_completos` falha, codigo 3 |
| Avaliado com peso `NULL`, 0, negativo, NaN ou infinito | Mesmo teste falha, codigo 3 |
| `dbtRunner` retorna `success=False` sem teste `fail` | Falha fechada, codigo 1 |
| 1 alfabetizado (peso 3) + 1 nao alfabetizado (peso 1) | Taxa ponderada = 75% nos 3 niveis |

Para os casos negativos, usar **fixtures isoladas no projeto/dataset de
homologacao**, jamais modificar `silver.alunos` ou Bronze do ambiente de
producao. A consulta abaixo ajuda a inspecionar dados reais (substituir projeto
com controle de acesso apropriado):

```sql
SELECT ano, id_municipio, rede_canonica,
       COUNTIF(alfabetizado IS NULL) AS sem_classificacao,
       COUNTIF(peso_aluno IS NULL OR peso_aluno <= 0
               OR IS_NAN(peso_aluno) OR IS_INF(peso_aluno)) AS peso_invalido
FROM `<PROJETO>.silver.alunos`
WHERE avaliado
GROUP BY 1, 2, 3
HAVING sem_classificacao > 0 OR peso_invalido > 0;
```

Se o teste reprovar, conferir `ops.dq_results` no `run_id` de homologacao:
`assert_avaliados_completos`, severidade `bloqueante`, status `fail`.
Confirmar que o Workflow parou **antes** de `dbt-gold` e `publish-gold` e
que as tabelas `gold.*` nao mudaram (comparar `published_run_id` e
`last_modified` antes/depois). Esta garantia se refere a falha na Silver.

## 3. Casos de aceite - ML

1. Conferir que `gold_staging.ml_features_municipio` nao possui
   `feat_meta_pactuada_t_mais_1` e que `assert_ml_sem_vazamento` passa.
2. Confirmar que `gold.meta_vs_resultado` ainda tem `meta_pactuada_pct`:
   a mudanca nao elimina comparacao historica de metas na Gold.
3. Validar que as demais features, o alvo e o grao
   `(id_municipio, rede_canonica, ano_referencia)` continuam consistentes.
4. Conferir **depois** do deploy/publicacao a tabela publicada:

```sql
SELECT table_name, column_name
FROM `<PROJETO>.gold.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'ml_features_municipio'
  AND column_name = 'feat_meta_pactuada_t_mais_1';
-- Esperado: zero linhas apos a Gold NOVA ser publicada.
```

5. Exportar **um novo snapshot** da Fase 3, com identificacao de versao/run_id.
   Nao reutilizar o snapshot/Parquet de `2026-10-01` para treinamento: sua
   estrutura e de antes da ADR-009. O export atual identifica versao por dia;
   conferir colisao antes de executar `make export-ml` no mesmo dia.

## 4. Deploy somente depois da revisao do grupo

- Registrar o commit/versao da imagem; o README contem o procedimento com
  `make deploy`, `make run-batch` e `make export-ml`.
- **Deploy da nova imagem e execucao do workflow sao obrigatorios:**
  editar SQL no Git **nao atualiza automaticamente** a Gold publicada.
- Evidenciar os novos IDs de job, data, testes e contagens em `evidencias/`
  somente apos a execucao real; nao substituir evidencias de outubro por
  alegacoes sem consulta na nuvem.
- Comparar o baseline da Gold antiga com a nova: volumes, pesos,
  taxas e resultado de qualidade. Recortes sem anomalias devem permanecer
  com as mesmas taxas (nao ha motivo para muda-las).
- Somente apos esses passos marcar a nova versao no README como validada
  em GCP e emitir o artefato analitico da Fase 3 atualizado.

**Observacao:** a publicacao de varias tabelas no `publish.gold` atual nao e
atomica em caso de falha durante copias; este limite ja existia e nao foi
reprojetado por estar fora das duas decisoes aprovadas.

## 5. Procedimento executavel de evidencias (preparado para a proxima rodada)

A coleta pós-ADR foi organizada em
[ROTEIRO_EVIDENCIAS_ADR008_ADR009.md](ROTEIRO_EVIDENCIAS_ADR008_ADR009.md).
Ela inclui comandos de aceite somente leitura, o registro nominal dos testes
em `ops.dq_results`, a foto da Gold antes/depois da falha controlada e a
prevenção de colisão no export de Fase 3. Esses recursos **não provam execução
na nuvem** por si só: seus arquivos só devem ser gerados com um `run_id` real.

A fixture `avaliado_incompleto` adiciona **somente linhas sintéticas à consulta
do teste singular** em homologação, nunca grava registros na Silver. Exige
`ALFAB_HML_PROJECT_ID` igual a `target.project` e é bloqueada fora do projeto
explicitamente configurado. Não configurar essa variável em produção.

As evidências foram regeneradas após o aceite de 03/11 (seção 6).

## 6. Resultado no GCP (02-03/11/2026)

Projeto `midyear-cursor-510311-v9`, o único do grupo. Execuções em ordem (UTC):

| Quando | run_id / workflow | Imagem | O que foi | Resultado |
|---|---|---|---|---|
| 02/11 22:58 | `20261102T225805Z-230ae9` | `pipeline:fd2d72c` (main pós-PR #2) | primeira execução com ADR-008/009 | publicada; 84 bloqueantes aprovadas |
| 02/11 23:36 | `20261102T233638Z-1e9916` | `pipeline:123b089` | teste negativo do ADR-008 **no projeto principal**, com injeção que gravava 19 avaliados sem classificação e 11 com peso zero na Silver | FAILED em `dbt.silver` (`assert_avaliados_completos`); Gold intacta; alerta em 4 min 3 s |
| 02/11 23:41 | `20261102T234111Z-6ef6e8` | `pipeline:123b089` | batch normal para restaurar a Silver | publicada |
| 03/11 00:25 | **`20261103T002534Z-7e1e21`** (workflow `7e1e21db-6776-4ec8-811a-e1619bdb4490`) | **`pipeline:4531e38`** (main pós-PR #4 + correção da DLQ) | execução de aceite | publicada; `validar-adrs`: **ACEITE GCP APROVADO** |

Observações:
- O teste negativo de 02/11 23:36 foi disparado um minuto antes do merge do PR #4, que passou a exigir
  homologação e um mecanismo de injeção que não grava na Silver. Aquele modo de injeção não está na `main`.
  O resultado fica registrado em `ops.pipeline_runs` e `ops.dq_results`, mas **não substitui** a seção 3
  do roteiro, que continua pendente por falta de um projeto de homologação.
- Pré-checagem nos dados reais: 0 avaliados sem classificação e 0 com peso inválido, em 3.354.661 avaliados.
- Resultados analíticos (Brasil, UFs, municípios, validação cruzada, universalização) idênticos aos de
  01/10; a única diferença é a coluna removida da base de ML (26 colunas).
- Fase 3: `python -m alfab export-ml --versao 2026-11-03-4531e38 --aceite-run-id 20261103T002534Z-7e1e21`
  gerou `gold.ml_features_municipio_fase3_20261103_4531e38` e `versao=2026-11-03-4531e38/` no GCS.
- Evidências regeneradas com `--aceite-run-id 20261103T002534Z-7e1e21` (`profile`, `evidencias`,
  `dashboard`); custos com `finops --dias 35`; incidentes com `scripts/incidentes_alerta.py`.

