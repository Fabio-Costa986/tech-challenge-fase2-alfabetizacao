# ADR-001: Acessar a fonte nativamente no BigQuery (região US)

**Status:** aceita

## Contexto
A Base dos Dados publica `br_inep_avaliacao_alfabetizacao` no BigQuery público (multi-região US) e
também como arquivos para download. O enunciado aceita os dois caminhos e pede a justificativa.

## Decisão
Ler direto do BigQuery público, com colunas explícitas, e materializar a Bronze com `EXPORT DATA`.
Todos os datasets e o bucket do projeto ficam em `US`.

## Consequências
- **Custo:** pagamos bytes escaneados (on-demand; 1 TiB/mês grátis). Não há egress: fonte, warehouse e
  lake estão na mesma nuvem e região. `EXPORT DATA` não cobra além do scan.
- **Medição:** cada leitura tem dry run antes, e o número entra na tabela de FinOps.
- **Atualização da fonte:** `modified` da tabela de origem (via API, sem custo) é comparado com
  `ops.source_watermarks`. Fonte igual: entidade pulada. Fonte nova: novo snapshot imutável.
- **Risco:** dependência do projeto público. Uma mudança de schema faz o `EXPORT` falhar (colunas
  explícitas) ou reprova testes bloqueantes da Silver, em vez de propagar dado errado.
- **Alternativa descartada:** download + upload. Exigiria transferência e armazenamento duplicado, e
  perderia o dry run como ferramenta de medição.
- **Restrição:** usar a região `southamerica-east1` impediria joins com a fonte (o BigQuery não junta
  regiões diferentes) e exigiria cópia entre regiões.
