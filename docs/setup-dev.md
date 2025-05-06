# Development Environment Setup

This guide will help you set up your local development environment for the Toro AI Assistant project.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.11** or higher
- **AWS CLI** version 2 or higher
- **AWS SAM CLI** for serverless application deployment
- **Make** for running automation scripts
- **Poetry** (optional but recommended for dependency management)

## Installation Steps

### 1. Python and Virtualenv

```bash
# Check Python version
python --version  # Should be 3.11 or higher

# Install virtualenv if not already installed
pip install virtualenv

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/macOS
source venv/bin/activate
# On Windows
.\venv\Scripts\activate
```

### 2. AWS CLI

```bash
# Install AWS CLI (example for Linux)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
```

### 3. AWS SAM CLI

```bash
# Install AWS SAM CLI (example for Linux)
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install

# Verify installation
sam --version
```

### 4. Make

Make is typically pre-installed on most Linux distributions and macOS. For Windows, you can install it via Chocolatey or Scoop.

```bash
# Verify installation
make --version
```

### 5. Ruff (Linter and Formatter)

```bash
# Install ruff
pip install ruff

# Verify installation
ruff --version
```

### 6. Project Dependencies

```bash
# Clone the repository (if not already done)
git clone https://github.com/acn3to/toro-ai-assistant.git
cd toro-ai-assistant

# Install dependencies using Poetry (recommended)
pip install poetry
poetry install

# Alternatively, install dependencies directly
pip install -r requirements.txt
```

## AWS Configuration

### 1. Create an IAM User

1. Go to the [AWS Management Console](https://console.aws.amazon.com/)
2. Navigate to IAM > Users > Create User
3. Enter a username (e.g., `toro-ai-assistant-dev`)
4. Select "Programmatic access" for access type
5. Attach policies (see below for minimum required permissions)

### 2. Required IAM Permissions

For development purposes, you might use the `AdministratorAccess` policy, but for production, you should follow the principle of least privilege and create a custom policy with only the necessary permissions:

- `AmazonDynamoDBFullAccess` - For DynamoDB operations
- `AmazonSNSFullAccess` - For SNS topics
- `AWSLambda_FullAccess` - For Lambda functions
- `AmazonAPIGatewayAdministrator` - For API Gateway
- `AmazonBedrockFullAccess` - For AWS Bedrock access

### 3. Configure AWS CLI

```bash
# Configure AWS CLI with your credentials
aws configure

# Enter the following when prompted:
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]
# Default region name: us-east-2 (or your preferred region)
# Default output format: json
```

Alternatively, you can edit the `~/.aws/credentials` and `~/.aws/config` files directly:

```ini
# ~/.aws/credentials
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

# ~/.aws/config
[default]
region = us-east-2
output = json
```

### 4. Create an AWS Profile (Optional)

If you work with multiple AWS accounts, create a named profile:

```bash
aws configure --profile toro-ai-assistant
```

Then use this profile in your commands:

```bash
aws s3 ls --profile toro-ai-assistant
```

## Project Configuration

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install the pre-commit hooks
pre-commit install
```

## Verifying Your Setup

Run the following commands to verify your setup:

```bash
# Validate the SAM template
make validate

# Run linting
make lint

# Run tests
make test
```

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Found**
   - Ensure your credentials are correctly set in `~/.aws/credentials`
   - Check if the region is configured in `~/.aws/config`

2. **Python Version Mismatch**
   - The project requires Python 3.11. Verify with `python --version`

3. **Dependency Issues**
   - Run `poetry update` to update dependencies
   - Check for conflicting versions in `poetry.lock`

4. **AWS Bedrock Access**
   - Ensure your AWS account has AWS Bedrock enabled
   - Request access to the required models in the AWS Bedrock console

For more detailed information on deployment, see [Deployment Guide](deployment.md).

---

<div align="center">
  <a href="../README.md">
    <img src="https://img.shields.io/badge/⬅️_Back_to_Home-0A66C2?style=for-the-badge" alt="Back to Home"/>
  </a>
</div>
