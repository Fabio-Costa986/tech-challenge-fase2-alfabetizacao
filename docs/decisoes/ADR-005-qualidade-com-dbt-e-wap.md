# ADR-005: Qualidade com dbt + Write-Audit-Publish na Gold

**Status:** aceita

## Decisão
- dbt Core: `severity: error` = bloqueante, `severity: warn` = informativa. O `dbt build` testa cada
  modelo logo depois de construí-lo.
- Silver e Gold rodam em invocações separadas. Se a Silver reprova, o Workflow não chama a Gold.
- A Gold é construída em `gold_staging` e copiada para `gold` (copy job, sem custo) só se todos os testes
  passarem. Os consumidores leem `gold`.
- O resultado de cada teste vai para `ops.dq_results` (hook on-run-end), inclusive em execuções
  reprovadas.
- O entrypoint propaga o código de saída (0 = ok, 3 = qualidade, 1 = erro). O único `except` genérico
  (`cli.main`) converte a exceção em código diferente de zero e nunca termina com sucesso. Há teste
  automatizado para isso.
