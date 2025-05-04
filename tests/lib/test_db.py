"""
Testes unitários para o módulo lib/db.py.
"""

from unittest.mock import patch

from lib.db import get_question, save_question, update_question_status


def test_save_question(mock_dynamodb_table):
    """Testa o salvamento de uma nova pergunta no DynamoDB."""

    with patch("lib.db.table", mock_dynamodb_table):
        result = save_question("test123", "O que é CDB?")

        assert "user_id" in result
        assert "question_id" in result
        assert "status" in result
        assert result["user_id"] == "test123"
        assert result["status"] == "pending"

        mock_dynamodb_table.put_item.assert_called_once()

        item = mock_dynamodb_table.put_item.call_args[1]["Item"]
        assert item["user_id"] == "test123"
        assert item["question"] == "O que é CDB?"
        assert item["status"] == "pending"
        assert item["PK"].startswith("USER#")
        assert item["SK"].startswith("QUESTION#")
        assert "created_at" in item
        assert "updated_at" in item


def test_get_question(mock_dynamodb_table):
    """Testa a recuperação de uma pergunta específica do DynamoDB."""

    mock_response = {
        "Item": {
            "PK": "USER#test123",
            "SK": "QUESTION#abc123",
            "user_id": "test123",
            "question_id": "abc123",
            "question": "O que é CDB?",
            "status": "completed",
            "answer": "CDB é um investimento...",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:30:00",
        }
    }
    mock_dynamodb_table.get_item.return_value = mock_response

    with patch("lib.db.table", mock_dynamodb_table):
        result = get_question("test123", "abc123")

        assert result == mock_response["Item"]
        mock_dynamodb_table.get_item.assert_called_once_with(
            Key={"PK": "USER#test123", "SK": "QUESTION#abc123"}
        )


def test_get_question_not_found(mock_dynamodb_table):
    """Testa a recuperação de uma pergunta que não existe."""

    mock_dynamodb_table.get_item.return_value = {}

    with patch("lib.db.table", mock_dynamodb_table):
        result = get_question("test123", "nonexistent")

        assert result is None
        mock_dynamodb_table.get_item.assert_called_once()


def test_update_question_status_completed(mock_dynamodb_table):
    """Testa a atualização do status de uma pergunta para 'completed'."""

    mock_response = {
        "Attributes": {
            "PK": "USER#test123",
            "SK": "QUESTION#abc123",
            "user_id": "test123",
            "question_id": "abc123",
            "status": "completed",
            "answer": "CDB é um investimento...",
            "updated_at": "2023-01-01T13:00:00",
        }
    }
    mock_dynamodb_table.update_item.return_value = mock_response

    with patch("lib.db.table", mock_dynamodb_table):
        result = update_question_status(
            "test123", "abc123", "completed", answer="CDB é um investimento..."
        )

        assert result == mock_response["Attributes"]
        mock_dynamodb_table.update_item.assert_called_once()

        call_args = mock_dynamodb_table.update_item.call_args[1]
        assert call_args["Key"] == {"PK": "USER#test123", "SK": "QUESTION#abc123"}
        assert ":status" in call_args["ExpressionAttributeValues"]
        assert call_args["ExpressionAttributeValues"][":status"] == "completed"
        assert ":answer" in call_args["ExpressionAttributeValues"]
        assert call_args["ExpressionAttributeValues"][":answer"] == "CDB é um investimento..."


def test_update_question_status_error(mock_dynamodb_table):
    """Testa a atualização do status de uma pergunta para 'error'."""

    mock_response = {
        "Attributes": {
            "PK": "USER#test123",
            "SK": "QUESTION#abc123",
            "user_id": "test123",
            "question_id": "abc123",
            "status": "error",
            "error": "Erro ao processar a pergunta",
            "updated_at": "2023-01-01T13:00:00",
        }
    }
    mock_dynamodb_table.update_item.return_value = mock_response

    with patch("lib.db.table", mock_dynamodb_table):
        result = update_question_status(
            "test123", "abc123", "error", error="Erro ao processar a pergunta"
        )

        assert result == mock_response["Attributes"]
        mock_dynamodb_table.update_item.assert_called_once()

        call_args = mock_dynamodb_table.update_item.call_args[1]
        assert call_args["Key"] == {"PK": "USER#test123", "SK": "QUESTION#abc123"}
        assert ":status" in call_args["ExpressionAttributeValues"]
        assert call_args["ExpressionAttributeValues"][":status"] == "error"
        assert ":error" in call_args["ExpressionAttributeValues"]
        assert call_args["ExpressionAttributeValues"][":error"] == "Erro ao processar a pergunta"
