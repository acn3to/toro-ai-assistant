"""
Module for AWS client factories.
Centralizes instance creation to avoid direct coupling and facilitate testing.
"""

import os
from typing import Any, Optional, cast

import boto3
from botocore.client import BaseClient

from lib.adapters.bedrock_client import BedrockClient
from lib.adapters.dynamodb_client import DynamoDBClient
from lib.core.constants import (
    DEFAULT_NOTIFY_TOPIC,
    DEFAULT_PROCESS_TOPIC,
    DEFAULT_TABLE_NAME,
)
from lib.models.aws import SNSTopic


def get_dynamodb_resource(region_name: Optional[str] = None) -> Any:
    """
    Creates a DynamoDB resource.

    Args:
        region_name: Optional AWS region

    Returns:
        DynamoDB resource
    """
    return boto3.resource("dynamodb", region_name=region_name)


def get_sns_resource(region_name: Optional[str] = None) -> Any:
    """
    Creates an SNS resource.

    Args:
        region_name: Optional AWS region

    Returns:
        SNS resource
    """
    return boto3.resource("sns", region_name=region_name)


def get_bedrock_agent_runtime_client(region_name: Optional[str] = None) -> BaseClient:
    """
    Creates a bedrock-agent-runtime client.

    Args:
        region_name: Optional AWS region

    Returns:
        bedrock-agent-runtime client
    """
    return boto3.client("bedrock-agent-runtime", region_name=region_name)


def get_dynamodb_client(
    table_name: Optional[str] = None, dynamodb_resource: Optional[Any] = None
) -> DynamoDBClient:
    """
    Returns a configured DynamoDBClient instance.

    Args:
        table_name: Optional name of the DynamoDB table
        dynamodb_resource: Optional DynamoDB resource for testing

    Returns:
        DynamoDBClient instance
    """
    table_name = table_name or os.environ.get("TABLE_NAME", DEFAULT_TABLE_NAME)
    resource = dynamodb_resource or get_dynamodb_resource()
    return DynamoDBClient(dynamodb_resource=resource, table_name=table_name)


def get_sns_topic(topic_name: Optional[str] = None, sns_resource: Any = None) -> SNSTopic:
    """
    Returns a configured SNS topic.

    Args:
        topic_name: Optional SNS topic name
        sns_resource: Optional SNS resource for testing

    Returns:
        SNS topic
    """
    sns = sns_resource or get_sns_resource()
    topic_name = topic_name or ""
    return cast(SNSTopic, sns.Topic(topic_name))


def get_process_topic(topic_name: Optional[str] = None, sns_resource: Any = None) -> SNSTopic:
    """
    Returns the processing SNS topic.

    Args:
        topic_name: Optional topic name
        sns_resource: Optional SNS resource for testing

    Returns:
        Processing SNS topic
    """
    topic_name = topic_name or os.environ.get("PROCESS_TOPIC", DEFAULT_PROCESS_TOPIC)
    return get_sns_topic(topic_name, sns_resource)


def get_notify_topic(topic_name: Optional[str] = None, sns_resource: Any = None) -> SNSTopic:
    """
    Returns the notification SNS topic.

    Args:
        topic_name: Optional topic name
        sns_resource: Optional SNS resource for testing

    Returns:
        Notification SNS topic
    """
    topic_name = topic_name or os.environ.get("NOTIFY_TOPIC", DEFAULT_NOTIFY_TOPIC)
    return get_sns_topic(topic_name, sns_resource)


def get_bedrock_client(
    knowledge_base_id: Optional[str] = None,
    inference_profile_id: Optional[str] = None,
    region_name: Optional[str] = None,
    bedrock_agent_runtime_client: Optional[BaseClient] = None,
) -> BedrockClient:
    """
    Returns a configured BedrockClient instance.

    Args:
        knowledge_base_id: Knowledge base ID
        inference_profile_id: ID of the model to be used
        region_name: AWS region
        bedrock_agent_runtime_client: Optional bedrock-agent-runtime client for testing

    Returns:
        BedrockClient instance
    """
    client = bedrock_agent_runtime_client or get_bedrock_agent_runtime_client(region_name)

    return BedrockClient(
        knowledge_base_id=knowledge_base_id or os.environ.get("KNOWLEDGE_BASE_ID"),
        inference_profile_id=inference_profile_id or os.environ.get("INFERENCE_PROFILE_ID"),
        bedrock_agent_runtime_client=client,
    )
