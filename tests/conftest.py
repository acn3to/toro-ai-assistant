"""
Global settings and fixtures for tests.
"""

import json
import os
from typing import Any
from unittest.mock import MagicMock

import boto3
from boto3.resources.base import ServiceResource
from boto3.session import Session
from moto import mock_aws
import pytest

from lib.adapters.bedrock_client import BedrockClient
from lib.adapters.dynamodb_client import DynamoDBClient
from lib.core.constants import STATUS_COMPLETED, STATUS_PENDING

TEST_TABLE_NAME = "test-questions-table"
TEST_PROCESS_TOPIC_NAME = "test-process-topic"
TEST_NOTIFY_TOPIC_NAME = "test-notify-topic"
TEST_REGION = "us-east-2"

DYNAMODB_TABLE_CONFIG = {
    "KeySchema": [
        {"AttributeName": "PK", "KeyType": "HASH"},
        {"AttributeName": "SK", "KeyType": "RANGE"},
    ],
    "AttributeDefinitions": [
        {"AttributeName": "PK", "AttributeType": "S"},
        {"AttributeName": "SK", "AttributeType": "S"},
    ],
    "BillingMode": "PAY_PER_REQUEST",
}


class MockLambdaContext:
    """Mock for the Lambda context object passed to functions."""

    function_name = "test-function"
    memory_limit_in_mb = 128
    invoked_function_arn = "arn:aws:lambda:us-east-2:123456789012:function:test-function"
    aws_request_id = "00000000-0000-0000-0000-000000000000"


@pytest.fixture(scope="function")
def lambda_context() -> MockLambdaContext:
    """Returns a mocked Lambda context object."""
    return MockLambdaContext()


@pytest.fixture(scope="function")
def aws_credentials() -> None:
    """Sets up fake AWS credentials for testing."""
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


@pytest.fixture(scope="function")
def mock_dynamodb_table() -> MagicMock:
    """Returns a mock DynamoDB table."""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}
    return mock_table


@pytest.fixture(scope="function")
def mock_sns_topic() -> MagicMock:
    """Returns a mock SNS topic."""
    return MagicMock()


@pytest.fixture(scope="function")
def setup_env_vars() -> None:
    """Sets environment variables for tests."""
    os.environ["TABLE_NAME"] = TEST_TABLE_NAME
    os.environ["PROCESS_TOPIC"] = TEST_PROCESS_TOPIC_NAME
    os.environ["NOTIFY_TOPIC"] = TEST_NOTIFY_TOPIC_NAME

    yield

    os.environ.pop("TABLE_NAME", None)
    os.environ.pop("PROCESS_TOPIC", None)
    os.environ.pop("NOTIFY_TOPIC", None)


def create_dynamodb_table(dynamodb: ServiceResource, table_name: str) -> None:
    """
    Helper function to create a DynamoDB table with test structure.

    Args:
        dynamodb: AWS DynamoDB resource
        table_name: Name of the table to create
    """
    config = DYNAMODB_TABLE_CONFIG.copy()
    config["TableName"] = table_name
    dynamodb.create_table(**config)


@pytest.fixture(scope="function")
def aws_session(aws_credentials) -> Session:
    """
    Fixture that provides an AWS session configured for testing.

    Depends on:
        aws_credentials: Fixture that sets up test AWS credentials

    Returns:
        Configured boto3.session.Session object
    """
    with mock_aws():
        session = boto3.Session(region_name=TEST_REGION)
        yield session


@pytest.fixture(scope="function")
def moto_dynamodb(aws_session: Session) -> ServiceResource:
    """
    Fixture that provides a mocked DynamoDB resource using Moto.

    Creates a table with the project's standard structure and returns it.
    The table is automatically deleted when the test ends.

    Depends on:
        aws_session: Configured AWS session

    Returns:
        Mocked DynamoDB resource with a pre-created table
    """
    dynamodb = aws_session.resource("dynamodb")
    create_dynamodb_table(dynamodb, "toro-ai-assistant-questions")
    return dynamodb


@pytest.fixture(scope="function")
def db_client_mock() -> MagicMock:
    """
    Fixture that provides a mock DynamoDBClient for unit tests.

    This mock simulates basic operations like save_question, get_question, etc.

    Returns:
        Mocked DynamoDBClient with pre-configured methods
    """
    mock = MagicMock(spec=DynamoDBClient)
    mock.save_question.return_value = {
        "user_id": "test123",
        "question_id": "mock-id-123",
        "status": STATUS_PENDING,
    }
    return mock


@pytest.fixture(scope="function")
def db_client_moto(moto_dynamodb: ServiceResource) -> DynamoDBClient:
    """
    Fixture that provides a real DynamoDBClient using a mocked DynamoDB.

    Useful for integration tests that need to verify actual class behavior.

    Depends on:
        moto_dynamodb: Mocked DynamoDB resource

    Returns:
        DynamoDBClient instance using mocked DynamoDB
    """
    return DynamoDBClient(dynamodb_resource=moto_dynamodb)


@pytest.fixture(scope="function")
def mock_question_data() -> dict[str, Any]:
    """
    Fixture that provides sample question data for testing.

    Returns:
        Dictionary with sample question data
    """
    return {
        "user_id": "test123",
        "question_id": "abc123",
        "question": "O que é CDB?",
        "status": STATUS_COMPLETED,
        "answer": "CDB is an investment...",
        "created_at": "2023-01-01T12:00:00",
        "updated_at": "2023-01-01T12:30:00",
    }


@pytest.fixture(scope="function")
def mock_error_dynamodb_client() -> MagicMock:
    """
    Fixture that provides a DynamoDBClient mock that raises exceptions.

    Returns:
        Mocked DynamoDBClient configured to raise exceptions
    """
    mock = MagicMock(spec=DynamoDBClient)
    mock.save_question.side_effect = Exception("Simulated error")
    return mock


@pytest.fixture(scope="function")
def standard_event() -> dict[str, Any]:
    """
    Fixture that provides a standard event for tests.

    Returns:
        Simulated event with serialized JSON body
    """
    return {"body": json.dumps({"user_id": "test123", "question": "O que é CDB?"})}


@pytest.fixture(scope="function")
def direct_json_event() -> dict[str, Any]:
    """
    Fixture that provides an event with body as a direct JSON (not string).

    Returns:
        Simulated event with Python object as body
    """
    return {"body": {"user_id": "test123", "question": "O que é CDB?"}}


@pytest.fixture(scope="function")
def mock_bedrock_response() -> dict[str, Any]:
    """
    Fixture that provides a simulated AWS Bedrock response.

    Returns:
        Dictionary simulating Bedrock response
    """
    return {
        "answer": "This is a response generated by the simulated model.",
        "sources": [
            {
                "source_id": "doc1",
                "source_type": "document",
                "reference": "Reference Document 1",
                "content": "Content of document 1",
            }
        ],
        "inference_profile_id": "us.amazon.nova-pro-v1:0",
    }


@pytest.fixture(scope="function")
def mock_bedrock_client(mock_bedrock_response: dict[str, Any]) -> MagicMock:
    """
    Fixture that provides a mocked BedrockClient for tests.

    This mock simulates the main retrieve_and_generate operation
    to return model-generated answers.

    Depends on:
        mock_bedrock_response: Simulated Bedrock response

    Returns:
        Mocked Bedrock client with pre-configured methods
    """
    mock = MagicMock(spec=BedrockClient)
    mock.retrieve_and_generate.return_value = mock_bedrock_response
    return mock


@pytest.fixture(scope="function")
def setup_bedrock_error_client() -> MagicMock:
    """
    Fixture that provides a BedrockClient mock that raises exceptions.

    Returns:
        Mocked BedrockClient configured to raise exceptions
    """
    mock = MagicMock(spec=BedrockClient)
    mock.retrieve_and_generate.side_effect = Exception("Bedrock model error")
    return mock


@pytest.fixture(scope="function")
def setup_minimal_bedrock_client() -> MagicMock:
    """
    Fixture that provides a simplified BedrockClient mock.

    Returns:
        Mocked BedrockClient with a minimal response
    """
    mock = MagicMock(spec=BedrockClient)
    mock.retrieve_and_generate.return_value = {"answer": "Short answer"}
    return mock


@pytest.fixture(scope="function")
def sns_payload() -> dict[str, Any]:
    """
    Fixture that provides payload for an SNS event.

    Returns:
        Dictionary with data for an SNS message
    """
    return {"user_id": "test123", "question_id": "abc123"}


@pytest.fixture(scope="function")
def sns_event(sns_payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """
    Fixture that provides a simulated SNS event message.

    Depends on:
        sns_payload: Payload for the SNS message

    Returns:
        Simulated SNS event for Lambda testing
    """
    return {
        "Records": [
            {
                "EventSource": "aws:sns",
                "Sns": {"Message": json.dumps(sns_payload)},
            }
        ]
    }
