"""Tests for ads.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListAds:
    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_returns_ads(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        mock_row = MagicMock()
        mock_row.ad_group_ad.ad.id = 333
        mock_row.ad_group_ad.ad.type_.name = "RESPONSIVE_SEARCH_AD"
        mock_row.ad_group_ad.status.name = "ENABLED"
        mock_row.ad_group_ad.ad_strength.name = "GOOD"
        mock_row.ad_group_ad.ad.final_urls = ["https://example.com"]
        mock_row.ad_group_ad.ad.responsive_search_ad.headlines = []
        mock_row.ad_group_ad.ad.responsive_search_ad.descriptions = []
        mock_row.ad_group.id = 222
        mock_row.campaign.id = 111

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_ads("123"))
        assert result["data"]["count"] == 1

    @patch("mcp_google_ads.tools.ads.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ads import list_ads

        result = assert_error(list_ads(""))
        assert "Failed" in result["error"]
