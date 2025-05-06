"""
Unit tests for the WebSocket handler.
"""

import json
from unittest.mock import MagicMock

import pytest

from lib.models.aws import DynamoDBTable
import src.websocket.handler


@pytest.fixture
def connections_table_mock():
    """Mock DynamoDB connections table."""
    mock = MagicMock(spec=DynamoDBTable)
    return mock


@pytest.fixture
def connect_event():
    """Fixture for a WebSocket $connect event."""
    return {
        "requestContext": {"connectionId": "connection-123", "routeKey": "$connect"},
        "queryStringParameters": {"user_id": "test123"},
    }


@pytest.fixture
def connect_event_no_user():
    """Fixture for a WebSocket $connect event without user_id."""
    return {
        "requestContext": {"connectionId": "connection-123", "routeKey": "$connect"},
        "queryStringParameters": {},
    }


@pytest.fixture
def disconnect_event():
    """Fixture for a WebSocket $disconnect event."""
    return {"requestContext": {"connectionId": "connection-123", "routeKey": "$disconnect"}}


@pytest.fixture
def register_event():
    """Fixture for a WebSocket register event."""
    return {
        "requestContext": {"connectionId": "connection-123", "routeKey": "register"},
        "body": json.dumps({"user_id": "test123"}),
    }


@pytest.fixture
def register_event_no_user():
    """Fixture for a WebSocket register event without user_id."""
    return {
        "requestContext": {"connectionId": "connection-123", "routeKey": "register"},
        "body": json.dumps({}),
    }


def test_connect_with_user(connect_event, connections_table_mock):
    """Tests handling of $connect event with user_id."""

    response = src.websocket.handler.lambda_handler(
        connect_event, {}, connections_table=connections_table_mock
    )

    assert response["statusCode"] == 200
    connections_table_mock.put_item.assert_called_once_with(
        Item={"user_id": "test123", "connection_id": "connection-123"}
    )


def test_connect_without_user(connect_event_no_user, connections_table_mock):
    """Tests handling of $connect event without user_id."""

    response = src.websocket.handler.lambda_handler(
        connect_event_no_user, {}, connections_table=connections_table_mock
    )

    assert response["statusCode"] == 200
    connections_table_mock.put_item.assert_not_called()


def test_disconnect(disconnect_event, connections_table_mock):
    """Tests handling of $disconnect event."""

    # Simula encontrar um item com esse connection_id
    connections_table_mock.scan.return_value = {
        "Items": [{"user_id": "test123", "connection_id": "connection-123"}]
    }

    response = src.websocket.handler.lambda_handler(
        disconnect_event, {}, connections_table=connections_table_mock
    )

    assert response["statusCode"] == 200
    connections_table_mock.delete_item.assert_called_once_with(Key={"user_id": "test123"})


def test_register(register_event, connections_table_mock):
    """Tests handling of register event."""

    response = src.websocket.handler.lambda_handler(
        register_event, {}, connections_table=connections_table_mock
    )

    assert response["statusCode"] == 200
    connections_table_mock.put_item.assert_called_once_with(
        Item={"user_id": "test123", "connection_id": "connection-123"}
    )


def test_register_no_user(register_event_no_user, connections_table_mock):
    """Tests handling of register event without user_id."""

    response = src.websocket.handler.lambda_handler(
        register_event_no_user, {}, connections_table=connections_table_mock
    )

    assert response["statusCode"] == 400
    connections_table_mock.put_item.assert_not_called()


def test_unknown_route(connections_table_mock):
    """Tests handling of unknown route."""

    event = {"requestContext": {"connectionId": "connection-123", "routeKey": "unknown"}}

    response = src.websocket.handler.lambda_handler(
        event, {}, connections_table=connections_table_mock
    )

    assert response["statusCode"] == 404
    connections_table_mock.put_item.assert_not_called()


def test_exception_handling(register_event, connections_table_mock):
    """Tests exception handling."""

    connections_table_mock.put_item.side_effect = Exception("Test error")

    response = src.websocket.handler.lambda_handler(
        register_event, {}, connections_table=connections_table_mock
    )

    assert response["statusCode"] == 500
    assert "Test error" in response["body"]
