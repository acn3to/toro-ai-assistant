"""
Unit tests for the module lib/adapters/dynamodb_client.py.
"""

from unittest.mock import MagicMock

import pytest

from lib.adapters.dynamodb_client import DynamoDBClient


def setup_mocked_db_client(mock_dynamodb_table):
    """Sets up and returns a DynamoDBClient with a mocked table."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_dynamodb_table
    return DynamoDBClient(dynamodb_resource=mock_dynamodb)


def assert_dynamodb_keys(item, user_id, question_id=None):
    """Checks if the DynamoDB keys are correctly formatted."""
    assert item["PK"] == f"USER#{user_id}"
    if question_id:
        assert item["SK"] == f"QUESTION#{question_id}"
    else:
        assert item["SK"].startswith("QUESTION#")


def test_save_question_with_moto(moto_dynamodb):
    """Tests saving a new question to DynamoDB."""

    client = DynamoDBClient(dynamodb_resource=moto_dynamodb)
    result = client.save_question("test123", "O que é CDB?")

    assert "user_id" in result
    assert "question_id" in result
    assert "status" in result
    assert result["user_id"] == "test123"
    assert result["status"] == "pending"

    table = moto_dynamodb.Table("toro-ai-assistant-questions")
    response = table.scan()
    items = response.get("Items", [])

    assert len(items) == 1
    assert items[0]["user_id"] == "test123"
    assert items[0]["question"] == "O que é CDB?"
    assert items[0]["status"] == "pending"
    assert_dynamodb_keys(items[0], "test123")
    assert "created_at" in items[0]
    assert "updated_at" in items[0]


def test_get_question_found(mock_dynamodb_table, mock_question_data):
    """Tests successfully retrieving a specific question from DynamoDB."""

    mock_response = {"Item": mock_question_data}
    mock_dynamodb_table.get_item.return_value = mock_response

    client = setup_mocked_db_client(mock_dynamodb_table)
    result = client.get_question("test123", "abc123")

    assert result == mock_question_data

    mock_dynamodb_table.get_item.assert_called_once_with(
        Key={"PK": "USER#test123", "SK": "QUESTION#abc123"}
    )


def test_get_question_not_found(mock_dynamodb_table):
    """Tests retrieving a question that does not exist."""

    mock_dynamodb_table.get_item.return_value = {}

    client = setup_mocked_db_client(mock_dynamodb_table)
    result = client.get_question("test123", "nonexistent")

    assert result is None

    mock_dynamodb_table.get_item.assert_called_once()


def test_update_question_status_structure(mock_dynamodb_table):
    """Tests the structure of the status update call."""

    mock_dynamodb_table.update_item.return_value = {"Attributes": {}}
    client = setup_mocked_db_client(mock_dynamodb_table)

    client.update_question_status("test123", "abc123", "processing")

    call_args = mock_dynamodb_table.update_item.call_args[1]
    assert call_args["Key"] == {"PK": "USER#test123", "SK": "QUESTION#abc123"}
    assert ":status" in call_args["ExpressionAttributeValues"]
    assert call_args["ExpressionAttributeValues"][":status"] == "processing"
    assert ":updated_at" in call_args["ExpressionAttributeValues"]


def test_update_question_status_response(mock_dynamodb_table):
    """Tests the response after updating the status."""

    mock_response = {
        "Attributes": {
            "PK": "USER#test123",
            "SK": "QUESTION#abc123",
            "user_id": "test123",
            "question_id": "abc123",
            "status": "processing",
            "updated_at": "2023-01-01T13:00:00",
        }
    }
    mock_dynamodb_table.update_item.return_value = mock_response

    client = setup_mocked_db_client(mock_dynamodb_table)
    result = client.update_question_status("test123", "abc123", "processing")

    assert result == mock_response["Attributes"]
    assert result["status"] == "processing"


def test_update_question_content(mock_dynamodb_table):
    """Tests updating the content of a question."""

    mock_response = {
        "Attributes": {
            "PK": "USER#test123",
            "SK": "QUESTION#abc123",
            "user_id": "test123",
            "question_id": "abc123",
            "status": "completed",
            "answer": "CDB is an investment...",
            "updated_at": "2023-01-01T13:00:00",
        }
    }
    mock_dynamodb_table.update_item.return_value = mock_response

    client = setup_mocked_db_client(mock_dynamodb_table)
    update_data = {"status": "completed", "answer": "CDB is an investment..."}
    result = client.update_question("test123", "abc123", update_data)

    assert result == mock_response["Attributes"]
    assert result["status"] == "completed"
    assert result["answer"] == "CDB is an investment..."


def test_update_question_expression_structure(mock_dynamodb_table):
    """Tests the structure of the update expression."""

    mock_dynamodb_table.update_item.return_value = {"Attributes": {}}
    client = setup_mocked_db_client(mock_dynamodb_table)

    update_data = {"status": "error", "error_message": "Error processing the question"}
    client.update_question("test123", "abc123", update_data)

    call_args = mock_dynamodb_table.update_item.call_args[1]

    assert call_args["Key"] == {"PK": "USER#test123", "SK": "QUESTION#abc123"}

    assert "#attr0" in call_args["ExpressionAttributeNames"]
    assert "#attr1" in call_args["ExpressionAttributeNames"]
    assert "#attr2" in call_args["ExpressionAttributeNames"]

    status_placeholder = None
    for name, value in call_args["ExpressionAttributeNames"].items():
        if value == "status":
            status_placeholder = name
            break

    assert status_placeholder is not None
    value_placeholder = status_placeholder.replace("#attr", ":val")
    assert value_placeholder in call_args["ExpressionAttributeValues"]
    assert call_args["ExpressionAttributeValues"][value_placeholder] == "error"


def test_list_user_questions(mock_dynamodb_table):
    """Tests listing a user's questions."""

    mock_items = [
        {
            "PK": "USER#test123",
            "SK": "QUESTION#abc123",
            "user_id": "test123",
            "question_id": "abc123",
            "question": "O que é CDB?",
            "status": "completed",
            "created_at": "2023-01-01T12:00:00",
        },
        {
            "PK": "USER#test123",
            "SK": "QUESTION#def456",
            "user_id": "test123",
            "question_id": "def456",
            "question": "How does the Stock Market work?",
            "status": "pending",
            "created_at": "2023-01-02T14:00:00",
        },
    ]

    mock_dynamodb_table.query.return_value = {"Items": mock_items}

    client = setup_mocked_db_client(mock_dynamodb_table)
    result = client.list_user_questions("test123", limit=10)

    assert "items" in result
    assert len(result["items"]) == 2
    assert result["items"] == mock_items
    assert "next_token" not in result

    mock_dynamodb_table.query.assert_called_once_with(
        KeyConditionExpression="#pk = :pk_val",
        ExpressionAttributeNames={"#pk": "PK"},
        ExpressionAttributeValues={":pk_val": "USER#test123"},
        Limit=10,
    )


def test_list_user_questions_pagination(mock_dynamodb_table):
    """Tests pagination in listing questions."""
    mock_items = [
        {
            "user_id": "test123",
            "question_id": "abc123",
            "question": "O que é CDB?",
            "status": "completed",
        }
    ]

    mock_response = {
        "Items": mock_items,
        "LastEvaluatedKey": {"PK": "USER#test123", "SK": "QUESTION#xyz789"},
    }

    mock_dynamodb_table.query.return_value = mock_response

    client = setup_mocked_db_client(mock_dynamodb_table)
    result = client.list_user_questions("test123", limit=5)

    assert "items" in result
    assert result["items"] == mock_items
    assert "next_token" in result
    assert result["next_token"] == {"PK": "USER#test123", "SK": "QUESTION#xyz789"}

    call_kwargs = mock_dynamodb_table.query.call_args[1]
    assert call_kwargs["Limit"] == 5


def test_list_user_questions_with_token(mock_dynamodb_table):
    """Tests listing questions with a continuation token."""
    mock_items = [
        {
            "user_id": "test123",
            "question_id": "def456",
            "question": "Page 2",
            "status": "completed",
        }
    ]

    mock_dynamodb_table.query.return_value = {"Items": mock_items}

    next_token = {"PK": "USER#test123", "SK": "QUESTION#abc123"}

    client = setup_mocked_db_client(mock_dynamodb_table)
    result = client.list_user_questions("test123", next_token=next_token)

    assert "items" in result
    assert result["items"] == mock_items

    call_kwargs = mock_dynamodb_table.query.call_args[1]
    assert "ExclusiveStartKey" in call_kwargs
    assert call_kwargs["ExclusiveStartKey"] == next_token


def test_default_limit_value(mock_dynamodb_table):
    """Tests the default limit value in listing questions."""
    mock_dynamodb_table.query.return_value = {"Items": []}

    client = setup_mocked_db_client(mock_dynamodb_table)
    client.list_user_questions("test123")

    call_kwargs = mock_dynamodb_table.query.call_args[1]
    assert call_kwargs["Limit"] == 20


def test_logging_save_question(moto_dynamodb, caplog):
    """Tests logging the question save operation."""
    client = DynamoDBClient(dynamodb_resource=moto_dynamodb)
    result = client.save_question("test-log", "Test log")

    question_id = result["question_id"]
    assert f"Question saved: user_id=test-log, question_id={question_id}" in caplog.text


def test_logging_update_question(mock_dynamodb_table, caplog):
    """Tests logging the question update operation."""
    mock_dynamodb_table.update_item.return_value = {
        "Attributes": {
            "user_id": "test-log",
            "question_id": "abc-log",
        }
    }

    client = setup_mocked_db_client(mock_dynamodb_table)
    client.update_question("test-log", "abc-log", {"status": "completed"})

    assert "Question updated: user_id=test-log, question_id=abc-log" in caplog.text


def test_build_key_method(mock_dynamodb_table):
    """Tests the _build_key method."""
    client = setup_mocked_db_client(mock_dynamodb_table)
    key = client._build_key("test123", "abc123")

    assert key == {"PK": "USER#test123", "SK": "QUESTION#abc123"}


def test_client_initialization_with_none_resource():
    """Tests that DynamoDBClient raises ValueError when dynamodb_resource is None."""
    with pytest.raises(ValueError, match="dynamodb_resource cannot be None"):
        DynamoDBClient(dynamodb_resource=None)
