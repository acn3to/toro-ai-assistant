.PHONY: help build clean deploy invoke start-api validate lint format test install update list-resources delete-stack create-bucket upload-documents prepare-layer build-with-deps print-account print-kb

# Variables
STAGE = dev
REGION = us-east-2
STACK_NAME = toro-ai-assistant
AWS_PROFILE = default
S3_BUCKET = $(STACK_NAME)-artifacts
KB_BUCKET = $(STACK_NAME)-kb-documents
TEMPLATE = infra/serverless-template.yaml
AWS_REGION = $(shell aws configure get region)
ACCOUNT_ID := $(shell aws sts get-caller-identity --query "Account" --output text)
KNOWLEDGE_BASE_ID := $(shell aws bedrock-agent list-knowledge-bases --query "knowledgeBaseSummaries[0].knowledgeBaseId" --output text)

# Colors for output
RESET = \033[0m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
RED = \033[31m

print-account: ## Prints the AWS Account ID
	@echo "AWS Account ID: $(ACCOUNT_ID)"

print-kb: ## Prints the Knowledge Base ID
	@echo "Knowledge Base ID: $(KNOWLEDGE_BASE_ID)"

help: ## Displays help with all available commands
	@echo "$(BLUE)Toro AI Assistant - Available Commands$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

prepare-layer: ## Prepares the layer with the shared library
	@echo "$(GREEN)Preparing layer with shared library...$(RESET)"
	# Remove old layer and recreate directory
	rm -rf layer/python
	mkdir -p layer/python/lib/python3.11/site-packages

	# Copy shared code to the correct folder
	cp -r lib layer/python/

	# Create a temporary virtual environment to install dependencies
	python -m venv /tmp/toro-venv

	# Activate the virtual environment and install dependencies
	. /tmp/toro-venv/bin/activate && \
	for func in src/questions/*/requirements.txt; do \
		echo "Installing dependencies for $$func in the layer..."; \
		pip install -r $$func && \
		cp -r /tmp/toro-venv/lib/python3.11/site-packages/* layer/python/lib/python3.11/site-packages/; \
	done && \
	deactivate

	# Remove the temporary virtual environment
	rm -rf /tmp/toro-venv
	@echo "$(GREEN)Layer successfully prepared.$(RESET)"

build: prepare-layer ## Builds the SAM application
	@echo "$(GREEN)Building the application...$(RESET)"
	sam build --use-container -t $(TEMPLATE)

build-with-deps: prepare-layer ## Builds the SAM application with more details about dependencies
	@echo "$(GREEN)Building the application with dependency details...$(RESET)"
	sam build --use-container -t $(TEMPLATE) --debug

clean: ## Removes temporary files and build directories
	@echo "$(GREEN)Cleaning directory...$(RESET)"
	rm -rf .aws-sam
	rm -rf .pytest_cache
	rm -rf layer/python
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

deploy: validate build create-bucket ## Deploys the application to AWS
	@echo "$(GREEN)Setting up deployment parameters...$(RESET)"
	@echo "$(GREEN)Using AWS Account ID: $(ACCOUNT_ID)$(RESET)"
	@echo "$(GREEN)Using Knowledge Base ID: $(KNOWLEDGE_BASE_ID)$(RESET)"

	@if [ -z "$(KNOWLEDGE_BASE_ID)" ]; then \
		echo "$(YELLOW)No Knowledge Base found. Deploying without RAG capabilities.$(RESET)"; \
		sam deploy --stack-name $(STACK_NAME)-$(STAGE) \
			--s3-bucket $(S3_BUCKET) \
			--region $(REGION) \
			--capabilities CAPABILITY_IAM \
			--parameter-overrides Stage=$(STAGE) BedrockModel=us.amazon.nova-pro-v1:0 AwsAccountId=$(ACCOUNT_ID) \
			--no-fail-on-empty-changeset \
			-t $(TEMPLATE); \
	else \
		echo "$(GREEN)Deploying with Knowledge Base ID: $(KNOWLEDGE_BASE_ID)$(RESET)"; \
		sam deploy --stack-name $(STACK_NAME)-$(STAGE) \
			--s3-bucket $(S3_BUCKET) \
			--region $(REGION) \
			--capabilities CAPABILITY_IAM \
			--parameter-overrides Stage=$(STAGE) KnowledgeBaseId=$(KNOWLEDGE_BASE_ID) BedrockModel=us.amazon.nova-pro-v1:0 AwsAccountId=$(ACCOUNT_ID) \
			--no-fail-on-empty-changeset \
			-t $(TEMPLATE); \
	fi

validate: ## Validates the SAM template
	@echo "$(GREEN)Validating template...$(RESET)"
	sam validate -t $(TEMPLATE)

start-api: build ## Starts the API locally
	@echo "$(GREEN)Starting API locally...$(RESET)"
	sam local start-api -t $(TEMPLATE)

lint: ## Runs lint check on all Python files
	@echo "$(GREEN)Running lint...$(RESET)"
	poetry run ruff check src/ lib/ tests/

format: ## Formats all Python files
	@echo "$(GREEN)Formatting code...$(RESET)"
	poetry run ruff format src/ lib/ tests/

test: ## Runs all tests (unit and integration)
	@echo "$(GREEN)Running tests...$(RESET)"
	poetry run pytest

create-bucket: ## Creates the S3 bucket to store deployment artifacts
	@echo "$(GREEN)Creating S3 bucket for artifacts...$(RESET)"
	@aws s3 ls s3://$(S3_BUCKET) >/dev/null 2>&1 && echo "$(YELLOW)Bucket $(S3_BUCKET) already exists.$(RESET)" || \
	aws s3 mb s3://$(S3_BUCKET) --region $(AWS_REGION) && \
	echo "$(GREEN)Bucket $(S3_BUCKET) successfully created.$(RESET)"

create-kb-bucket: ## Creates the S3 bucket for Knowledge Base documents
	@echo "$(GREEN)Creating S3 bucket for Knowledge Base documents...$(RESET)"
	@aws s3 ls s3://$(KB_BUCKET) >/dev/null 2>&1 && echo "$(YELLOW)Bucket $(KB_BUCKET) already exists.$(RESET)" || \
	aws s3 mb s3://$(KB_BUCKET) --region $(AWS_REGION) && \
	echo "$(GREEN)Bucket $(KB_BUCKET) successfully created.$(RESET)"

upload-documents: create-kb-bucket ## Uploads documents to the S3 Knowledge Base bucket
	@echo "$(GREEN)Uploading documents to the S3 bucket...$(RESET)"
	@if [ -d "data/documents/" ]; then \
		aws s3 cp data/documents/ s3://$(KB_BUCKET)/documents/ --recursive; \
		echo "$(GREEN)Documents successfully uploaded.$(RESET)"; \
	else \
		echo "$(YELLOW)data/documents/ directory not found. Creating...$(RESET)"; \
		mkdir -p data/documents; \
		echo "$(YELLOW)Place your documents in data/documents/ and run again.$(RESET)"; \
	fi

install: ## Installs dependencies with Poetry (development environment)
	@echo "$(GREEN)Installing dependencies with Poetry...$(RESET)"
	poetry install

update: ## Updates dependencies with Poetry (development environment)
	@echo "$(GREEN)Updating dependencies with Poetry...$(RESET)"
	poetry update

list-resources: ## Lists the resources created by CloudFormation
	@echo "$(GREEN)Listing created resources...$(RESET)"
	aws cloudformation describe-stack-resources --stack-name $(STACK_NAME)-$(STAGE)

delete-stack: ## Removes a specific CloudFormation stack (e.g., make delete-stack STACK=stack-name)
	@echo "$(RED)WARNING: This operation will delete all resources of stack $(RESET)"
	@echo "$(RED)Stack to be removed: $(STACK)$(RESET)"
	@read -p "Are you sure you want to proceed? (y/n) " confirm; \
	if [ "$$confirm" = "y" ]; then \
		aws cloudformation delete-stack --stack-name $(STACK); \
		echo "$(GREEN)Delete stack request sent. Checking status...$(RESET)"; \
		aws cloudformation wait stack-delete-complete --stack-name $(STACK) || echo "$(RED)Error waiting for stack deletion. Check AWS console.$(RESET)"; \
	else \
		echo "$(YELLOW)Operation canceled.$(RESET)"; \
	fi

kb-instructions: ## Shows instructions for creating the Knowledge Base manually
	@echo "$(GREEN)=================================================$(RESET)"
	@echo "$(GREEN)  INSTRUCTIONS TO CREATE THE KNOWLEDGE BASE MANUALLY$(RESET)"
	@echo "$(GREEN)=================================================$(RESET)"
	@echo ""
	@echo "$(YELLOW)1. Go to the AWS Bedrock console:$(RESET)"
	@echo "   https://console.aws.amazon.com/bedrock/home"
	@echo ""
	@echo "$(YELLOW)2. In the sidebar menu, select 'Knowledge base'$(RESET)"
	@echo ""
	@echo "$(YELLOW)3. Click on 'Create knowledge base'$(RESET)"
	@echo ""
	@echo "$(YELLOW)4. Provide the details for the Knowledge Base:$(RESET)"
	@echo "   - Name: toro-ai-assistant-kb"
	@echo "   - Description: Knowledge Base for Toro AI Assistant"
	@echo "   - IAM role: Create a new role or use an existing one"
	@echo ""
	@echo "$(YELLOW)5. Configure the data source:$(RESET)"
	@echo "   - Data source name: investment-documents"
	@echo "   - S3 location: s3://$(KB_BUCKET)/documents/"
	@echo "   - Embedding model: Amazon Titan Embeddings - Text"
	@echo ""
	@echo "$(YELLOW)6. Configure the Vector Database:$(RESET)"
	@echo "   - Type: OpenSearch Serverless"
	@echo "   - Collection: Create new or use existing"
	@echo "   - Index name: kb-index"
	@echo "   - Vector field: vector"
	@echo "   - Text field: text"
	@echo "   - Metadata field: metadata"
	@echo ""
	@echo "$(YELLOW)7. After creating the Knowledge Base, obtain the ID:$(RESET)"
	@echo "   - Note the Knowledge Base ID (format KB-XXXXXXXX)"
	@echo ""
	@echo "$(YELLOW)8. Deploy or update the application with the ID:$(RESET)"
	@echo "   make deploy"
	@echo ""
	@echo "$(GREEN)=================================================$(RESET)"
