"""
Unit tests for the module lib/adapters/bedrock_client.py.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from lib.adapters.bedrock_client import BedrockClient


def setup_mock_bedrock_client():
    """Sets up and returns a BedrockClient with a mocked runtime client."""
    mock_bedrock_runtime = MagicMock()
    mock_bedrock_runtime.meta.region_name = "us-east-1"
    return BedrockClient(
        bedrock_agent_runtime_client=mock_bedrock_runtime,
        knowledge_base_id="test-kb-id",
        inference_profile_id="us.amazon.nova-pro-v1:0",
    )


@pytest.fixture
def aws_account_env():
    """Setup AWS account ID environment variable."""
    with patch.dict(os.environ, {"AWS_ACCOUNT_ID": "123456789012"}):
        yield


def test_initialization_with_explicit_params():
    """Tests initializing BedrockClient with explicit parameters."""
    mock_client = MagicMock()
    mock_client.meta.region_name = "us-east-1"

    client = BedrockClient(
        bedrock_agent_runtime_client=mock_client,
        knowledge_base_id="test-kb-id",
        inference_profile_id="test-model",
    )

    assert client.client == mock_client
    assert client.knowledge_base_id == "test-kb-id"
    assert client.inference_profile_id == "test-model"


def test_initialization_with_env_vars():
    """Tests initializing BedrockClient with environment variables."""
    mock_client = MagicMock()
    mock_client.meta.region_name = "us-east-1"

    with patch.dict(
        os.environ,
        {
            "KNOWLEDGE_BASE_ID": "env-kb-id",
            "INFERENCE_PROFILE_ID": "env-model",
        },
    ):
        client = BedrockClient(bedrock_agent_runtime_client=mock_client)

        assert client.knowledge_base_id == "env-kb-id"
        assert client.inference_profile_id == "env-model"


def test_initialization_without_client():
    """Tests that BedrockClient raises ValueError when client is None."""
    with pytest.raises(ValueError, match="bedrock_agent_runtime_client cannot be None"):
        BedrockClient(bedrock_agent_runtime_client=None)


def test_inference_profile_default():
    """Tests that inference_profile_id gets a default value if not provided."""
    mock_client = MagicMock()
    mock_client.meta.region_name = "us-east-1"

    client = BedrockClient(
        bedrock_agent_runtime_client=mock_client,
        knowledge_base_id="test-kb-id",
    )

    assert client.inference_profile_id == "us.amazon.nova-pro-v1:0"


def test_retrieve_and_generate_successful(aws_account_env):
    """Tests the successful execution of retrieve_and_generate."""
    client = setup_mock_bedrock_client()

    mock_response = {
        "output": {"text": "This is the answer"},
    }
    client.client.retrieve_and_generate.return_value = mock_response

    result = client.retrieve_and_generate("What is CDB?")

    assert result["answer"] == "This is the answer"
    assert result["inference_profile_id"] == "us.amazon.nova-pro-v1:0"

    client.client.retrieve_and_generate.assert_called_once()
    call_args = client.client.retrieve_and_generate.call_args[1]
    assert call_args["input"]["text"] == "What is CDB?"
    assert (
        call_args["retrieveAndGenerateConfiguration"]["knowledgeBaseConfiguration"][
            "knowledgeBaseId"
        ]
        == "test-kb-id"
    )


def test_retrieve_and_generate_without_knowledge_base_id(aws_account_env):
    """Tests that retrieve_and_generate raises an error when knowledge_base_id is not set."""
    mock_client = MagicMock()
    mock_client.meta.region_name = "us-east-1"

    client = BedrockClient(
        bedrock_agent_runtime_client=mock_client,
        knowledge_base_id=None,
    )

    with pytest.raises(ValueError, match="Knowledge Base ID not configured"):
        client.retrieve_and_generate("What is CDB?")


def test_retrieve_and_generate_client_error(aws_account_env):
    """Tests error handling when the Bedrock client raises an exception."""
    client = setup_mock_bedrock_client()

    client.client.retrieve_and_generate.side_effect = Exception("Bedrock API error")

    with pytest.raises(Exception, match="Bedrock API error"):
        client.retrieve_and_generate("What is CDB?")


def test_get_inference_profile_arn_with_account_id():
    """Tests the _get_inference_profile_arn method with account ID."""
    client = setup_mock_bedrock_client()

    with patch.dict(os.environ, {"AWS_ACCOUNT_ID": "123456789012"}):
        arn = client._get_inference_profile_arn("us.amazon.nova-pro-v1:0")
        assert (
            arn
            == "arn:aws:bedrock:us-east-1:123456789012:inference-profile/us.amazon.nova-pro-v1:0"
        )


def test_get_inference_profile_arn_existing_arn():
    """Tests that _get_inference_profile_arn returns unchanged ARNs."""
    client = setup_mock_bedrock_client()

    existing_arn = (
        "arn:aws:bedrock:us-east-1:123456789012:inference-profile/us.amazon.nova-pro-v1:0"
    )
    arn = client._get_inference_profile_arn(existing_arn)
    assert arn == existing_arn


def test_get_inference_profile_arn_without_account_id():
    """Tests that _get_inference_profile_arn raises error when AWS_ACCOUNT_ID is not set."""
    client = setup_mock_bedrock_client()

    with (
        patch.dict(os.environ, clear=True),
        pytest.raises(ValueError, match="Environment variable AWS_ACCOUNT_ID is not set"),
    ):
        client._get_inference_profile_arn("us.amazon.nova-pro-v1:0")


def test_get_inference_config():
    """Tests the _get_inference_config method."""
    client = setup_mock_bedrock_client()

    config = client._get_inference_config(2000)

    assert "textInferenceConfig" in config
    assert config["textInferenceConfig"]["maxTokens"] == 2000
    assert config["textInferenceConfig"]["temperature"] == 0.1
    assert config["textInferenceConfig"]["topP"] == 0.9
