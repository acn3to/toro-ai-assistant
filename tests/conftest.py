"""
Configurações e fixtures globais para testes.
Este arquivo é automaticamente descoberto pelo pytest.
"""

import os
from unittest.mock import MagicMock

import pytest

TEST_TABLE_NAME = "test-questions-table"
TEST_TOPIC_NAME = "test-process-topic"
TEST_NOTIFY_TOPIC_NAME = "test-notify-topic"
TEST_REGION = "us-east-2"


class MockLambdaContext:
    """Mock para o objeto context passado para funções Lambda."""

    function_name = "test-function"
    memory_limit_in_mb = 128
    invoked_function_arn = "arn:aws:lambda:us-east-2:123456789012:function:test-function"
    aws_request_id = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
def lambda_context():
    """Retorna um objeto de contexto Lambda simulado."""
    return MockLambdaContext()


@pytest.fixture
def aws_credentials():
    """Configura credenciais AWS falsas para os testes."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = TEST_REGION

    yield

    os.environ.pop("AWS_ACCESS_KEY_ID", None)
    os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
    os.environ.pop("AWS_SECURITY_TOKEN", None)
    os.environ.pop("AWS_SESSION_TOKEN", None)
    os.environ.pop("AWS_DEFAULT_REGION", None)


@pytest.fixture
def mock_dynamodb_table():
    """Retorna um mock para uma tabela DynamoDB."""
    mock_table = MagicMock()
    yield mock_table


@pytest.fixture
def mock_sns_topic():
    """Retorna um mock para um tópico SNS."""
    mock_topic = MagicMock()
    yield mock_topic


@pytest.fixture
def setup_env_vars():
    """Configura variáveis de ambiente para os testes."""
    os.environ["TABLE_NAME"] = TEST_TABLE_NAME
    os.environ["PROCESS_TOPIC"] = TEST_TOPIC_NAME
    os.environ["NOTIFY_TOPIC"] = TEST_NOTIFY_TOPIC_NAME

    yield

    os.environ.pop("TABLE_NAME", None)
    os.environ.pop("PROCESS_TOPIC", None)
    os.environ.pop("NOTIFY_TOPIC", None)
