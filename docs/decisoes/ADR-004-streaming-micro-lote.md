# ADR-004: Streaming com Pub/Sub + push + micro-lote MERGE

**Status:** aceita

## Decisão
- Simulador → Pub/Sub (retenção de 7 dias) → push subscription autenticada (OIDC) → Cloud Run
  `event-ingestor`.
- O ingestor valida o contrato (pydantic), carimba `ingested_at` e grava em `bronze.eventos_raw`. Evento
  inválido vai para `bronze.eventos_quarentena` com o motivo e recebe ACK. Erro de escrita retorna 5xx,
  o Pub/Sub tenta de novo com backoff e, depois de 5 tentativas, manda a mensagem para a DLQ.
  A subscription de inspeção da DLQ (`alfab-eventos-dlq-inspect`) não expira: no padrão do Pub/Sub ela
  seria apagada após 31 dias sem atividade, o que aconteceu entre 01/10 e 02/11/2026 e deixou o alerta
  da DLQ sem efeito até o Terraform recriá-la.
- Micro-lote a cada 5 min: janela por watermark com lookback de 10 min, dedup `ROW_NUMBER()` por
  `event_id`, validação referencial (o município existe) e `MERGE` na Silver (horizonte de dedup de 7 dias).
- A Gold recebe o evento por views (`gold.vw_indicador_consolidado`, `gold.vw_eventos_tempo_real`),
  sempre com `origem_dado = 'SIMULADO'`.

## Alternativas descartadas
- **Dataflow:** worker sempre ligado; desproporcional ao volume.
- **BigQuery continuous queries:** exigem reserva Enterprise.
- **Schema no tópico (Avro):** rejeitaria a mensagem malformada já no publish, sem deixar rastro na
  quarentena. Preferimos validar no consumidor e registrar o motivo. Em produção, as duas camadas podem
  coexistir.

## Garantias
Entrega at-least-once e resultado efetivamente exactly-once na Silver (MERGE idempotente). A ordem não
é garantida; o estado mais recente é decidido por `produced_at` (last-write-wins).
