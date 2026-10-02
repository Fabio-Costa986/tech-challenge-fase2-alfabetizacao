-- Indicador oficial por UF + volume de alunos avaliados (ponderado) para agregação nacional correta.
SELECT
  i.ano,
  i.sigla_uf,
  i.regiao,
  i.serie,
  i.rede_codigo,
  i.rede,
  i.rede_canonica,
  i.taxa_alfabetizacao,
  i.media_portugues,
  {% for n in range(9) -%}
  i.proporcao_aluno_nivel_{{ n }},
  {% endfor -%}
  m.n_avaliados AS alunos_avaliados,
  m.peso_avaliados AS alunos_avaliados_ponderado,
  m.proficiencia_media_ponderada,
  {{ lineage_columns() }}
FROM {{ ref('indicador_uf') }} i
LEFT JOIN {{ ref('agg_microdado_recorte') }} m
  ON m.nivel = 'UF' AND m.id_local = i.sigla_uf AND m.ano = i.ano AND m.recorte = i.rede_canonica
