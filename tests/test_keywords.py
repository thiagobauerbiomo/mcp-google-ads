"""Tests for keywords.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListKeywords:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_returns_keywords(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.keywords import list_keywords

        mock_row = MagicMock()
        mock_row.ad_group_criterion.criterion_id = 444
        mock_row.ad_group_criterion.keyword.text = "test keyword"
        mock_row.ad_group_criterion.keyword.match_type.name = "BROAD"
        mock_row.ad_group_criterion.status.name = "ENABLED"
        mock_row.ad_group_criterion.cpc_bid_micros = 2_000_000
        mock_row.ad_group_criterion.quality_info.quality_score = 7
        mock_row.ad_group.id = 222
        mock_row.campaign.id = 111

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_keywords("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["keywords"][0]["keyword"] == "test keyword"
        assert result["data"]["keywords"][0]["quality_score"] == 7


class TestAddKeywords:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_adds_keywords(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import add_keywords

        mock_service = MagicMock()
        mock_response = MagicMock()
        r1 = MagicMock()
        r1.resource_name = "customers/123/adGroupCriteria/222~444"
        mock_response.results = [r1]
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        kws = [{"text": "test keyword", "match_type": "BROAD"}]
        result = assert_success(add_keywords("123", "222", kws))
        assert result["data"]["added"] == 1

    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.keywords import add_keywords

        result = assert_error(add_keywords("", "222", []))
        assert "Failed" in result["error"]


class TestRemoveKeywords:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_removes_keywords(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import remove_keywords

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock()]
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_keywords("123", "222", ["444"]))
        assert result["data"]["removed"] == 1
