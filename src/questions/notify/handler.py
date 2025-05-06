"""
Handler to process notifications about question updates.
Receives events via SNS and triggers notification actions to users via WebSocket.
"""

from datetime import datetime, timezone
import json
from typing import Optional

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from lib.adapters.dynamodb_client import DynamoDBClient
from lib.core.validation import parse_sns_message
from lib.factories.aws_clients import (
    get_api_gateway_management_client,
    get_connections_table,
    get_dynamodb_client,
)
from lib.models.api import APIErrorResponse, APISuccessResponse
from lib.models.aws import APIGatewayManagementClient, DynamoDBTable
from lib.models.question import QuestionStatus

logger = Logger()
tracer = Tracer()


def get_timestamp() -> str:
    """
    Returns the current timestamp in ISO format.

    Returns:
        ISO formatted timestamp
    """
    return datetime.now(timezone.utc).isoformat()


def publish_notification_to_websocket(
    user_id: str,
    question_id: str,
    status: str,
    question_data: Optional[dict] = None,
    connections_table: Optional[DynamoDBTable] = None,
    api_gateway_client: Optional[APIGatewayManagementClient] = None,
) -> bool:
    """
    Publishes a notification to the user via WebSocket.

    Args:
        user_id: User ID
        question_id: Question ID
        status: Current question status
        question_data: Full question and answer data
        connections_table: DynamoDB table for WebSocket connections
        api_gateway_client: API Gateway Management client

    Returns:
        True if the notification was sent, False otherwise
    """
    try:
        connections_table = connections_table or get_connections_table()

        response = connections_table.get_item(Key={"user_id": user_id})
        connection_id = response.get("Item", {}).get("connection_id")

        if not connection_id:
            logger.info(f"User {user_id} is not connected to WebSocket")
            return False

        payload = {"type": "question_update", "question_id": question_id, "status": status}

        if status == QuestionStatus.COMPLETED and question_data:
            payload["answer"] = question_data.get("answer", "")
            payload["sources"] = question_data.get("sources", [])
            payload["question"] = question_data.get("question", "")
        elif status == QuestionStatus.ERROR:
            payload["error_message"] = question_data.get("error_message", "Unknown error")

        api_client = api_gateway_client or get_api_gateway_management_client()
        api_client.post_to_connection(ConnectionId=connection_id, Data=json.dumps(payload))

        logger.info(f"WebSocket notification sent to {user_id}")
        return True

    except Exception as e:
        if "GoneException" in str(e):
            try:
                connections_table = connections_table or get_connections_table()
                connections_table.delete_item(Key={"user_id": user_id})
                logger.info(f"Expired connection removed for user {user_id}")
            except Exception as delete_error:
                logger.exception(f"Error removing expired connection: {delete_error}")

        logger.exception(f"Error sending WebSocket notification: {e}")
        return False


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(
    event: dict,
    context: LambdaContext,
    db_client: Optional[DynamoDBClient] = None,
    connections_table: Optional[DynamoDBTable] = None,
    api_gateway_client: Optional[APIGatewayManagementClient] = None,
) -> dict:
    """
    Main handler that processes question update notifications.

    Args:
        event: SNS event with user_id, question_id and status
        context: Lambda execution context
        db_client: Optional DynamoDB client (for testing)
        connections_table: Optional WebSocket connections table (for testing)
        api_gateway_client: Optional API Gateway Management client (for testing)

    Returns:
        Processing result
    """
    try:
        logger.info("Received notification event")
        db_client = db_client or get_dynamodb_client()

        sns_event = parse_sns_message(event)

        if isinstance(sns_event, dict) and "error" in sns_event:
            logger.error(f"Error processing SNS event: {sns_event['error']}")
            return APIErrorResponse(error=sns_event["error"]).model_dump()

        user_id = sns_event.user_id
        question_id = sns_event.question_id
        status = sns_event.status or QuestionStatus.PENDING

        question_data = db_client.get_question(user_id, question_id)

        websocket_sent = publish_notification_to_websocket(
            user_id, question_id, status, question_data, connections_table, api_gateway_client
        )

        if status == QuestionStatus.COMPLETED:
            logger.info(f"Question {question_id} from user {user_id} was successfully answered")
        elif status == QuestionStatus.ERROR:
            logger.info(f"Error processing question {question_id} from user {user_id}")

        if websocket_sent:
            notification_update = {
                "notification_sent": True,
                "notification_details": {
                    "realtime_sent": websocket_sent,
                    "notification_time": get_timestamp(),
                },
            }
            db_client.update_question(user_id, question_id, notification_update)

        response_data = {
            "user_id": user_id,
            "question_id": question_id,
            "status": status,
            "notification_sent": websocket_sent,
            "notification_details": {
                "realtime_sent": websocket_sent,
            },
        }

        return APISuccessResponse(data=response_data).model_dump()

    except Exception as e:
        logger.exception(f"Unhandled error: {e}")
        return APIErrorResponse(error=str(e)).model_dump()
