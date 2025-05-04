"""
Módulo para operações de banco de dados com DynamoDB.
Contém funções compartilhadas para acesso aos dados.
"""

from datetime import UTC, datetime
import os
from typing import Any, Optional
import uuid

import boto3

dynamodb = boto3.resource("dynamodb")
table_name = os.environ.get("TABLE_NAME", "toro-ai-assistant-questions")
table = dynamodb.Table(table_name)


def save_question(user_id: str, question_text: str) -> dict[str, Any]:
    """
    Salva uma nova pergunta no DynamoDB.

    Args:
        user_id: ID do usuário
        question_text: Texto da pergunta

    Returns:
        Dict com informações da pergunta salva
    """
    question_id = str(uuid.uuid4())
    timestamp = datetime.now(UTC).isoformat()

    item = {
        "PK": f"USER#{user_id}",
        "SK": f"QUESTION#{question_id}",
        "user_id": user_id,
        "question_id": question_id,
        "question": question_text,
        "status": "pending",
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    table.put_item(Item=item)

    return {"user_id": user_id, "question_id": question_id, "status": "pending"}


def get_question(user_id: str, question_id: str) -> Optional[dict[str, Any]]:
    """
    Recupera uma pergunta específica do DynamoDB.

    Args:
        user_id: ID do usuário
        question_id: ID da pergunta

    Returns:
        Dict com os dados da pergunta ou None se não encontrada
    """
    response = table.get_item(Key={"PK": f"USER#{user_id}", "SK": f"QUESTION#{question_id}"})

    return response.get("Item")


def update_question_status(
    user_id: str,
    question_id: str,
    status: str,
    answer: Optional[str] = None,
    error: Optional[str] = None,
) -> dict[str, Any]:
    """
    Atualiza o status de uma pergunta no DynamoDB.

    Args:
        user_id: ID do usuário
        question_id: ID da pergunta
        status: Novo status (pending, processing, completed, error)
        answer: Resposta (quando status=completed)
        error: Mensagem de erro (quando status=error)

    Returns:
        Dict com resultado da atualização
    """
    timestamp = datetime.now(UTC).isoformat()

    update_expression = "SET #status = :status, updated_at = :updated_at"
    expression_attribute_names = {"#status": "status"}
    expression_attribute_values = {":status": status, ":updated_at": timestamp}

    if answer is not None:
        update_expression += ", answer = :answer"
        expression_attribute_values[":answer"] = answer

    if error is not None:
        update_expression += ", error = :error"
        expression_attribute_values[":error"] = error

    response = table.update_item(
        Key={"PK": f"USER#{user_id}", "SK": f"QUESTION#{question_id}"},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW",
    )

    return response.get("Attributes", {})
