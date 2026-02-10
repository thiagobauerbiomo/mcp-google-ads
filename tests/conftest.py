"""Shared fixtures for Google Ads MCP tests."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def mock_config():
    """Mock GoogleAdsConfig with test values."""
    from mcp_google_ads.config import GoogleAdsConfig

    return GoogleAdsConfig(
        client_id="test-client-id",
        client_secret="test-client-secret",
        developer_token="test-dev-token",
        refresh_token="test-refresh-token",
        login_customer_id="1234567890",
        default_customer_id="9876543210",
    )


@pytest.fixture()
def mock_google_ads_client():
    """Mock GoogleAdsClient with common methods."""
    client = MagicMock()

    # Mock enums
    client.enums.CampaignStatusEnum.PAUSED = 2
    client.enums.CampaignStatusEnum.ENABLED = 1
    client.enums.CampaignStatusEnum.REMOVED = 3
    client.enums.AdGroupStatusEnum.PAUSED = 2
    client.enums.AdGroupStatusEnum.ENABLED = 1
    client.enums.AdGroupCriterionStatusEnum.ENABLED = 1
    client.enums.AdGroupCriterionStatusEnum.PAUSED = 2
    client.enums.KeywordMatchTypeEnum.BROAD = 1
    client.enums.KeywordMatchTypeEnum.PHRASE = 2
    client.enums.KeywordMatchTypeEnum.EXACT = 3
    client.enums.BudgetDeliveryMethodEnum.STANDARD = 1
    client.enums.SharedSetTypeEnum.NEGATIVE_KEYWORDS = 1
    client.enums.ConversionActionStatusEnum.ENABLED = 1
    client.enums.ConversionActionCountingTypeEnum.ONE_PER_CLICK = 1
    client.enums.AssetFieldTypeEnum.SITELINK = 2
    client.enums.AssetFieldTypeEnum.CALLOUT = 3
    client.enums.DayOfWeekEnum.MONDAY = 1
    client.enums.MinuteOfHourEnum.ZERO = 0
    client.enums.DeviceEnum.MOBILE = 1

    # Mock get_type to return MagicMock with nested attrs
    def mock_get_type(type_name):
        mock_type = MagicMock()
        mock_type.create = MagicMock()
        mock_type.update = MagicMock()
        mock_type.remove = ""
        mock_type.update_mask = MagicMock()
        return mock_type

    client.get_type = mock_get_type
    client.copy_from = MagicMock()

    return client


@pytest.fixture()
def mock_google_ads_service():
    """Mock GoogleAdsService for search queries."""
    service = MagicMock()
    service.search.return_value = []
    return service


@pytest.fixture()
def mock_mutate_response():
    """Mock mutate response with a resource name."""
    response = MagicMock()
    result = MagicMock()
    result.resource_name = "customers/1234567890/campaigns/111"
    response.results = [result]
    return response


def parse_response(response_str: str) -> dict:
    """Parse a JSON response string into a dict."""
    return json.loads(response_str)


def assert_success(response_str: str) -> dict:
    """Assert the response is a success and return parsed data."""
    data = parse_response(response_str)
    assert data["status"] == "success", f"Expected success, got: {data}"
    return data


def assert_error(response_str: str) -> dict:
    """Assert the response is an error and return parsed data."""
    data = parse_response(response_str)
    assert data["status"] == "error", f"Expected error, got: {data}"
    return data
