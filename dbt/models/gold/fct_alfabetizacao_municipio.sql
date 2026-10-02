{{ config(cluster_by=['sigla_uf', 'id_municipio']) }}

-- Indicador oficial por município, enriquecido com território e volume de alunos avaliados
-- (peso para agregações corretas). Uma linha por ano x município x rede.
SELECT
  i.ano,
  i.id_municipio,
  d.nome_municipio,
  i.sigla_uf,
  d.regiao,
  d.capital_uf,
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
FROM {{ ref('indicador_municipio') }} i
LEFT JOIN {{ ref('diretorio_municipio') }} d USING (id_municipio)
LEFT JOIN {{ ref('agg_microdado_recorte') }} m
  ON m.nivel = 'MUN' AND m.id_local = i.id_municipio AND m.ano = i.ano AND m.recorte = i.rede_canonica
