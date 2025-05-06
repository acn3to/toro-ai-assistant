"""
Unit tests for the notification handler.
"""

import json
from unittest.mock import MagicMock

import pytest

from lib.models.aws import APIGatewayManagementClient, DynamoDBTable
from lib.models.question import QuestionStatus
import src.questions.notify.handler


@pytest.fixture
def standard_event():
    """Fixture for a standard SNS event."""
    return {
        "Records": [
            {
                "EventSource": "aws:sns",
                "Sns": {
                    "Message": json.dumps(
                        {
                            "user_id": "test123",
                            "question_id": "q-123456",
                            "status": QuestionStatus.COMPLETED,
                        }
                    )
                },
            }
        ]
    }


@pytest.fixture
def error_event():
    """Fixture for an SNS event with ERROR status."""
    return {
        "Records": [
            {
                "EventSource": "aws:sns",
                "Sns": {
                    "Message": json.dumps(
                        {
                            "user_id": "test123",
                            "question_id": "q-123456",
                            "status": QuestionStatus.ERROR,
                        }
                    )
                },
            }
        ]
    }


@pytest.fixture
def pending_event():
    """Fixture for an SNS event with PENDING status."""
    return {
        "Records": [
            {
                "EventSource": "aws:sns",
                "Sns": {
                    "Message": json.dumps(
                        {
                            "user_id": "test123",
                            "question_id": "q-123456",
                            "status": QuestionStatus.PENDING,
                        }
                    )
                },
            }
        ]
    }


@pytest.fixture
def db_client_mock():
    """Mock DynamoDB client."""
    mock = MagicMock()
    mock.get_question.return_value = {
        "user_id": "test123",
        "question_id": "q-123456",
        "question": "Como funciona a inflação?",
        "answer": "A inflação é o aumento generalizado dos preços...",
        "status": QuestionStatus.COMPLETED,
    }
    return mock


@pytest.fixture
def connections_table_mock():
    """Mock DynamoDB connections table."""
    mock = MagicMock(spec=DynamoDBTable)
    mock.get_item.return_value = {"Item": {"connection_id": "mock-connection-id"}}
    return mock


@pytest.fixture
def api_gateway_client_mock():
    """Mock API Gateway Management API client."""
    mock = MagicMock(spec=APIGatewayManagementClient)
    return mock


def test_websocket_success(connections_table_mock, api_gateway_client_mock):
    """Tests successful WebSocket notification."""

    result = src.questions.notify.handler.publish_notification_to_websocket(
        "test123",
        "q-123456",
        QuestionStatus.COMPLETED,
        {"answer": "Resposta de teste", "question": "Pergunta de teste"},
        connections_table_mock,
        api_gateway_client_mock,
    )

    assert result is True
    api_gateway_client_mock.post_to_connection.assert_called_once()


def test_websocket_user_not_connected():
    """Tests WebSocket notification when user is not connected."""

    connections_table_mock = MagicMock(spec=DynamoDBTable)
    connections_table_mock.get_item.return_value = {"Item": {}}  # Sem connection_id

    result = src.questions.notify.handler.publish_notification_to_websocket(
        "test123", "q-123456", QuestionStatus.COMPLETED, {}, connections_table_mock
    )

    assert result is False


def test_websocket_connection_error(connections_table_mock):
    """Tests WebSocket notification when connection is gone."""

    api_gateway_client_mock = MagicMock(spec=APIGatewayManagementClient)
    api_gateway_client_mock.post_to_connection.side_effect = Exception(
        "GoneException: Connection not found"
    )

    result = src.questions.notify.handler.publish_notification_to_websocket(
        "test123",
        "q-123456",
        QuestionStatus.COMPLETED,
        {},
        connections_table_mock,
        api_gateway_client_mock,
    )

    assert result is False
    connections_table_mock.delete_item.assert_called_once()


def test_lambda_handler_success(
    lambda_context, db_client_mock, connections_table_mock, api_gateway_client_mock, standard_event
):
    """Tests the full flow of successfully processing a notification."""

    response = src.questions.notify.handler.lambda_handler(
        standard_event,
        lambda_context,
        db_client=db_client_mock,
        connections_table=connections_table_mock,
        api_gateway_client=api_gateway_client_mock,
    )

    assert response["success"] is True
    assert response["data"]["user_id"] == "test123"
    assert response["data"]["question_id"] == "q-123456"
    assert response["data"]["status"] == QuestionStatus.COMPLETED
    assert response["data"]["notification_sent"] is True

    db_client_mock.update_question.assert_called_once()


def test_lambda_handler_websocket_failure(lambda_context, db_client_mock, standard_event):
    """Tests handling when WebSocket notification fails."""

    connections_table_mock = MagicMock(spec=DynamoDBTable)
    connections_table_mock.get_item.return_value = {"Item": {}}  # Sem connection_id

    response = src.questions.notify.handler.lambda_handler(
        standard_event,
        lambda_context,
        db_client=db_client_mock,
        connections_table=connections_table_mock,
    )

    assert response["success"] is True
    assert response["data"]["notification_sent"] is False

    db_client_mock.update_question.assert_not_called()


def test_invalid_sns_event(lambda_context, db_client_mock):
    """Tests handling of invalid SNS event."""

    invalid_event = {"invalid": "data"}

    response = src.questions.notify.handler.lambda_handler(
        invalid_event, lambda_context, db_client=db_client_mock
    )

    assert response["success"] is False
    assert "error" in response
