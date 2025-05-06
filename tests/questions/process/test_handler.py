"""
Unit tests for the question processing handler.
"""

import json

from lib.core.constants import STATUS_COMPLETED, STATUS_ERROR, STATUS_PROCESSING
import src.questions.process.handler


def test_successful_processing(
    lambda_context,
    db_client_mock,
    mock_sns_topic,
    mock_bedrock_client,
    mock_question_data,
    sns_event,
):
    """Tests the full flow of successfully processing a question."""
    db_client_mock.get_question.return_value = mock_question_data

    response = src.questions.process.handler.lambda_handler(
        sns_event,
        lambda_context,
        db_client=db_client_mock,
        bedrock_client=mock_bedrock_client,
        notify_topic=mock_sns_topic,
    )

    assert response["success"] is True
    assert response["data"]["user_id"] == "test123"
    assert response["data"]["question_id"] == "abc123"
    assert response["data"]["status"] == STATUS_COMPLETED

    db_client_mock.get_question.assert_called_once_with("test123", "abc123")

    processing_call = db_client_mock.update_question.call_args_list[0]
    assert processing_call[0][0] == "test123"
    assert processing_call[0][1] == "abc123"
    assert processing_call[0][2]["status"] == STATUS_PROCESSING

    mock_bedrock_client.retrieve_and_generate.assert_called_once_with(
        mock_question_data["question"]
    )

    completed_call = db_client_mock.update_question.call_args_list[1]
    assert completed_call[0][0] == "test123"
    assert completed_call[0][1] == "abc123"
    assert completed_call[0][2]["status"] == STATUS_COMPLETED
    assert (
        completed_call[0][2]["answer"]
        == mock_bedrock_client.retrieve_and_generate.return_value["answer"]
    )
    assert "sources" in completed_call[0][2]

    mock_sns_topic.publish.assert_called_once()
    published_message = json.loads(mock_sns_topic.publish.call_args[1]["Message"])
    assert published_message["user_id"] == "test123"
    assert published_message["question_id"] == "abc123"
    assert published_message["status"] == STATUS_COMPLETED


def test_direct_event_format(
    lambda_context, db_client_mock, mock_sns_topic, mock_bedrock_client, mock_question_data
):
    """Tests processing with direct event format (not SNS)."""
    db_client_mock.get_question.return_value = mock_question_data

    event = {"user_id": "test123", "question_id": "abc123"}

    response = src.questions.process.handler.lambda_handler(
        event,
        lambda_context,
        db_client=db_client_mock,
        bedrock_client=mock_bedrock_client,
        notify_topic=mock_sns_topic,
    )

    assert response["success"] is True
    db_client_mock.get_question.assert_called_once_with("test123", "abc123")
    mock_bedrock_client.retrieve_and_generate.assert_called_once()


def test_missing_parameters(lambda_context, db_client_mock, mock_sns_topic):
    """Tests the validation of required parameters."""
    event1 = {
        "Records": [
            {"EventSource": "aws:sns", "Sns": {"Message": json.dumps({"user_id": "test123"})}}
        ]
    }
    event2 = {
        "Records": [
            {"EventSource": "aws:sns", "Sns": {"Message": json.dumps({"question_id": "abc123"})}}
        ]
    }
    event3 = {"user_id": "test123"}

    response1 = src.questions.process.handler.lambda_handler(
        event1, lambda_context, db_client=db_client_mock, notify_topic=mock_sns_topic
    )
    response2 = src.questions.process.handler.lambda_handler(
        event2, lambda_context, db_client=db_client_mock, notify_topic=mock_sns_topic
    )
    response3 = src.questions.process.handler.lambda_handler(
        event3, lambda_context, db_client=db_client_mock, notify_topic=mock_sns_topic
    )

    assert response1["success"] is False
    assert response2["success"] is False
    assert response3["success"] is False

    db_client_mock.get_question.assert_not_called()
    mock_sns_topic.publish.assert_not_called()


def test_question_not_found(lambda_context, db_client_mock, mock_sns_topic):
    """Tests when the question is not found in the database."""
    db_client_mock.get_question.return_value = None

    event = {"user_id": "test123", "question_id": "nonexistent"}

    response = src.questions.process.handler.lambda_handler(
        event, lambda_context, db_client=db_client_mock, notify_topic=mock_sns_topic
    )

    assert response["success"] is False
    assert "Question not found" in response["error"]
    db_client_mock.get_question.assert_called_once_with("test123", "nonexistent")
    assert "status" not in db_client_mock.update_question.call_args_list


def test_bedrock_error_handling(
    lambda_context, db_client_mock, mock_sns_topic, mock_question_data, setup_bedrock_error_client
):
    """Tests the handling of errors from Bedrock."""
    db_client_mock.get_question.return_value = mock_question_data

    event = {"user_id": "test123", "question_id": "abc123"}

    response = src.questions.process.handler.lambda_handler(
        event,
        lambda_context,
        db_client=db_client_mock,
        bedrock_client=setup_bedrock_error_client,
        notify_topic=mock_sns_topic,
    )

    assert response["success"] is False
    assert "Bedrock model error" in response["error"]

    error_call = db_client_mock.update_question.call_args_list[-1]
    assert error_call[0][0] == "test123"
    assert error_call[0][1] == "abc123"
    assert error_call[0][2]["status"] == STATUS_ERROR
    assert "Bedrock model error" in error_call[0][2]["error_message"]

    mock_sns_topic.publish.assert_called_once()
    published_message = json.loads(mock_sns_topic.publish.call_args[1]["Message"])
    assert published_message["status"] == STATUS_ERROR


def test_different_bedrock_responses(
    lambda_context, db_client_mock, mock_sns_topic, mock_question_data, setup_minimal_bedrock_client
):
    """Tests different Bedrock response formats."""
    db_client_mock.get_question.return_value = mock_question_data

    event = {"user_id": "test123", "question_id": "abc123"}

    response = src.questions.process.handler.lambda_handler(
        event,
        lambda_context,
        db_client=db_client_mock,
        bedrock_client=setup_minimal_bedrock_client,
        notify_topic=mock_sns_topic,
    )

    assert response["success"] is True

    completed_call = db_client_mock.update_question.call_args_list[-1]
    assert completed_call[0][2]["answer"] == "Short answer"
    assert completed_call[0][2]["sources"] == []
