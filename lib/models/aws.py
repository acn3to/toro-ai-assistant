"""
Data models for specific AWS resource typing.
"""

from typing import Any, Protocol, TypedDict, runtime_checkable


@runtime_checkable
class SNSTopic(Protocol):
    """Protocol for representing an SNS topic."""

    def publish(self, **kwargs: Any) -> dict[str, Any]:
        """
        Publishes a message to the SNS topic.

        Args:
            **kwargs: Arguments for publishing the message

        Returns:
            The response from the publish operation
        """
        ...


class DynamoDBResponse(TypedDict, total=False):
    """Model for DynamoDB responses."""

    Attributes: dict[str, Any]
    Item: dict[str, Any]
    Items: list[dict[str, Any]]
    Count: int
    ScannedCount: int
    LastEvaluatedKey: dict[str, Any]
    ResponseMetadata: dict[str, Any]


class BedrockRetrievalResult(TypedDict):
    """Model for a Knowledge Base query result."""

    content: str
    document_id: str
    score: float


class BedrockRAGResult(TypedDict):
    """Model for a RAG generation result."""

    answer: str
    sources: list[str]
    inference_profile_id: str
