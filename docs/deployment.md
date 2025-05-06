# Deployment Guide

This guide provides detailed instructions for deploying the Toro AI Assistant to AWS, both for development and production environments.

## Prerequisites

Before deploying, ensure you have:

- Completed the [Development Environment Setup](setup-dev.md)
- AWS CLI configured with appropriate credentials
- AWS SAM CLI installed
- Knowledge Base documents prepared in `data/documents/` (optional, for RAG capability)

## Deployment Process Overview

The deployment of Toro AI Assistant involves several steps:

1. Setting up Knowledge Base (if using RAG)
2. Building the application
3. Deploying infrastructure with AWS SAM
4. Testing the deployment

## Deployment Using Makefile

The project includes a comprehensive Makefile with commands to simplify deployment:

### 1. Knowledge Base Setup (Optional, for RAG)

```bash
# Create S3 bucket for knowledge base documents
make create-kb-bucket

# Upload documents to the S3 bucket
make upload-documents
```

If you don't have documents yet, place them in the `data/documents/` directory before running `upload-documents`.

### 2. Build the Application

```bash
# Clean any previous build artifacts
make clean

# Build the application
make build
```

This will build the application using Docker containers (via SAM), creating a `.aws-sam` directory with the build artifacts.

### 3. Deploy the Application

```bash
# Deploy to AWS
make deploy
```

During deployment, you will be prompted for:
- Stage name (default: dev)
- Knowledge Base ID (if you have one)
- Bedrock model ID (default: us.amazon.nova-pro-v1:0)

If you don't have a Knowledge Base yet, AWS SAM will prompt you to create one. You can follow these instructions:

```bash
# Show instructions for creating a Knowledge Base
make kb-instructions
```

### 4. Verify the Deployment

```bash
# List all resources created by CloudFormation
make list-resources

# Check the API endpoint URL
aws cloudformation describe-stacks --stack-name toro-ai-assistant-dev --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text
```

## Manual Deployment Process

If you need more control over the deployment process, you can use the SAM CLI directly:

### 1. Build the Application

```bash
# Build with SAM CLI
sam build --use-container -t infra/serverless-template.yaml
```

### 2. Deploy the Built Application

```bash
# Deploy with SAM CLI
sam deploy --stack-name toro-ai-assistant-dev \
  --s3-bucket your-deployment-bucket \
  --region us-east-2 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides Stage=dev KnowledgeBaseId=your-kb-id BedrockModel=us.amazon.nova-pro-v1:0 \
  --no-fail-on-empty-changeset
```

## Testing the Deployment

### 1. Test the API Endpoint

```bash
# Get the API endpoint URL
API_URL=$(aws cloudformation describe-stacks --stack-name toro-ai-assistant-dev --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)

# Send a test question
curl -X POST $API_URL/questions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "question": "What is a CDB?"}'
```

### 2. Check Logs

```bash
# Check logs for the Ingest Lambda
sam logs -n IngestFunction --stack-name toro-ai-assistant-dev --tail

# Check logs for the Process Lambda
sam logs -n ProcessFunction --stack-name toro-ai-assistant-dev --tail
```

## Deployment Environments

### Development Environment

```bash
# Deploy to dev environment
make deploy STAGE=dev
```

### Production Environment

```bash
# Deploy to production environment
make deploy STAGE=prod
```

For production, consider:
- Different IAM roles with stricter permissions
- CloudWatch Alarms for monitoring
- Higher concurrency limits for Lambda functions
- DynamoDB on-demand capacity mode

## Cleanup Resources

To remove all deployed resources:

```bash
# Delete the CloudFormation stack
make delete-stack STACK=toro-ai-assistant-dev
```

This will remove all AWS resources created for the application.

## Troubleshooting

### Common Deployment Issues

1. **SAM Build Fails**
   - Check Docker is running
   - Ensure you have permissions to use Docker
   - Check disk space for Docker images

2. **SAM Deploy Fails**
   - Verify AWS credentials have necessary permissions
   - Check CloudFormation service limits
   - Look for pre-existing resources with the same names

3. **Knowledge Base Creation Fails**
   - Ensure you have permissions for AWS Bedrock
   - Check if the model is enabled in your account
   - Verify the S3 bucket has the correct permissions

For more details on architecture, see [Architecture](architecture.md).

---

<div align="center">
  <a href="../README.md">
    <img src="https://img.shields.io/badge/⬅️_Back_to_Home-0A66C2?style=for-the-badge" alt="Back to Home"/>
  </a>
</div>
