# ADR-008: Avaliados com classificacao e peso validos sao bloqueantes

**Status:** aceita pelo grupo em 28/10/2026; implementada em codigo, pendente de nova validacao em GCP.

## Contexto

A taxa de alfabetizacao do microdado so e calculavel para estudantes **avaliados**
(`presenca = codigo_presente` **e** `preenchimento_caderno = codigo_caderno_preenchido`).
Antes, a Silver aceitava `alfabetizado IS NULL` ate uma taxa de 1% com `severity: warn`
e peso invalido tambem gerava apenas aviso. O numerador e o denominador da Gold
usavam filtros que poderiam excluir subconjuntos distintos se a fonte mudasse.

## Decisao

1. Reprovar a **Silver** quando um estudante `avaliado = TRUE` tiver
   `alfabetizado IS NULL`, `peso_aluno IS NULL`, peso `<= 0`, `NaN` ou infinito.
   O teste `assert_avaliados_completos.sql` retorna os recortes afetados
   (ano, municipio e rede), com contagens por causa, e possui tag `silver`
   e severidade **error** (zero inconsistencias toleradas entre avaliados).
2. Preservar o criterio original de avaliado. Nao alterar `alfabetizado` nem
   imputar classificacoes; pesos e classificacoes nulos de **nao avaliados**
   continuam permitidos (ausentes nao pertencem ao denominador).
3. Calcular o denominador da taxa ponderada na Gold com o MESMO conjunto de
   `peso_avaliados`: todos os avaliados, aprovados pelo portao de qualidade.
   O numerador continua limitado a avaliados alfabetizados.
4. Apos reprovacao da Silver, a invocacao dbt encerra com erro (codigo 3) e
   o Workflow nao executa `dbt-gold` nem `publish-gold`; o dataset `gold`
   anteriormente publicado permanece inalterado. `run_dbt.run` tambem valida
   `dbtRunnerResult.success`, impedindo liberar a etapa em build inconclusivo.
5. Preservar os avisos de distribuicao historica (`warn`) para os demais
   registros; **eles nao substituem** a regra bloqueante para avaliados.

## Justificativa e custo da escolha

Exclusao silenciosa de avaliados altera a amostra e pode enviesar a taxa de
alfabetizacao, sobretudo por rede e municipio. Parar o pipeline preserva
integridade e permite investigar a fonte antes de mudar um produto analitico.
O custo e que novas cargas podem ficar bloqueadas ate a origem ser corrigida;
a ultima Gold aprovada continua disponivel.

## Codigo / testes / aceite

- [dbt/tests/singular/assert_avaliados_completos.sql](../../dbt/tests/singular/assert_avaliados_completos.sql)
- [dbt/models/silver/silver.yml](../../dbt/models/silver/silver.yml)
- [dbt/models/gold/agg_microdado_recorte.sql](../../dbt/models/gold/agg_microdado_recorte.sql)
- [dbt/models/gold/unit_tests.yml](../../dbt/models/gold/unit_tests.yml): 75% para pesos 3+1, com ausentes excluidos.
- [src/alfab/quality/run_dbt.py](../../src/alfab/quality/run_dbt.py): erro explicito em resultado dbt inconclusivo.
- Provar em ambiente de **teste**: dados validos passam; 1 avaliado sem
  classificacao e 1 com peso invalido reprovam. Conferir que a Gold aprovada
  nao mudou e que `ops.dq_results` registra o teste.

**Limite:** a protecao da ultima Gold aqui se refere a falha detectada na Silver.
Publicacao parcial diante de falha da copia entre tabelas durante `publish.gold`
e uma limitacao independente da implementacao WAP atual.

**Evidencia:** o profiling de 01/10/2026 nao identificou avaliado sem
classificacao/peso valido; a regra nova e preventiva. Nenhuma nova execucao
GCP foi realizada como parte deste commit; ver
[roteiro de validacao](../validacao_ajustes_silver_gold.md).
