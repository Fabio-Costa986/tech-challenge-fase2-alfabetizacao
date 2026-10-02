# Atalhos. Todo identificador vem do .env (copie de .env.example). Sem make? Os comandos
# equivalentes estão no README, seção "Como executar".
SHELL := bash
-include .env
export

PY      ?= python
TAG     ?= $(shell git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)
IMAGE   := $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/alfab/pipeline:$(TAG)
TF      := terraform -chdir=infra
TFVARS  := -var project_id=$(GCP_PROJECT_ID) -var region=$(GCP_REGION) -var bq_location=$(BQ_LOCATION) \
           -var bronze_bucket=$(BRONZE_BUCKET) -var alert_email=$(ALERT_EMAIL)

.PHONY: help setup test lint infra-init infra-plan infra build deploy profile run-batch run-batch-local \
        demo-falha stream microbatch export-ml finops evidencias

help:
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  %-18s %s\n", $$1, $$2}'

setup: ## cria venv e instala dependências fixadas
	$(PY) -m venv .venv && .venv/bin/pip install -e ".[dev]" || .venv/Scripts/pip install -e ".[dev]"

test: ## testes unitários (sem nuvem)
	$(PY) -m pytest -q

lint: ## ruff + validação do projeto dbt e do terraform
	$(PY) -m ruff check src tests
	cd dbt && dbt parse --profiles-dir .
	$(TF) fmt -check -recursive

infra-init: ## terraform init
	$(TF) init

infra-plan: ## terraform plan (diff revisável)
	$(TF) plan $(TFVARS)

infra: ## provisiona tudo (fase 1: imagem placeholder)
	$(TF) apply $(TFVARS)

build: ## build da imagem no Cloud Build e push no Artifact Registry
	gcloud builds submit --project $(GCP_PROJECT_ID) --region $(GCP_REGION) --tag $(IMAGE) .

deploy: build ## build + atualiza jobs e serviço com a nova imagem
	$(TF) apply $(TFVARS) -var image=$(IMAGE)

profile: ## profiling da fonte -> evidencias/profiling/
	$(PY) -m alfab profile

run-batch: ## executa o workflow batch na nuvem e aguarda
	gcloud workflows run alfab-pipeline-batch --project $(GCP_PROJECT_ID) --location $(GCP_REGION) --data='{}'

run-batch-local: ## mesmo pipeline, a partir da máquina local (ADC)
	$(PY) -m alfab pipeline

demo-falha: ## DEMONSTRA o pipeline falhando: chaves duplicadas na Silver -> Gold não é publicada
	-gcloud workflows run alfab-pipeline-batch --project $(GCP_PROJECT_ID) --location $(GCP_REGION) \
	  --data='{"fault_injection": "duplicate_keys"}'
	@echo ">> Esperado: execução FAILED, linha FAIL em ops.dq_results, e-mail de alerta, gold intocada."

stream: ## publica eventos simulados (job na nuvem)
	gcloud run jobs execute alfab-simulator --project $(GCP_PROJECT_ID) --region $(GCP_REGION) --wait

microbatch: ## força um micro-lote agora
	gcloud run jobs execute alfab-microbatch --project $(GCP_PROJECT_ID) --region $(GCP_REGION) --wait

export-ml: ## snapshot da base de features para a Fase 3
	gcloud run jobs execute alfab-export-ml --project $(GCP_PROJECT_ID) --region $(GCP_REGION) --wait

finops: ## mede custos e gera evidencias/finops/custos_medidos.md
	$(PY) -m alfab finops

evidencias: ## exporta contagens e últimas execuções para evidencias/
	$(PY) -m alfab evidencias
