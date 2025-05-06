"""
Module `dynamodb_client`.

Provides the `DynamoDBClient` class for CRUD operations on DynamoDB.
"""

from datetime import datetime, timezone
import os
from typing import Any, Optional
import uuid

from aws_lambda_powertools import Logger

from lib.core.constants import DEFAULT_TABLE_NAME, STATUS_PENDING
from lib.models.question import DynamoDBKey

logger = Logger()


class DynamoDBClient:
    """
    Client for DynamoDB operations (CRUD for questions).
    """

    def __init__(self, dynamodb_resource: Any, table_name: Optional[str] = None):
        """
        Initializes connection with the DynamoDB table.

        Args:
            dynamodb_resource: DynamoDB resource with Table method.
            table_name (Optional[str]): Table name (or ENV `TABLE_NAME`).

        Raises:
            ValueError: If `dynamodb_resource` is None.
            AttributeError: If `dynamodb_resource` doesn't have a Table method.
        """
        if dynamodb_resource is None:
            raise ValueError("dynamodb_resource cannot be None")

        self.dynamodb = dynamodb_resource
        self.table_name = table_name or os.environ.get("TABLE_NAME", DEFAULT_TABLE_NAME)

        try:
            self.table = self.dynamodb.Table(self.table_name)
        except AttributeError as err:
            raise AttributeError("dynamodb_resource must have a Table method") from err

        logger.info(f"DynamoDBClient initialized: table={self.table_name}")

    def _save_question_internal(self, user_id: str, question_text: str) -> dict[str, Any]:
        """
        Internal logic to save a question in DynamoDB.

        Args:
            user_id: User ID
            question_text: Question text

        Returns:
            Dict with saved question information
        """
        question_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        item = {
            "PK": f"USER#{user_id}",
            "SK": f"QUESTION#{question_id}",
            "user_id": user_id,
            "question_id": question_id,
            "question": question_text,
            "status": STATUS_PENDING,
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        self.table.put_item(Item=item)

        return {"user_id": user_id, "question_id": question_id, "status": STATUS_PENDING}

    def save_question(self, user_id: str, question_text: str) -> dict[str, Any]:
        """
        Saves a new question in DynamoDB.

        Args:
            user_id: User ID
            question_text: Question text

        Returns:
            Dict with saved question information
        """
        result = self._save_question_internal(user_id, question_text)
        logger.info(f"Question saved: user_id={user_id}, question_id={result['question_id']}")
        return result

    def _get_question_internal(self, user_id: str, question_id: str) -> Optional[dict[str, Any]]:
        """
        Internal logic to retrieve a question from DynamoDB.

        Args:
            user_id: User ID
            question_id: Question ID

        Returns:
            Dict with question data or None if not found
        """
        key = self._build_key(user_id, question_id)
        response = self.table.get_item(Key=key)
        return response.get("Item")

    def get_question(self, user_id: str, question_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieves a specific question from DynamoDB.

        Args:
            user_id: User ID
            question_id: Question ID

        Returns:
            Dict with question data or None if not found
        """
        item = self._get_question_internal(user_id, question_id)

        if item:
            logger.info(f"Question retrieved: user_id={user_id}, question_id={question_id}")
        else:
            logger.warning(f"Question not found: user_id={user_id}, question_id={question_id}")

        return item

    def _update_question_status_internal(
        self, user_id: str, question_id: str, status: str
    ) -> dict[str, Any]:
        """
        Internal logic to update the status of a question.

        Args:
            user_id: User ID
            question_id: Question ID
            status: New status

        Returns:
            Dict with update result
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        key = self._build_key(user_id, question_id)

        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_attribute_names = {"#status": "status"}
        expression_attribute_values = {":status": status, ":updated_at": timestamp}

        response = self.table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
        )

        return response.get("Attributes", {})

    def update_question_status(self, user_id: str, question_id: str, status: str) -> dict[str, Any]:
        """
        Updates only the status of a question in DynamoDB.

        Args:
            user_id: User ID
            question_id: Question ID
            status: New status (pending, processing, completed, error)

        Returns:
            Dict with update result
        """
        result = self._update_question_status_internal(user_id, question_id, status)
        logger.info(
            f"Question status updated: user_id={user_id}, question_id={question_id}, status={status}"
        )
        return result

    def _build_update_expression(
        self, update_data: dict[str, Any]
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        """
        Builds the update expression for DynamoDB.

        Args:
            update_data: Dictionary with fields to update

        Returns:
            Tuple with (update_expression, attribute_names, attribute_values)
        """
        update_expression = "SET "
        expression_attribute_names = {}
        expression_attribute_values = {}

        for i, (key, value) in enumerate(update_data.items()):
            placeholder = f":val{i}"
            name_placeholder = f"#attr{i}"

            update_expression += f"{name_placeholder} = {placeholder}"
            if i < len(update_data) - 1:
                update_expression += ", "

            expression_attribute_names[name_placeholder] = key
            expression_attribute_values[placeholder] = value

        return update_expression, expression_attribute_names, expression_attribute_values

    def _update_question_internal(
        self, user_id: str, question_id: str, update_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Internal logic to update a question in DynamoDB.

        Args:
            user_id: User ID
            question_id: Question ID
            update_data: Dictionary with fields to update

        Returns:
            Dict with update result
        """
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        key = self._build_key(user_id, question_id)
        update_expression, expr_attr_names, expr_attr_values = self._build_update_expression(
            update_data
        )

        response = self.table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW",
        )

        return response.get("Attributes", {})

    def update_question(
        self, user_id: str, question_id: str, update_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Updates a question with multiple fields in DynamoDB.

        Args:
            user_id: User ID
            question_id: Question ID
            update_data: Dictionary with fields to update

        Returns:
            Dict with update result
        """
        result = self._update_question_internal(user_id, question_id, update_data)
        logger.info(f"Question updated: user_id={user_id}, question_id={question_id}")
        return result

    def _list_user_questions_internal(
        self, user_id: str, limit: int = 20, next_token: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Internal logic to list user questions.

        Args:
            user_id: User ID
            limit: Max number of items to return
            next_token: Pagination token to continue from

        Returns:
            Dict with items and next pagination token
        """
        params = {
            "KeyConditionExpression": "#pk = :pk_val",
            "ExpressionAttributeNames": {"#pk": "PK"},
            "ExpressionAttributeValues": {":pk_val": f"USER#{user_id}"},
            "Limit": limit,
        }

        if next_token:
            params["ExclusiveStartKey"] = next_token

        response = self.table.query(**params)

        result = {
            "items": response.get("Items", []),
        }

        if "LastEvaluatedKey" in response:
            result["next_token"] = response["LastEvaluatedKey"]

        return result

    def list_user_questions(
        self, user_id: str, limit: int = 20, next_token: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Lists all user questions.

        Args:
            user_id: User ID
            limit: Max number of items to return
            next_token: Pagination token to continue from

        Returns:
            Dict with items and next pagination token
        """
        result = self._list_user_questions_internal(user_id, limit, next_token)
        item_count = len(result.get("items", []))
        logger.info(f"Listing questions: user_id={user_id}, count={item_count}")
        return result

    def _build_key(self, user_id: str, question_id: str) -> DynamoDBKey:
        """
        Builds the primary key for a DynamoDB item.

        Args:
            user_id: User ID
            question_id: Question ID

        Returns:
            Dictionary with the formatted primary key
        """
        return {"PK": f"USER#{user_id}", "SK": f"QUESTION#{question_id}"}
