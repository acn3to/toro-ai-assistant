"""
API Models for response validation and formatting.
"""

from typing import Any, TypedDict

from pydantic import BaseModel


class ErrorResponse(TypedDict):
    """Model for standardized error responses."""

    error: str


class APIResponse(BaseModel):
    """Base model for API responses."""

    success: bool


class APIErrorResponse(APIResponse):
    """Model for API error responses."""

    success: bool = False
    error: str


class APISuccessResponse(APIResponse):
    """Model for API success responses."""

    success: bool = True
    data: dict[str, Any]
