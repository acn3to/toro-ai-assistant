"""
Data models for questions and updates.
"""

from enum import Enum
from typing import Optional, TypedDict

from pydantic import BaseModel, field_validator, model_validator

from lib.core.constants import STATUS_COMPLETED, STATUS_ERROR, STATUS_PENDING, STATUS_PROCESSING


class QuestionStatus(str, Enum):
    """Enum for question statuses."""

    PENDING = STATUS_PENDING
    PROCESSING = STATUS_PROCESSING
    COMPLETED = STATUS_COMPLETED
    ERROR = STATUS_ERROR


class DynamoDBKey(TypedDict):
    """Model for DynamoDB keys."""

    PK: str
    SK: str


class QuestionRequest(BaseModel):
    """Model for validating question requests."""

    user_id: str
    question: str

    @field_validator("user_id", "question")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Validates that string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Cannot be an empty string")
        return v.strip()

    @field_validator("question")
    @classmethod
    def max_length(cls, v: str) -> str:
        """Validates the maximum length of the question."""
        if len(v) > 2000:
            raise ValueError("The question must be at most 2000 characters")
        return v


class SNSQuestionEvent(BaseModel):
    """Model for question events in SNS."""

    user_id: str
    question_id: str
    status: Optional[QuestionStatus] = None

    @field_validator("user_id", "question_id")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Validates that string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Cannot be an empty string")
        return v.strip()


class QuestionResponse(BaseModel):
    """Model for question operation responses."""

    user_id: str
    question_id: str
    status: QuestionStatus = QuestionStatus.PENDING


class QuestionUpdateData(BaseModel):
    """Model for question updates."""

    status: Optional[QuestionStatus] = None
    answer: Optional[str] = None
    error_message: Optional[str] = None
    sources: Optional[list[str]] = None
    inference_profile_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "QuestionUpdateData":
        """Validates that at least one field is being updated."""
        if all(v is None for v in self.model_dump().values()):
            raise ValueError("At least one field must be updated")
        return self


class QuestionItem(BaseModel):
    """Complete model for a question item in DynamoDB."""

    PK: str
    SK: str
    user_id: str
    question_id: str
    question: str
    status: str
    created_at: str
    updated_at: str
    answer: Optional[str] = None
    error_message: Optional[str] = None
    sources: Optional[list[str]] = None
    inference_profile_id: Optional[str] = None
    processed_at: Optional[str] = None
