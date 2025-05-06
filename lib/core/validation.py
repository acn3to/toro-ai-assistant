"""
Module for data validation functions.
"""

import json
from typing import Any, Union

from lib.models.api import ErrorResponse
from lib.models.question import (
    DynamoDBKey,
    QuestionRequest,
    QuestionStatus,
    QuestionUpdateData,
    SNSQuestionEvent,
)


def build_dynamodb_key(user_id: str, question_id: str) -> DynamoDBKey:
    """
    Builds the primary key for a DynamoDB item.

    Args:
        user_id: User ID
        question_id: Question ID

    Returns:
        Dictionary with the formatted primary key
    """
    return {"PK": f"USER#{user_id}", "SK": f"QUESTION#{question_id}"}


def validate_question_input(body: Any) -> Union[QuestionRequest, ErrorResponse]:
    """
    Validates a question request using Pydantic.

    Args:
        body: Request body

    Returns:
        Validated QuestionRequest model or ErrorResponse on error
    """
    try:
        return QuestionRequest.model_validate(body)
    except Exception as e:
        return {"error": str(e)}


def parse_api_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    Extracts and validates the body from an API Gateway event.

    Args:
        event: API Gateway event

    Returns:
        Event body content as a dictionary
    """
    if "body" in event:
        body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
    else:
        body = event

    return body


def parse_sns_message(event: dict[str, Any]) -> Union[SNSQuestionEvent, ErrorResponse]:
    """
    Extracts and validates a message from an SNS event.

    Args:
        event: SNS event

    Returns:
        Validated SNSQuestionEvent model or ErrorResponse on error
    """
    try:
        if "Records" in event and event["Records"][0].get("EventSource") == "aws:sns":
            message_str = event["Records"][0]["Sns"]["Message"]
            message = json.loads(message_str) if isinstance(message_str, str) else message_str
        else:
            message = event

        return SNSQuestionEvent.model_validate(message)
    except Exception as e:
        return {"error": str(e)}


def format_error_update(error: Exception) -> QuestionUpdateData:
    """
    Formats data for an error update.

    Args:
        error: Exception that occurred

    Returns:
        QuestionUpdateData model with error information
    """
    return QuestionUpdateData(status=QuestionStatus.ERROR, error_message=str(error))
