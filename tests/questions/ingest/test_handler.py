"""
Testes unitários para o handler de ingestão de perguntas.
"""

import json
from unittest.mock import patch

import src.questions.ingest.handler


def test_successful_question_ingestion(lambda_context, mock_dynamodb_table, mock_sns_topic):
    """Testa o fluxo completo de ingestão de uma pergunta com sucesso."""

    event = {"body": json.dumps({"user_id": "test123", "question": "O que é CDB?"})}

    with (
        patch.object(src.questions.ingest.handler, "table", mock_dynamodb_table),
        patch.object(src.questions.ingest.handler, "process_topic", mock_sns_topic),
    ):
        response = src.questions.ingest.handler.lambda_handler(event, lambda_context)
        response_body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert response_body["success"] is True
        assert "question_id" in response_body["data"]
        assert response_body["data"]["user_id"] == "test123"
        assert response_body["data"]["status"] == "pending"

        mock_dynamodb_table.put_item.assert_called_once()
        mock_sns_topic.publish.assert_called_once()


def test_missing_required_fields(lambda_context):
    """Testa a validação de campos obrigatórios."""

    event = {"body": json.dumps({"question": "O que é CDB?"})}
    response = src.questions.ingest.handler.lambda_handler(event, lambda_context)
    assert response["statusCode"] == 400

    event = {"body": json.dumps({"user_id": "test123"})}
    response = src.questions.ingest.handler.lambda_handler(event, lambda_context)
    assert response["statusCode"] == 400

    event = {"body": json.dumps({})}
    response = src.questions.ingest.handler.lambda_handler(event, lambda_context)
    assert response["statusCode"] == 400


def test_direct_json_body(lambda_context, mock_dynamodb_table, mock_sns_topic):
    """Testa quando o body já é um objeto JSON (não string)."""

    event = {"body": {"user_id": "test123", "question": "O que é CDB?"}}

    with (
        patch.object(src.questions.ingest.handler, "table", mock_dynamodb_table),
        patch.object(src.questions.ingest.handler, "process_topic", mock_sns_topic),
    ):
        response = src.questions.ingest.handler.lambda_handler(event, lambda_context)
        response_body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert response_body["success"] is True
        assert mock_dynamodb_table.put_item.called
        assert mock_sns_topic.publish.called


def test_exception_handling(lambda_context, mock_dynamodb_table):
    """Testa o tratamento de exceções no handler."""

    event = {"body": json.dumps({"user_id": "test123", "question": "O que é CDB?"})}

    mock_dynamodb_table.put_item.side_effect = Exception("Erro simulado")

    with patch.object(src.questions.ingest.handler, "table", mock_dynamodb_table):
        response = src.questions.ingest.handler.lambda_handler(event, lambda_context)
        response_body = json.loads(response["body"])

        assert response["statusCode"] == 500
        assert response_body["success"] is False
        assert response_body["error"] == "Erro interno do servidor."
