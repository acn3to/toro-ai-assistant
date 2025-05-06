"""
Unit tests for the question ingestion handler.
"""

import json

from lib.core.constants import STATUS_PENDING
import src.questions.ingest.handler


def test_successful_question_ingestion(
    lambda_context, db_client_mock, mock_sns_topic, standard_event
):
    """Tests the full flow of successfully ingesting a question."""

    response = src.questions.ingest.handler.lambda_handler(
        standard_event, lambda_context, db_client=db_client_mock, process_topic=mock_sns_topic
    )
    response_body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert response_body["success"] is True
    assert "question_id" in response_body["data"]
    assert response_body["data"]["user_id"] == "test123"
    assert response_body["data"]["status"] == STATUS_PENDING

    db_client_mock.save_question.assert_called_once_with("test123", "O que é CDB?")
    mock_sns_topic.publish.assert_called_once()


def test_missing_required_fields(lambda_context, db_client_mock, mock_sns_topic):
    """Tests the validation of required fields."""

    event = {"body": json.dumps({"question": "O que é CDB?"})}
    response = src.questions.ingest.handler.lambda_handler(
        event, lambda_context, db_client=db_client_mock, process_topic=mock_sns_topic
    )
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert response_body["success"] is False
    assert "error" in response_body

    event = {"body": json.dumps({"user_id": "test123"})}
    response = src.questions.ingest.handler.lambda_handler(
        event, lambda_context, db_client=db_client_mock, process_topic=mock_sns_topic
    )
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert response_body["success"] is False
    assert "error" in response_body

    event = {"body": json.dumps({})}
    response = src.questions.ingest.handler.lambda_handler(
        event, lambda_context, db_client=db_client_mock, process_topic=mock_sns_topic
    )
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert response_body["success"] is False
    assert "error" in response_body

    db_client_mock.save_question.assert_not_called()
    mock_sns_topic.publish.assert_not_called()


def test_direct_json_body(lambda_context, db_client_mock, mock_sns_topic, direct_json_event):
    """Tests when the body is already a JSON object (not a string)."""

    response = src.questions.ingest.handler.lambda_handler(
        direct_json_event, lambda_context, db_client=db_client_mock, process_topic=mock_sns_topic
    )
    response_body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert response_body["success"] is True
    assert db_client_mock.save_question.called
    assert mock_sns_topic.publish.called


def test_exception_handling(
    lambda_context, mock_error_dynamodb_client, mock_sns_topic, standard_event
):
    """Tests exception handling in the handler."""

    response = src.questions.ingest.handler.lambda_handler(
        standard_event,
        lambda_context,
        db_client=mock_error_dynamodb_client,
        process_topic=mock_sns_topic,
    )
    response_body = json.loads(response["body"])

    assert response["statusCode"] == 500
    assert response_body["success"] is False
    assert response_body["error"] == "Internal server error."


def test_integration_with_moto(lambda_context, db_client_moto, mock_sns_topic):
    """
    Integration test that uses Moto to simulate the real DynamoDB.
    This test evaluates the full flow with a simulated DynamoDB.
    """
    event = {"body": json.dumps({"user_id": "test-moto", "question": "Test with Moto"})}

    response = src.questions.ingest.handler.lambda_handler(
        event, lambda_context, db_client=db_client_moto, process_topic=mock_sns_topic
    )
    response_body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert response_body["success"] is True

    question_id = response_body["data"]["question_id"]

    response = db_client_moto.get_question("test-moto", question_id)

    assert response is not None
    assert response["user_id"] == "test-moto"
    assert response["question"] == "Test with Moto"
    assert response["status"] == STATUS_PENDING

    mock_sns_topic.publish.assert_called_once()
