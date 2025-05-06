"""
Module `bedrock_client`.

Provides the `BedrockClient` class, which configures the Bedrock Agent Runtime client,
retrieves documents from a Knowledge Base, and generates responses via RAG based on context.
"""

import os
from typing import Any, Optional

from aws_lambda_powertools import Logger
from botocore.client import BaseClient

from lib.core.constants import (
    DEFAULT_INFERENCE_PROFILE_ID,
    DEFAULT_MAX_TOKENS,
    DEFAULT_PROMPT_TEMPLATE,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_VECTOR_SEARCH_RESULTS,
)

logger = Logger()


class BedrockClient:
    """
    Client to interact with AWS Bedrock, performing Retrieval-Augmented Generation (RAG).
    """

    def __init__(
        self,
        bedrock_agent_runtime_client: BaseClient,
        knowledge_base_id: Optional[str] = None,
        inference_profile_id: Optional[str] = None,
    ):
        """
        Initializes the Bedrock client.

        Args:
            bedrock_agent_runtime_client (BaseClient): Instance of the Bedrock Agent runtime.
            knowledge_base_id (Optional[str]): Knowledge Base ID (or ENV `KNOWLEDGE_BASE_ID`).
            inference_profile_id (Optional[str]): Inference profile ID (or ENV `INFERENCE_PROFILE_ID`).

        Raises:
            ValueError: If `bedrock_agent_runtime_client` is None.
        """
        if bedrock_agent_runtime_client is None:
            raise ValueError("bedrock_agent_runtime_client cannot be None")

        self.client = bedrock_agent_runtime_client
        self.knowledge_base_id = knowledge_base_id or os.environ.get("KNOWLEDGE_BASE_ID")
        self.inference_profile_id = inference_profile_id or os.environ.get(
            "INFERENCE_PROFILE_ID", DEFAULT_INFERENCE_PROFILE_ID
        )

        logger.info(
            f"BedrockClient initialized: inference_profile_id={self.inference_profile_id}, kb_id={self.knowledge_base_id}"
        )

    def retrieve_and_generate(
        self, query: str, max_tokens: int = DEFAULT_MAX_TOKENS
    ) -> dict[str, Any]:
        """
        Retrieves relevant documents and generates a response based on them.

        Args:
            query (str): User's question.
            max_tokens (int): Token limit for the response.

        Returns:
            dict: Contains 'answer' and 'inference_profile_id'.

        Raises:
            ValueError: If `knowledge_base_id` is not defined.
            Exception: On failure when calling Bedrock.
        """
        if not self.knowledge_base_id:
            logger.error("Knowledge Base ID not configured.")
            raise ValueError("Knowledge Base ID not configured. Set KNOWLEDGE_BASE_ID.")

        profile_arn = self._get_inference_profile_arn(self.inference_profile_id)
        inference_config = self._get_inference_config(max_tokens)

        try:
            response = self.client.retrieve_and_generate(
                input={"text": query},
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self.knowledge_base_id,
                        "modelArn": profile_arn,
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "numberOfResults": DEFAULT_VECTOR_SEARCH_RESULTS
                            }
                        },
                        "generationConfiguration": {
                            "promptTemplate": {"textPromptTemplate": DEFAULT_PROMPT_TEMPLATE},
                            "inferenceConfig": inference_config,
                        },
                    },
                },
            )

            return {
                "answer": response["output"]["text"],
                "inference_profile_id": self.inference_profile_id,
            }

        except Exception as e:
            logger.exception(f"Error generating RAG response: {e}")
            raise

    def _get_inference_profile_arn(self, profile_id: str) -> str:
        """
        Returns the full ARN of the inference profile.
        """
        if profile_id.startswith("arn:"):
            return profile_id

        account = os.environ.get("AWS_ACCOUNT_ID")
        if not account:
            raise ValueError("Environment variable AWS_ACCOUNT_ID is not set.")

        region = self.client.meta.region_name
        return f"arn:aws:bedrock:{region}:{account}:inference-profile/{profile_id}"

    def _get_inference_config(self, max_tokens: int) -> dict[str, Any]:
        """
        Generates the inference configuration for the model.
        """
        return {
            "textInferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": DEFAULT_TEMPERATURE,
                "topP": DEFAULT_TOP_P,
            }
        }
