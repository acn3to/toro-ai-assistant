"""
Utilities for formatting HTTP and API Gateway responses.
"""

import json
from typing import Optional, TypedDict


class JSONResponse(TypedDict, total=False):
    """Model for JSON responses."""

    statusCode: int
    body: str
    headers: dict[str, str]
    isBase64Encoded: bool


def format_api_gateway_response(
    response_body: dict,
    status_code: Optional[int] = None,
    headers: Optional[dict[str, str]] = None,
) -> JSONResponse:
    """
    Formats a response for API Gateway.

    Args:
        response_body: Response body
        status_code: HTTP status code (default: 200 if success=True, 400 if success=False)
        headers: Optional HTTP headers

    Returns:
        Formatted response for API Gateway
    """
    if status_code is None:
        status_code = 200 if response_body.get("success", False) else 400

    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
    }

    if headers:
        default_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(response_body),
        "isBase64Encoded": False,
    }
