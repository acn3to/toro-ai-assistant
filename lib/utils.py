"""
Módulo para funções utilitárias compartilhadas por todo o projeto.
"""

import json
import traceback
from typing import Any, Optional


def format_api_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """
    Formata uma resposta para API Gateway.

    Args:
        status_code: Código HTTP de status
        body: Corpo da resposta

    Returns:
        Resposta formatada para API Gateway
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
        "body": json.dumps(body),
    }


def get_traceback() -> str:
    """
    Captura o traceback da exceção atual.

    Returns:
        String com o traceback formatado
    """
    return traceback.format_exc()


def sanitize_log_data(data: Any) -> Any:
    """
    Sanitiza dados para logging, removendo informações sensíveis.

    Args:
        data: Dados a serem sanitizados

    Returns:
        Dados sanitizados
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if key.lower() in ["password", "secret", "token", "key", "credential"]:
                sanitized[key] = "******"
            else:
                sanitized[key] = sanitize_log_data(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    else:
        return data


def validate_question_request(body: dict[str, Any]) -> Optional[dict[str, Any]]:
    """
    Valida uma requisição de pergunta.

    Args:
        body: Corpo da requisição

    Returns:
        None se válido, ou dict com erro se inválido
    """
    if not isinstance(body, dict):
        return {"error": "O corpo da requisição deve ser um objeto JSON"}

    if "user_id" not in body:
        return {"error": "O campo 'user_id' é obrigatório"}

    if "question" not in body:
        return {"error": "O campo 'question' é obrigatório"}

    if not isinstance(body["user_id"], str) or not body["user_id"].strip():
        return {"error": "O campo 'user_id' deve ser uma string não vazia"}

    if not isinstance(body["question"], str) or not body["question"].strip():
        return {"error": "O campo 'question' deve ser uma string não vazia"}

    return None
