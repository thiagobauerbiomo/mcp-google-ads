"""Tests for shared_sets.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListSharedSets:
    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_returns_sets(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.shared_sets import list_shared_sets

        mock_row = MagicMock()
        mock_row.shared_set.id = 777
        mock_row.shared_set.name = "Negative List"
        mock_row.shared_set.type_.name = "NEGATIVE_KEYWORDS"
        mock_row.shared_set.status.name = "ENABLED"
        mock_row.shared_set.member_count = 50

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_shared_sets("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["shared_sets"][0]["name"] == "Negative List"


class TestCreateSharedSet:
    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.get_client")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_creates_set(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.shared_sets import create_shared_set

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/sharedSets/777")]
        mock_service.mutate_shared_sets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_shared_set("123", "New List"))
        assert result["data"]["shared_set_id"] == "777"


class TestLinkSharedSetToCampaign:
    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.get_client")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_links_set(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.shared_sets import link_shared_set_to_campaign

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignSharedSets/111~777")]
        mock_service.mutate_campaign_shared_sets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(link_shared_set_to_campaign("123", "111", "777"))
        assert "linked" in result["message"]
