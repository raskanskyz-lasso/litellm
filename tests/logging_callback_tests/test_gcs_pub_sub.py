import io
import os
import sys


sys.path.insert(0, os.path.abspath("../.."))

import asyncio
import gzip
import json
import logging
import time
from unittest.mock import AsyncMock, patch

import pytest

import litellm
from litellm import completion
from litellm._logging import verbose_logger
from litellm.integrations.gcs_pubsub.pub_sub import *
from datetime import datetime, timedelta
from litellm.types.utils import (
    StandardLoggingPayload,
    StandardLoggingModelInformation,
    StandardLoggingMetadata,
    StandardLoggingHiddenParams,
)

verbose_logger.setLevel(logging.DEBUG)


def assert_gcs_pubsub_request_matches_expected(
    actual_request_body: dict,
    expected_file_name: str,
):
    """
    Helper function to compare actual GCS PubSub request body with expected JSON file.

    Args:
        actual_request_body (dict): The actual request body received from the API call
        expected_file_name (str): Name of the JSON file containing expected request body
    """
    # Get the current directory and read the expected request body
    pwd = os.path.dirname(os.path.realpath(__file__))
    expected_body_path = os.path.join(pwd, "gcs_pub_sub_body", expected_file_name)

    with open(expected_body_path, "r") as f:
        expected_request_body = json.load(f)

    # Replace dynamic values in actual request body
    time_fields = ["startTime", "endTime", "completionStartTime", "request_id"]
    for field in time_fields:
        if field in actual_request_body:
            actual_request_body[field] = expected_request_body[field]

    # Assert the entire request body matches
    assert (
        actual_request_body == expected_request_body
    ), f"Difference in request bodies: {json.dumps(actual_request_body, indent=2)} != {json.dumps(expected_request_body, indent=2)}"


@pytest.mark.asyncio
async def test_gcs_pub_sub():
    mock_httpx_client = AsyncMock()

    with patch(
        "litellm.llms.custom_httpx.http_handler.AsyncHTTPHandler",
        return_value=mock_httpx_client,
    ):
        gcs_pub_sub_logger = GcsPubSubLogger(flush_interval=1)
        litellm.callbacks = [gcs_pub_sub_logger]

        response = await litellm.acompletion(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, world!"}],
            mock_response="hi",
        )

        await asyncio.sleep(3)  # Wait for async flush

        # Assert httpx post was called
        mock_httpx_client.post.assert_called_once()

        # Get the actual request body from the mock
        actual_request = mock_httpx_client.post.call_args[1]["json"]

        # Extract and decode the base64 encoded message
        encoded_message = actual_request["messages"][0]["data"]
        import base64

        decoded_message = base64.b64decode(encoded_message).decode("utf-8")

        # Parse the JSON string into a dictionary
        actual_request = json.loads(decoded_message)
        print("##########\n")
        print(json.dumps(actual_request, indent=4))
        print("##########\n")
        # Verify the request body matches expected format
        assert_gcs_pubsub_request_matches_expected(
            actual_request, "spend_logs_payload.json"
        )
