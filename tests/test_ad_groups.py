"""Tests for ad_groups.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListAdGroups:
    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_returns_ad_groups(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        mock_row = MagicMock()
        mock_row.ad_group.id = 222
        mock_row.ad_group.name = "Ad Group 1"
        mock_row.ad_group.status.name = "ENABLED"
        mock_row.ad_group.type_.name = "SEARCH_STANDARD"
        mock_row.ad_group.cpc_bid_micros = 1_500_000
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Campaign 1"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_ad_groups("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["ad_groups"][0]["name"] == "Ad Group 1"

    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        result = assert_error(list_ad_groups(""))
        assert "Failed" in result["error"]
