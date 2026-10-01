# Investigação de anomalias

> **Estado:** H1, H3, H7 e H8 investigadas com o profiling de 2026-10-01
> (`python -m alfab profile`, resultados em `evidencias/profiling/`). As demais dependem da primeira
> execução do pipeline. Cada hipótese abaixo vem com a evidência que a confirma ou descarta. Ao investigar, preencher
> **Observado**, **Causa** e **Decisão** com números e `job_id`. Não registrar conclusão sem número.

## H1: o flag `alfabetizado` corresponde a proficiência ≥ 743?
- **Por que importa:** o indicador é definido pelo corte de 743 pontos. Se o flag divergir da
  proficiência, a validação cruzada falha por definição, não por erro do pipeline.
- **Evidência:** `evidencias/profiling/06_alfabetizado_vs_corte_743.csv`.
- **Observado:** `alfabetizado = 1` -> 1.984.546 alunos, todos com proficiência ≥ 743 e nenhum abaixo.
  `alfabetizado = 0` -> 1.370.115 com proficiência < 743, nenhum ≥ 743, e 513.338 sem proficiência
  (ausentes ou prova não preenchida).
- **Causa:** o flag é derivado do corte de 743 na própria fonte.
- **Decisão:** usar o flag como numerador. A validação cruzada não terá divergência causada por definição.

## H2: a validação cruzada converge?
- **Evidência:** `gold.validacao_cruzada_microdado`, colunas `diff_pp`, `diff_pp_sem_peso_ERRADA`,
  `diff_pp_com_ausentes_ERRADA`.
- Se `diff_pp` estiver perto de 0 e as colunas `*_ERRADA` estiverem longe, o pipeline está certo e as
  armadilhas têm tamanho mensurável. Registrar esses tamanhos: é um resultado.
- Se `diff_pp` estiver longe de 0, testar nesta ordem: definição de avaliado (presença × preenchimento),
  recorte de rede (`rede_recortes.csv`), peso (`peso_aluno` nulo ou zero) e cobertura (`tem_microdado`).
- Observado: _a preencher_

## H3: as redes falam a mesma língua?
- **Evidência:** `evidencias/profiling/02_rede_por_tabela.csv` e `silver.rede_map` (`metodo_traducao`,
  `n_significados`).
- Esperado pela documentação da fonte: códigos nas tabelas de indicador e representação própria nas
  tabelas de meta.
- **Observado:** as tabelas de indicador usam códigos (`municipio`: 0, 2, 3, 5; `uf`: 0, 2, 3, 5), e o
  dicionário traduz `5` = "Pública (Estadual e Municipal)", `6` = "Pública (Federal, Estadual e
  Municipal)" e `0` = "Total (Federal, Estadual, Municipal e Privada)". As tabelas de meta usam **texto**:
  "Pública" (Brasil e UF) e "Municipal" (município). `alunos.rede` usa 2, 3, 4 (sem federal; 25 alunos
  da rede privada).
- **Causa:** representações diferentes da mesma dimensão no mesmo dataset.
- **Decisão:** `rede_sinonimos.csv` mapeia as descrições reais. "Pública" das metas = código 5 (estadual
  + municipal), e a pública com federal (código 6) virou uma categoria canônica própria
  (`publica_com_federal`) para nunca ser confundida. `rede_recortes.csv` foi corrigido: o recorte
  `publica` do microdado soma só estadual + municipal. A premissa inicial (incluir federal) estava errada
  e teria gerado uma validação cruzada enviesada sem nenhum erro aparente.

## H4: municípios com indicador e sem meta pactuada
- **Evidência:** `gold.meta_vs_resultado` com `status_meta = 'SEM_META'` no nível MUN, e
  `ops.join_match_rate` (`indicador_municipio__meta_municipio`).
- Pergunta: é falta de adesão (esperado) ou chave que não casa (erro)? Comparar com a cobertura de
  `meta_alfabetizacao_municipio` por UF.
- Observado: _a preencher_

## H5: consistência entre a tabela de meta e a tabela de indicador
- **Evidência:** testes `assert_consistencia_meta_vs_indicador_*` em `ops.dq_results`.
- Observado: _a preencher_

## H6: média simples × indicador nacional
- **Evidência:** `gold.fct_alfabetizacao_brasil` (`taxa_oficial`, `taxa_ponderada_ufs`,
  `media_simples_ufs`).
- Registrar a diferença em p.p. É o argumento numérico para nunca usar média simples.
- Observado: _a preencher_

## H7: o ano mais recente só existe nas tabelas de meta
- **Observado:** `municipio` e `uf` vão de 2023 a 2024. `meta_alfabetizacao_brasil` e
  `meta_alfabetizacao_uf` trazem `taxa_alfabetizacao` também para **2025** (Brasil, rede pública: 55,9 em
  2023 → 59,2 em 2024 → 66,0 em 2025). A trajetória pactuada também muda conforme a linha de base:
  `meta_alfabetizacao_2024` do Brasil = 59,9 nas linhas de 2023/2024 e 60,0 na de 2025.
- **Causa:** as tabelas de meta são atualizadas com a nova publicação do ICA (última modificação
  2026-03-24) antes das tabelas de indicador (2026-01-14).
- **Decisão:** `gold.resultado_oficial` usa a tabela de indicador como fonte principal e completa, com a
  taxa da tabela de meta, apenas as combinações ausentes, registrando `fonte_resultado`. Para a meta, vale
  a trajetória da linha de base mais recente (`ano_referencia`). Sem isso, a comparação meta × resultado
  perderia 2025, o único ano em que o Brasil aparece acima da meta.

## H8: ausentes não têm peso amostral
- **Observado:** os 512.153 ausentes e os 1.185 presentes com prova não preenchida têm `peso_aluno` e
  `proficiencia` **nulos**.
- **Decisão:** o denominador ponderado já os exclui naturalmente. A coluna didática
  `taxa_denominador_com_ausentes_ERRADA` passou a ser calculada por contagem, porque por peso ela seria
  igual à correta e não mostraria a armadilha.

## H9: recorte "total" não é recomponível a partir do microdado (achado da 1ª execução)
- **Observado:** na execução `20261001T131455Z-325f14`, a regra bloqueante `alunos__indicador_uf` reprovou
  com 142/192 grupos (74%). 48 dos 50 grupos sem par eram do recorte `total` (todas as redes, incluindo
  a privada). O indicador UF só publica `total` para 1 UF em 2024, e o microdado tem só 25 alunos
  da rede privada.
- **Causa:** erro nosso de universo. O microdado da avaliação cobre as redes públicas; "total" não pode ser
  recomposto a partir dele. O portão de qualidade funcionou: a Gold não foi construída.
- **Decisão:** `total` foi removido de `rede_recortes.csv` (o limiar de 95% não foi alterado).

## H10: DF sem indicador estadual/público em 2024
- **Observado:** o microdado tem alunos avaliados da rede estadual do DF em 2024, mas `uf` não publica
  linha para DF/estadual nem para DF/pública em 2024 (2023 existe).
- **Decisão:** lacuna da fonte, mantida. Esses 2 grupos ficam sem validação cruzada (`tem_microdado`
  / taxa de match de 142/144 = 98,6%).

## H11: divergência entre tabela de meta e tabela de indicador em municípios do CE
- **Observado:** regra informativa `assert_consistencia_meta_vs_indicador_municipio` com 3 casos em 2023
  (rede municipal): 2305100 (55,6 na meta × 91,67 no indicador), 2304905 (83,1 × 99,15),
  5106752 (68,0 × 65,94).
- **Decisão:** a tabela de indicador é a fonte principal de `resultado_oficial` (ver H7). Os casos ficam
  registrados como informativos e merecem consulta ao Inep. Não bloqueiam, porque são 3 em ~10 mil.
