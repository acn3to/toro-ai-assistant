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


@runtime_checkable
class DynamoDBTable(Protocol):
    """Protocol for representing a DynamoDB table."""

    def put_item(self, **kwargs: Any) -> dict[str, Any]:
        """Puts an item in the table."""
        ...

    def get_item(self, **kwargs: Any) -> dict[str, Any]:
        """Gets an item from the table."""
        ...

    def update_item(self, **kwargs: Any) -> dict[str, Any]:
        """Updates an item in the table."""
        ...

    def delete_item(self, **kwargs: Any) -> dict[str, Any]:
        """Deletes an item from the table."""
        ...

    def scan(self, **kwargs: Any) -> dict[str, Any]:
        """Scans the table."""
        ...


@runtime_checkable
class APIGatewayManagementClient(Protocol):
    """Protocol for representing an API Gateway Management client."""

    def post_to_connection(self, **kwargs: Any) -> dict[str, Any]:
        """Posts a message to a connection."""
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
