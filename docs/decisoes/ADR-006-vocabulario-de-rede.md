# ADR-006: Vocabulário canônico de rede

**Status:** aceita

## Contexto
No `schema.yml` oficial da Base dos Dados, o dicionário cobre `rede` e `serie` apenas nas tabelas
`municipio` e `uf`. As tabelas de meta não são cobertas. Além disso, `meta_alfabetizacao_municipio`
contempla só a rede municipal, enquanto as metas de UF e Brasil contemplam a rede pública. É o caso
clássico de chaves que não falam a mesma língua.

## Decisão
- `silver.rede_map` lista **toda** representação de rede encontrada nas 6 entidades, traduz pelo
  dicionário (mesma tabela → outra tabela → texto da própria fonte), normaliza (minúsculas, sem acento,
  sem "rede ") e mapeia para um vocabulário canônico pelo seed `rede_sinonimos.csv`.
- Sem tradução = `DESCONHECIDO`, reprovado por teste bloqueante.
- Resultado e meta só são comparados quando têm a mesma `rede_canonica` e o mesmo ano.
- Para o microdado, `rede_recortes.csv` define a composição dos recortes (pública = federal + estadual +
  municipal).

## Consequências
Um valor novo na fonte para o pipeline até alguém mapeá-lo de forma consciente.
