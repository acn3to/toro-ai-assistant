# Toro AI Assistant

![Versão](https://img.shields.io/badge/versão-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11-green)
![AWS SAM](https://img.shields.io/badge/aws--sam-latest-orange)
![Poetry](https://img.shields.io/badge/poetry-1.8.5-purple)

Assistente virtual serverless baseado em IA que responde perguntas sobre investimentos e serviços da Toro Investimentos, com histórico persistente e notificações em tempo real.

## 🚀 Visão Geral

O Toro AI Assistant permite que usuários façam perguntas sobre investimentos e recebam respostas contextualizadas, utilizando dados específicos da Toro Investimentos. O sistema utiliza arquitetura serverless na AWS e tecnologia RAG (Retrieval Augmented Generation) para fornecer respostas precisas e relevantes.

### Principais Recursos

- ✅ Envio de perguntas via API REST
- ✅ Processamento assíncrono com SNS
- ✅ Respostas contextualizadas via RAG
- ✅ Persistência de perguntas/respostas no DynamoDB
- ✅ Notificações de novas respostas
- ✅ Interface frontend
- ✅ Monitoramento e alertas com CloudWatch

## 🏗️ Arquitetura

O sistema utiliza arquitetura event-driven serverless na AWS:

```
API Gateway → Lambda Ingest → SNS → Lambda Process → SNS → Lambda Notify
                    ↓                    ↓  ↑               ↓
                DynamoDB               RAG + IA        Notificações
```

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.11, AWS Lambda, SNS, DynamoDB
- **Frontend**: HTML, JavaScript, CSS
- **IaC**: AWS SAM
- **IA/RAG**: AWS Bedrock
- **Gerenciamento de Dependências**: Poetry, pip (Lambdas)
- **CI/CD**: GitHub Actions
- **Monitoramento**: CloudWatch Alarms
- **Linting/Formatação**: Ruff, pre-commit

## 🔧 Instalação e Setup

### Pré-requisitos

- AWS CLI configurado com credenciais apropriadas
- Python >= 3.11
- AWS SAM CLI
- Poetry >= 1.0.0

### Instruções de Setup

1. **Clone o repositório**

```bash
git clone https://github.com/acn3to/toro-ai-assistant.git
cd toro-ai-assistant
```

2. **Instale as dependências**

```bash
# Instalar Poetry (se ainda não estiver instalado)
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependências do projeto usando Poetry
poetry install
```

3. **Configure as variáveis de ambiente**

Crie um arquivo `.env` na raiz do projeto:

```
RAG_DATA_PATH=./data/knowledge_base.json
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
AWS_REGION=us-east-2
TABLE_NAME=toro-ai-assistant-questions
PROCESS_TOPIC=toro-ai-assistant-process-topic
NOTIFY_TOPIC=toro-ai-assistant-notify-topic
```

4. **Execute localmente para desenvolvimento**

```bash
# Construir o projeto
make build

# Iniciar a API localmente
make start-api

# Testar a função de ingestão
make invoke-ingest
```

5. **Fazer deploy na AWS**

```bash
# Fazer deploy (primeira vez)
sam deploy --guided

# Para deploys subsequentes
make deploy
```

## 📋 Usando o Makefile

O projeto inclui um Makefile para simplificar tarefas comuns:

| Comando | Descrição |
|---------|-----------|
| `make help` | Exibe a lista de comandos disponíveis |
| `make build` | Constrói a aplicação SAM |
| `make clean` | Remove arquivos temporários e diretórios de build |
| `make deploy` | Faz o deploy da aplicação na AWS |
| `make validate` | Valida o template SAM |
| `make start-api` | Inicia a API localmente para testes |
| `make start-lambda` | Inicia o Lambda localmente para testes |
| `make invoke-ingest` | Invoca a função de ingestão localmente |
| `make lint` | Verifica lint em todos os arquivos Python |
| `make format` | Formata todos os arquivos Python |
| `make test` | Executa todos os testes (unitários e integração) |
| `make test-ingest` | Executa apenas os testes da função de ingestão |
| `make test-lib` | Executa apenas os testes da biblioteca compartilhada |
| `make coverage` | Executa testes e gera relatório de cobertura |
| `make list-resources` | Lista os recursos criados pelo CloudFormation |
| `make check-deployment` | Verifica o status do deployment mais recente |
| `make delete-stack` | Remove um stack do CloudFormation |

## 📈 Como Usar

### API Endpoints

- **POST /questions**

  Envia uma nova pergunta:

  ```json
  {
    "user_id": "user123",
    "question": "O que é um CDB?"
  }
  ```

  Resposta:

  ```json
  {
    "success": true,
    "data": {
      "user_id": "user123",
      "question_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "pending"
    }
  }
  ```

### Exemplo de uso com curl

```bash
curl -X POST https://[seu-api-id].execute-api.[sua-regiao].amazonaws.com/Prod/questions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "question": "O que é CDB?"}'
```

## 📝 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
