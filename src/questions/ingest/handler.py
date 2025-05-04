"""
Função Lambda para ingestão de perguntas.
Recebe perguntas via API Gateway, armazena no DynamoDB e publica evento no SNS
para processamento assíncrono.
"""

from datetime import UTC, datetime
import json
import os
import uuid

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3

dynamodb = boto3.resource("dynamodb")
sns = boto3.resource("sns")
logger = Logger()
tracer = Tracer()

TABLE_NAME = os.environ.get("TABLE_NAME", "toro-ai-assistant-questions")
PROCESS_TOPIC = os.environ.get("PROCESS_TOPIC", "toro-ai-assistant-process-topic")

table = dynamodb.Table(TABLE_NAME)
process_topic = sns.Topic(PROCESS_TOPIC)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """
    Handler principal para ingestão de perguntas.

    Args:
        event: Evento do API Gateway
        context: Contexto da função Lambda

    Returns:
        Resposta formatada para o API Gateway
    """
    try:
        if "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        if "user_id" not in body or "question" not in body:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"success": False, "error": "Campos 'user_id' e 'question' são obrigatórios."}
                ),
            }

        question_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()

        item = {
            "PK": f"USER#{body['user_id']}",
            "SK": f"QUESTION#{question_id}",
            "user_id": body["user_id"],
            "question_id": question_id,
            "question": body["question"],
            "status": "pending",
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        table.put_item(Item=item)

        process_topic.publish(
            Message=json.dumps(
                {
                    "user_id": body["user_id"],
                    "question_id": question_id,
                }
            )
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "success": True,
                    "data": {
                        "user_id": body["user_id"],
                        "question_id": question_id,
                        "status": "pending",
                    },
                }
            ),
        }
    except Exception:
        logger.exception("Erro ao processar requisição")

        return {
            "statusCode": 500,
            "body": json.dumps({"success": False, "error": "Erro interno do servidor."}),
        }
