"""
Adapters module for AWS services.
"""

from lib.adapters.bedrock_client import BedrockClient
from lib.adapters.dynamodb_client import DynamoDBClient

__all__ = ["BedrockClient", "DynamoDBClient"]
