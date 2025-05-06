"""
AWS Lambda Handler for processing questions via API Gateway.
"""

import json
from typing import Optional

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from lib.adapters.dynamodb_client import DynamoDBClient
from lib.core.constants import STATUS_PENDING
from lib.core.response_utils import format_api_gateway_response
from lib.core.validation import parse_api_event, validate_question_input
from lib.factories.aws_clients import get_dynamodb_client, get_process_topic
from lib.models.api import APIErrorResponse, APISuccessResponse
from lib.models.aws import SNSTopic
from lib.models.question import QuestionResponse, SNSQuestionEvent

logger = Logger()
tracer = Tracer()


def _process_question_request(
    user_id: str, question_text: str, db_client: DynamoDBClient, process_topic: SNSTopic
) -> dict:
    """
    Saves the question to DynamoDB and triggers an SNS event for processing.

    Args:
        user_id: User ID of the requester.
        question_text: The question asked by the user.
        db_client: DynamoDB client instance.
        process_topic: SNS topic for further processing.

    Returns:
        A dictionary containing the question status and metadata.
    """
    try:
        question_data = db_client.save_question(user_id, question_text)
        question_id = question_data["question_id"]

        event = SNSQuestionEvent(
            user_id=user_id,
            question_id=question_id,
            status=STATUS_PENDING,
        )
        process_topic.publish(Message=json.dumps(event.model_dump()))

        return QuestionResponse(
            user_id=user_id,
            question_id=question_id,
            status=STATUS_PENDING,
        ).model_dump()

    except Exception as e:
        logger.exception(f"Error processing question: {e!s}")
        raise


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(
    event: dict,
    context: LambdaContext,
    db_client: Optional[DynamoDBClient] = None,
    process_topic: Optional[SNSTopic] = None,
) -> dict:
    """
    Main Lambda handler to process question requests via API Gateway.

    Args:
        event: The incoming event from API Gateway.
        context: Lambda function context.
        db_client: Optional DynamoDB client.
        process_topic: Optional SNS topic.

    Returns:
        A formatted API Gateway response.
    """
    try:
        db_client = db_client or get_dynamodb_client()
        process_topic = process_topic or get_process_topic()

        body = parse_api_event(event)
        validation_result = validate_question_input(body)

        if isinstance(validation_result, dict) and "error" in validation_result:
            error_response = APIErrorResponse(error=validation_result["error"]).model_dump()
            return format_api_gateway_response(error_response, status_code=400)

        user_id = validation_result.user_id
        question_text = validation_result.question
        response_data = _process_question_request(user_id, question_text, db_client, process_topic)

        success_response = APISuccessResponse(data=response_data).model_dump()
        return format_api_gateway_response(success_response)

    except Exception as e:
        logger.exception(f"Unhandled error: {e}")
        error_response = APIErrorResponse(error="Internal server error.").model_dump()
        return format_api_gateway_response(error_response, status_code=500)
