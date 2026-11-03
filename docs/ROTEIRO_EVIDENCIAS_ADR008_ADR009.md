# Roteiro operacional — ADR-008 / ADR-009 e evidências pós-GCP

> **Estado em 03/11/2026:** seções 4 e 5 executadas no projeto principal (aceite
> `20261103T002534Z-7e1e21`, export `2026-11-03-4531e38`) e evidências regeneradas com
> `--aceite-run-id`; ver `docs/validacao_ajustes_silver_gold.md`, seção 6. **Pendentes:** seções 2 e 3
> em homologação (não há projeto de homologação). Os prints foram substituídos por exportação via API
> (`scripts/coletar_logs_gcp.py` → `evidencias/batch/`, `evidencias/streaming/`). Texto original abaixo:
>
> alterações de código preparadas. Este documento **não afirma** que
> a pipeline foi executada no GCP após os ADRs. A execução/aceite depende do
> integrante autorizado do grupo e de credenciais/infraestrutura separadas.
>
> **Não editar os CSVs/JSONs históricos manualmente.** Eles representam uma
> execução antiga e só devem ser substituídos por saídas reais dos coletores.

## 0. Responsabilidades e riscos

- **Responsável VS Code:** revisar patch, executar testes unitários, abrir PR e
  conferir os arquivos que serão regenerados. Não rodar `dbt build` no perfil
  padrão, pois `dbt/profiles.yml` usa `target: prod`.
- **Responsável GCP:** revisar projeto ativo, projeto de HOMOLOGAÇÃO distinto,
  IAM, custo e imagem implantada; executar positive/negative test e publicar a
  nova Gold **somente com autorização** do grupo.
- **Provas:** registrar projeto, commit, imagem, workflow execution ID, `run_id`,
  horários UTC, resultados dos testes, schema publicado, snapshot e prefixo GCS.
- **Limitação existente:** publicar várias tabelas de Gold não é operação atômica;
  a publicação só deve começar após os testes passarem.

## 1. Conferência local (não toca o GCP)

No clone `C:\dev\tech-challenge-fase2-alfabetizacao`, depois de aplicar o patch:

```powershell
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m pytest -q
py -3.12 -m ruff check src tests
py -3.12 -m compileall -q src tests
# dbt parse é apenas validação de projeto, não executa dbt build:
dbt parse --project-dir dbt --profiles-dir dbt
```

A execução de `dbt parse` pode precisar de variáveis de ambiente de configuração,
mas **não** deve executar consultas ou gravar dados no BigQuery. Não use
`make deploy`, `make run-batch` ou `dbt build` nesta etapa.

As decisões aprovadas continuam as mesmas: o ADR-008 bloqueia avaliado sem
classificação/peso válido; o ADR-009 remove a feature de meta t+1 sem prova
histórica de publicação. O item 2 (cobertura da validação cruzada) **não mudou**.

## 2. Homologação GCP — positiva

1. Confirmar o projeto GCP de homologação e o target dbt usando recursos
   isolados. Nunca apontar o teste para a Gold publicada do ambiente principal.
2. Conferir a revisão da imagem Cloud Run (contém este commit), ambiente e
   permissões. Configurar recursos apenas após revisão do grupo.
3. Executar um Workflow normal (`fault_injection: none`) em homologação.
4. Guardar o `run_id` retornado e os IDs de jobs.
5. Confirmar três etapas `SUCCEEDED`: `dbt.silver`, `dbt.gold`, `publish.gold`.
6. Confirmar ambos os testes em `ops.dq_results` com `status='pass'`,
   `severidade='bloqueante'` e mesmo `run_id`.
7. Confirmar que a tabela **publicada** `gold.ml_features_municipio` não tem
   `feat_meta_pactuada_t_mais_1`, mantém `alvo_taxa_t_mais_1` e o grão,
   e que `gold.meta_vs_resultado` ainda mantém `meta_pactuada_pct`.

Com credenciais **somente do projeto adequado** e após publicação positiva:

```powershell
python -m alfab validar-adrs --run-id <RUN_ID_POSITIVO>
```

A validação falha se faltar etapa/teste, se o schema antigo ainda estiver
publicado ou se o label `published_run_id` não corresponder ao `run_id`.

## 3. Homologação GCP — falha controlada ADR-008

Para reproduzir a reprovação sem modificar dados reais, o teste singular
`assert_avaliados_completos.sql` contém **duas linhas sintéticas apenas dentro
 da consulta do teste**, habilitadas exclusivamente quando:

- o Workflow recebe `fault_injection: "avaliado_incompleto"`;
- o ambiente do job `alfab-dbt-silver` informa `ALFAB_HML_PROJECT_ID`;
- `ALFAB_HML_PROJECT_ID` é **igual** ao projeto dbt em execução (`target.project`).

**Não configure `ALFAB_HML_PROJECT_ID` em produção.** Fora desse contexto,
a tentativa de injeção falha já na compilação do teste. A fixture injeta:
uma linha `avaliado=TRUE` com `alfabetizado=NULL`, e outra com `peso_aluno=0`.
Nenhuma linha é inserida na Silver; a execução reprovada existe apenas
como resultado do teste.

Após existir uma Gold publicada em homologação:

1. Antes do teste negativo, registrar a Gold atual com:

   ```powershell
   python -m alfab foto-gold --momento antes
   ```

2. Executar o Workflow do **projeto de homologação** com o argumento:

   ```json
   {"fault_injection":"avaliado_incompleto"}
   ```

3. Registrar `run_id` da execução esperada como `FAILED`, com código 3 do dbt.
   Conferir que `dbt.gold` e `publish.gold` **não rodaram**.
4. Capturar o estado da Gold após a falha:

   ```powershell
   python -m alfab foto-gold --momento depois --run-id <RUN_ID_NEGATIVO>
   ```

O último comando somente cria `evidencias/qualidade/demo_adr008_gold_depois.json`
se `ops.dq_results` comprovar a falha e os metadados da Gold forem **idênticos**
aos de `demo_adr008_gold_antes.json`. Se houver diferença, o comando bloqueia.
Esses dois arquivos são **novos**; não sobrescrevem a prova histórica
`demo_falha_gold_antes/depois.json` da demonstração `duplicate_keys`.

## 4. Publicação principal (somente após aceite e autorização)

O responsável GCP deve revisar `make deploy`/Terraform e o estado dos
recursos **antes** de qualquer implantação. O merge no GitHub e os checks CI
não atualizam tabelas BigQuery automaticamente.

Com a nova imagem/revisão aprovada, executar o Workflow normal,
registrar `run_id` e identificação do workflow, e repetir:

```powershell
python -m alfab validar-adrs --run-id <RUN_ID_PUBLICADO>
```

A atualização dos arquivos locais abaixo usa credenciais **de leitura** ao
projeto publicado e só deve ser feita após essa validação:

```powershell
python -m alfab profile --sql analises/02_estrutura_camadas.sql --saida evidencias/estrutura --aceite-run-id <RUN_ID_PUBLICADO>
python -m alfab evidencias --aceite-run-id <RUN_ID_PUBLICADO>
python -m alfab dashboard --aceite-run-id <RUN_ID_PUBLICADO>
```

O parâmetro `--aceite-run-id` impede atualizar evidências se a Gold ainda for a
versão anterior, ou se não houver provas de aprovação do mesmo `run_id`.
Esses scripts **consultam o GCP** e escrevem **somente nos arquivos locais**;
não simulam datas, contagens ou status.

## 5. Export de Fase 3: nova versão, sem sobrescrita

O export anterior `2026-10-01` contém o schema antigo e permanece arquivado,
**não apto para treino** após ADR-009. O novo export verifica o schema,
`published_run_id` e existência prévia de snapshot e objetos GCS. Não usa
`CREATE SNAPSHOT ... IF NOT EXISTS` e não reutiliza prefixo já ocupado.

O responsável GCP executa o job já atualizado, com argumentos de execução
pontuais (sem alterar a configuração permanente do Job):

```powershell
gcloud run jobs execute alfab-export-ml --project <PROJETO_GCP> --region <REGIAO> --args=export-ml,--versao,2026-11-02-21d8d75,--aceite-run-id,<RUN_ID_PUBLICADO> --wait
```

Ou em um shell Bash configurado com Make e variáveis do projeto:

```bash
make export-ml-adr ACEITE_RUN_ID=<RUN_ID_PUBLICADO> ML_VERSION=2026-11-02-21d8d75
```

Trocar a data/sufixo de versão se outra já existir. Não executar o export antes
da publicação e da validação da nova Gold.

## 6. Evidências que serão alteradas após nova execução real

| Arquivo | Origem real / verificação |
|---|---|
| `evidencias/estrutura/04_colunas_gold.csv` | `gold.INFORMATION_SCHEMA.COLUMNS`; sem feature vazada; posições recalculadas pelo BQ |
| `evidencias/estrutura/01_tabelas_por_camada.csv` | `__TABLES__` com tamanho e modificação efetivos |
| `evidencias/estrutura/07_grao_das_tabelas_gold.csv` | Contagens e chaves distintas após nova Gold |
| `evidencias/execucao.md` | `ops.pipeline_runs`, `ops.dq_results`, schema publicado; por teste e por execução |
| `evidencias/dashboard/dados.json` e `index.html` | Consulta real à Gold publicada, sem copia manual |
| `evidencias/qualidade/demo_adr008_gold_{antes,depois}.json` | Foto real antes/depois do Workflow NEGATIVO em homologação |
| `evidencias/batch/` e `evidencias/streaming/` | Capturas do Cloud Console/jobs, IDs e horários, após execução real |
| Snapshot BQ + GCS Fase 3 | Export real de uma versão NOVA da Gold ML validada |

Não modificar `evidencias/profiling/*`, FinOps e estado Terraform apenas para
alinhar números: preservá-los como histórico, salvo se suas fontes forem de
fato reexecutadas e medidas.

## 7. Aceite e PR final

Antes do commit de evidências, conferir:

- `run_id` positivo aparece como `SUCCEEDED` no Workflow e na tabela `ops.pipeline_runs`;
- os dois testes singulares aparecem `pass` em `ops.dq_results`;
- a execução negativa do ADR-008 aparece `FAILED` com `assert_avaliados_completos` em `fail`,
  `dbt.gold` e `publish.gold` ausentes; Gold antes/depois igual;
- feature vazada não existe na Gold real e no novo snapshot; `meta_vs_resultado` intacta;
- os números de estrutura/dashboard/execução vieram de consultas reais;
- prints batch e streaming capturados; IDs, UTC e projeto identificados;
- nenhuma credencial, `.env`, `.tfstate`, snapshot antigo sobrescrito ou segredo novo entrou no Git;
- rodar novamente os testes e abrir PR para integrar as novas evidências.

**Não afirmar "validado GCP" na documentação antes de concluir essa lista.**
