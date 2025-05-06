"""
Module `bedrock_client`.

Provides the `BedrockClient` class, which configures the Bedrock Agent Runtime client,
retrieves documents from a Knowledge Base, and generates responses via RAG based on context.
"""

import os
from typing import Any, Optional

from aws_lambda_powertools import Logger
from botocore.client import BaseClient

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
            "INFERENCE_PROFILE_ID", "us.amazon.nova-pro-v1:0"
        )

        logger.info(
            f"BedrockClient initialized: inference_profile_id={self.inference_profile_id}, kb_id={self.knowledge_base_id}"
        )

    def retrieve_and_generate(self, query: str, max_tokens: int = 4096) -> dict[str, Any]:
        """
        Retrieves relevant documents and generates a response based on them.

        Args:
            query (str): User's question.
            max_tokens (int): Token limit for the response.

        Returns:
            dict: Contains 'answer', 'sources', 'inference_profile_id', and 'found_relevant_docs'.

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
                            "vectorSearchConfiguration": {"numberOfResults": 10}
                        },
                        "generationConfiguration": {
                            "promptTemplate": {
                                "textPromptTemplate": (
                                    "Você é um assistente de investimentos da Toro especializado em responder "
                                    "perguntas usando SOMENTE as informações fornecidas no contexto abaixo. "
                                    "IMPORTANTE: Você NÃO deve usar seu conhecimento geral ou informações que "
                                    "não estejam explicitamente presentes nos documentos abaixo. "
                                    "Se os documentos não contiverem informações suficientes para responder à pergunta, "
                                    "você deve responder: 'Não tenho informações suficientes "
                                    "para responder a essa pergunta.' "
                                    "Suas respostas devem ser baseadas EXCLUSIVAMENTE no conteúdo dos documentos, "
                                    "sem adicionar conhecimento externo. "
                                    "\n\n"
                                    "CONTEXTO:"
                                    "\n$search_results$\n\n"
                                    "Pergunta: $query$\n\n"
                                    "Resposta (usando APENAS as informações do CONTEXTO acima):"
                                )
                            },
                            "inferenceConfig": inference_config,
                        },
                    },
                },
            )

            logger.info("Response received from Bedrock")

            answer = response["output"]["text"]
            sources = []

            citations = response.get("citations", [])
            logger.info(f"Number of citations received: {len(citations)}")

            for cite in citations:
                retrieved_refs = cite.get("retrievedReferences", [])

                if isinstance(retrieved_refs, dict):
                    uri = retrieved_refs.get("location", {}).get("s3Location", {}).get("uri", "")
                    text = retrieved_refs.get("content", {}).get("text", "")
                    if uri:
                        sources.append({"document_id": uri, "excerpt": text})

                elif isinstance(retrieved_refs, list):
                    for ref in retrieved_refs:
                        if isinstance(ref, dict):
                            uri = ref.get("location", {}).get("s3Location", {}).get("uri", "")
                            text = ref.get("content", {}).get("text", "")
                            if uri:
                                sources.append({"document_id": uri, "excerpt": text})

            if not sources:
                logger.warning("No sources extracted from citations")
            else:
                logger.info(f"Extracted {len(sources)} sources from citations")

            found_relevant_docs = len(sources) > 0

            return {
                "answer": answer,
                "sources": sources,
                "inference_profile_id": self.inference_profile_id,
                "found_relevant_docs": found_relevant_docs,
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
        return {"textInferenceConfig": {"maxTokens": max_tokens, "temperature": 0.1, "topP": 0.9}}
