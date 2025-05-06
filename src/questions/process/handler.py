"""
AWS Lambda Function for processing questions using RAG with AWS Bedrock.
"""

from datetime import datetime, timezone
import json
from typing import Any, Optional

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from lib.adapters.bedrock_client import BedrockClient
from lib.adapters.dynamodb_client import DynamoDBClient
from lib.core.constants import STATUS_PROCESSING
from lib.factories.aws_clients import get_bedrock_client, get_dynamodb_client, get_notify_topic
from lib.models.api import APIErrorResponse, APISuccessResponse
from lib.models.aws import SNSTopic
from lib.models.question import QuestionStatus

logger = Logger()
tracer = Tracer()


def parse_sns_message(event: dict[str, Any]) -> dict[str, Any]:
    """
    Extracts the SNS message from the event.

    Args:
        event: Lambda event containing the SNS message.

    Returns:
        Parsed message as a dictionary.
    """
    try:
        if event.get("Records"):
            message_text = event["Records"][0]["Sns"]["Message"]
            return json.loads(message_text)
        return event
    except Exception as e:
        logger.exception(f"Error processing SNS message: {e}")
        return {"error": f"Error processing message: {e}"}


def update_question_status(
    db_client: DynamoDBClient, user_id: str, question_id: str, status: str
) -> None:
    """
    Updates the question status in DynamoDB.

    Args:
        db_client: DynamoDB client instance.
        user_id: User ID associated with the question.
        question_id: The ID of the question.
        status: The new status to be set.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    update_dict = {"status": status, "updated_at": timestamp}

    if status == STATUS_PROCESSING:
        update_dict["processing_started_at"] = timestamp
    elif status == QuestionStatus.COMPLETED:
        update_dict["processed_at"] = timestamp

    db_client.update_question(user_id, question_id, update_dict)


def send_notification(notify_topic: SNSTopic, user_id: str, question_id: str, status: str) -> None:
    """
    Sends a notification about the status update.

    Args:
        notify_topic: SNS topic for notifications.
        user_id: User ID associated with the question.
        question_id: The ID of the question.
        status: The status to be communicated.
    """
    message = {"user_id": user_id, "question_id": question_id, "status": status}
    notify_topic.publish(Message=json.dumps(message))


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(
    event: dict[str, Any],
    context: LambdaContext,
    db_client: Optional[DynamoDBClient] = None,
    bedrock_client: Optional[BedrockClient] = None,
    notify_topic: Optional[SNSTopic] = None,
) -> dict[str, Any]:
    """
    Main Lambda handler that processes questions using AWS Bedrock's RAG.

    Args:
        event: SNS event containing `user_id` and `question_id`.
        context: Lambda function context.
        db_client: Optional DynamoDB client instance (for testing).
        bedrock_client: Optional Bedrock client instance (for testing).
        notify_topic: Optional SNS topic for notifications (for testing).

    Returns:
        A dictionary with the result of the processing.
    """
    db_client = db_client or get_dynamodb_client()
    bedrock_client = bedrock_client or get_bedrock_client()
    notify_topic = notify_topic or get_notify_topic()

    try:
        message = parse_sns_message(event)
        if "error" in message:
            logger.error(f"Error processing event: {message['error']}")
            return APIErrorResponse(error=message["error"]).model_dump()

        user_id = message.get("user_id")
        question_id = message.get("question_id")

        if not user_id or not question_id:
            error = "Missing required fields: user_id and question_id are mandatory"
            logger.error(error)
            return APIErrorResponse(error=error).model_dump()

        question_item = db_client.get_question(user_id, question_id)
        if not question_item:
            error = f"Question not found: user_id={user_id}, question_id={question_id}"
            logger.error(error)
            return APIErrorResponse(error=error).model_dump()

        question_text = question_item.get("question", "")
        if not question_text:
            error = "Question text not found in DynamoDB item"
            logger.error(error)
            return APIErrorResponse(error=error).model_dump()

        update_question_status(db_client, user_id, question_id, STATUS_PROCESSING)
        logger.info(f"Processing question: '{question_text}'")

        rag_result = bedrock_client.retrieve_and_generate(question_text)
        answer = rag_result.get("answer", "")
        sources = rag_result.get("sources", [])
        inference_profile_id = rag_result.get("inference_profile_id", "")
        found_relevant_docs = rag_result.get("found_relevant_docs", False)

        sources_list = [source.get("document_id", source) for source in sources]

        timestamp = datetime.now(timezone.utc).isoformat()
        update_dict = {
            "status": QuestionStatus.COMPLETED,
            "answer": answer,
            "sources": sources_list,
            "inference_model": inference_profile_id,
            "found_relevant_docs": found_relevant_docs,
            "processed_at": timestamp,
            "updated_at": timestamp,
        }
        db_client.update_question(user_id, question_id, update_dict)

        send_notification(notify_topic, user_id, question_id, QuestionStatus.COMPLETED)

        response_data = {
            "user_id": user_id,
            "question_id": question_id,
            "status": QuestionStatus.COMPLETED,
            "found_relevant_docs": found_relevant_docs,
        }
        return APISuccessResponse(data=response_data).model_dump()

    except Exception as e:
        logger.exception(f"Error processing: {e}")

        user_id, question_id = None, None
        try:
            message = parse_sns_message(event)
            user_id = message.get("user_id")
            question_id = message.get("question_id")
        except Exception:
            pass

        if user_id and question_id:
            timestamp = datetime.now(timezone.utc).isoformat()
            error_dict = {
                "status": QuestionStatus.ERROR,
                "error_message": str(e),
                "updated_at": timestamp,
            }
            try:
                db_client.update_question(user_id, question_id, error_dict)
                send_notification(notify_topic, user_id, question_id, QuestionStatus.ERROR)
            except Exception as update_error:
                logger.exception(f"Error updating status to ERROR: {update_error}")

        return APIErrorResponse(error=str(e)).model_dump()
