        # Verifica se a atualização inclui o status e o erro
# Makefile para o Toro AI Assistente
.PHONY: help build clean deploy invoke start-api validate lint format test verify-alarms check-deployment prepare-data install update list-resources delete-stack create-bucket unit-test test-ingest test-lib coverage start-lambda

# Variáveis
STACK_NAME = toro-ai-assistant
EVENTS_DIR = ./events
S3_BUCKET = $(STACK_NAME)-artifacts
STAGE = dev
TEMPLATE = infra/template.yaml

# Cores para saída
RESET = \033[0m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
RED = \033[31m

help: ## Exibe ajuda com todos os comandos
	@echo "$(BLUE)Toro AI Assistant - Comandos disponíveis$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

build: ## Constrói a aplicação SAM
	@echo "$(GREEN)Construindo aplicação...$(RESET)"
	sam build --use-container -t $(TEMPLATE)

clean: ## Remove arquivos temporários e diretórios de build
	@echo "$(GREEN)Limpando diretório...$(RESET)"
	rm -rf .aws-sam
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

deploy: validate build create-bucket ## Faz o deploy da aplicação na AWS
	@echo "$(GREEN)Realizando deploy...$(RESET)"
	sam deploy --stack-name $(STACK_NAME)-$(STAGE) \
		--s3-bucket $(S3_BUCKET) \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides Stage=$(STAGE) \
		--no-fail-on-empty-changeset \
		-t $(TEMPLATE)

validate: ## Valida o template SAM
	@echo "$(GREEN)Validando template...$(RESET)"
	sam validate -t $(TEMPLATE)

start-api: build ## Inicia a API localmente
	@echo "$(GREEN)Iniciando API localmente...$(RESET)"
	sam local start-api -t $(TEMPLATE)

invoke-ingest: build ## Invoca a função de ingestão localmente
	@echo "$(GREEN)Invocando função de ingestão...$(RESET)"
	sam local invoke IngestFunction -e $(EVENTS_DIR)/api-event.json -t $(TEMPLATE)

invoke-process: build ## Invoca a função de processamento localmente
	@echo "$(GREEN)Invocando função de processamento...$(RESET)"
	sam local invoke ProcessFunction -e $(EVENTS_DIR)/sns-event.json -t $(TEMPLATE)

invoke-notify: build ## Invoca a função de notificação localmente
	@echo "$(GREEN)Invocando função de notificação...$(RESET)"
	sam local invoke NotifyFunction -e $(EVENTS_DIR)/sns-event.json -t $(TEMPLATE)

lint: ## Verifica lint em todos os arquivos Python
	@echo "$(GREEN)Executando lint...$(RESET)"
	poetry run ruff check src/ lib/ tests/

format: ## Formata todos os arquivos Python
	@echo "$(GREEN)Formatando código...$(RESET)"
	poetry run ruff format src/ lib/ tests/

test: ## Executa todos os testes (unitários e integração)
	@echo "$(GREEN)Executando testes...$(RESET)"
	poetry run pytest

unit-test: ## Executa apenas os testes unitários
	@echo "$(GREEN)Executando testes unitários...$(RESET)"
	poetry run pytest tests/questions/

# Alias para testes específicos
test-ingest: ## Executa apenas os testes da função de ingestão
	@echo "$(GREEN)Executando testes da função de ingestão...$(RESET)"
	poetry run pytest tests/questions/ingest/

test-lib: ## Executa apenas os testes da biblioteca compartilhada
	@echo "$(GREEN)Executando testes da biblioteca...$(RESET)"
	poetry run pytest tests/lib/

coverage: ## Executa os testes e gera relatório de cobertura de código
	@echo "$(GREEN)Executando testes com análise de cobertura...$(RESET)"
	poetry run pytest --cov=src --cov=lib --cov-report=term-missing

prepare-data: ## Prepara os dados de conhecimento para o RAG
	@echo "$(GREEN)Preparando dados de conhecimento...$(RESET)"
	mkdir -p data
	poetry run python scripts/prepare_knowledge_base.py

verify-alarms: ## Verifica a configuração dos alarmes CloudWatch
	@echo "$(GREEN)Verificando configuração de alarmes...$(RESET)"
	aws cloudwatch describe-alarms --alarm-name-prefix ToroAssistant

check-deployment: ## Verifica o status do deployment mais recente
	@echo "$(GREEN)Verificando status do deployment...$(RESET)"
	aws cloudformation describe-stacks --stack-name $(STACK_NAME) \
		--query "Stacks[0].StackStatus" --output text

list-resources: ## Lista os recursos criados pelo CloudFormation
	@echo "$(GREEN)Listando recursos criados...$(RESET)"
	aws cloudformation describe-stack-resources --stack-name $(STACK_NAME)

delete-stack: ## Remove um stack específico do CloudFormation (ex: make delete-stack STACK=nome-do-stack)
	@echo "$(RED)ATENÇÃO: Esta operação irá excluir todos os recursos do stack $(RESET)"
	@echo "$(RED)Stack a ser removido: $(STACK)$(RESET)"
	@read -p "Tem certeza que deseja continuar? (y/n) " confirm; \
	if [ "$$confirm" = "y" ]; then \
		aws cloudformation delete-stack --stack-name $(STACK); \
		echo "$(GREEN)Solicitação de remoção do stack $(STACK) enviada. Verificando status...$(RESET)"; \
		aws cloudformation wait stack-delete-complete --stack-name $(STACK) || echo "$(RED)Erro ao aguardar exclusão do stack. Verifique no console da AWS.$(RESET)"; \
	else \
		echo "$(YELLOW)Operação cancelada.$(RESET)"; \
	fi

create-bucket: ## Cria o bucket S3 necessário para armazenar artefatos de deploy
	@echo "$(GREEN)Criando bucket S3 para artefatos...$(RESET)"
	@aws s3 ls s3://$(S3_BUCKET) >/dev/null 2>&1 && echo "$(YELLOW)Bucket $(S3_BUCKET) já existe.$(RESET)" || \
	aws s3 mb s3://$(S3_BUCKET) --region $(shell aws configure get region) && \
	echo "$(GREEN)Bucket $(S3_BUCKET) criado com sucesso.$(RESET)"

install: ## Instala dependências com Poetry (ambiente de desenvolvimento)
	@echo "$(GREEN)Instalando dependências com Poetry...$(RESET)"
	poetry install

update: ## Atualiza dependências com Poetry (ambiente de desenvolvimento)
	@echo "$(GREEN)Atualizando dependências com Poetry...$(RESET)"
	poetry update

start-lambda: build ## Inicia o Lambda localmente para testes
	@echo "$(GREEN)Iniciando Lambda localmente...$(RESET)"
	sam local start-lambda -t $(TEMPLATE)
