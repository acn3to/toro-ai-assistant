"""
Factory module for instantiating AWS service clients.
"""

from lib.factories.aws_clients import (
    get_bedrock_client,
    get_dynamodb_client,
    get_notify_topic,
    get_process_topic,
    get_sns_topic,
)

__all__ = [
    "get_bedrock_client",
    "get_dynamodb_client",
    "get_notify_topic",
    "get_process_topic",
    "get_sns_topic",
]
