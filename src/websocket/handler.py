"""
Handler to manage WebSocket connections for the Toro AI Assistant.
"""

import json
from typing import Any, Optional

from aws_lambda_powertools import Logger

from lib.factories.aws_clients import get_connections_table
from lib.models.aws import DynamoDBTable

logger = Logger()


def get_connection_id(event: dict[str, Any]) -> str:
    """
    Extracts the connection ID from the event.

    Args:
        event: API Gateway WebSocket event

    Returns:
        Connection ID
    """
    return event["requestContext"]["connectionId"]


def get_route_key(event: dict[str, Any]) -> str:
    """
    Extracts the route key from the event.

    Args:
        event: API Gateway WebSocket event

    Returns:
        Route key ($connect, $disconnect, etc.)
    """
    return event["requestContext"]["routeKey"]


def get_user_id(event: dict[str, Any]) -> Optional[str]:
    """
    Extracts the user_id from query parameters.

    Args:
        event: API Gateway WebSocket event

    Returns:
        User ID or None if not present
    """
    query_params = event.get("queryStringParameters", {}) or {}
    return query_params.get("user_id")


def get_body_user_id(event: dict[str, Any]) -> Optional[str]:
    """
    Extracts the user_id from the message body.

    Args:
        event: API Gateway WebSocket event

    Returns:
        User ID or None if not present
    """
    try:
        if event.get("body"):
            body = json.loads(event["body"])
            return body.get("user_id")
    except Exception:
        pass
    return None


def lambda_handler(
    event: dict[str, Any], context: Any, connections_table: Optional[DynamoDBTable] = None
) -> dict[str, Any]:
    """
    Main handler for WebSocket connections and messages.

    Args:
        event: API Gateway WebSocket event
        context: Lambda context
        connections_table: Optional WebSocket connections table (for testing)

    Returns:
        Formatted response for API Gateway
    """
    connection_id = get_connection_id(event)
    route_key = get_route_key(event)

    connections_table = connections_table or get_connections_table()

    try:
        if route_key == "$connect":
            user_id = get_user_id(event)
            if user_id:
                connections_table.put_item(
                    Item={"user_id": user_id, "connection_id": connection_id}
                )
                logger.info(f"User {user_id} connected with connection_id {connection_id}")
            else:
                logger.info(f"New connection {connection_id} without user_id")

            return {"statusCode": 200, "body": "Connected"}

        elif route_key == "$disconnect":
            response = connections_table.scan(
                FilterExpression="connection_id = :conn_id",
                ExpressionAttributeValues={":conn_id": connection_id},
            )

            for item in response.get("Items", []):
                user_id = item.get("user_id")
                if user_id:
                    connections_table.delete_item(Key={"user_id": user_id})
                    logger.info(f"Connection with user_id {user_id} removed")

            return {"statusCode": 200, "body": "Disconnected"}

        elif route_key == "register":
            user_id = get_body_user_id(event)

            if not user_id:
                return {"statusCode": 400, "body": "user_id is required"}

            connections_table.put_item(Item={"user_id": user_id, "connection_id": connection_id})

            logger.info(f"User {user_id} registered with connection_id {connection_id}")
            return {"statusCode": 200, "body": "User registered"}

        else:
            logger.warning(f"Unhandled route: {route_key}")
            return {"statusCode": 404, "body": "Route not implemented"}

    except Exception as e:
        logger.exception(f"Error processing WebSocket event: {e}")
        return {"statusCode": 500, "body": f"Internal error: {e!s}"}
