"""Tests for targeting.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestSetDeviceBidAdjustment:
    @patch("mcp_google_ads.tools.targeting.get_service")
    @patch("mcp_google_ads.tools.targeting.get_client")
    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", return_value="123")
    def test_sets_device_bid(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.targeting import set_device_bid_adjustment

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignCriteria/111~888")]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(set_device_bid_adjustment("123", "111", "MOBILE", 1.2))
        assert "MOBILE" in result["message"]


class TestCreateAdSchedule:
    @patch("mcp_google_ads.tools.targeting.get_service")
    @patch("mcp_google_ads.tools.targeting.get_client")
    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", return_value="123")
    def test_creates_schedule(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.targeting import create_ad_schedule

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignCriteria/111~999")]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_ad_schedule("123", "111", "MONDAY", 9, 17))
        assert "MONDAY" in result["message"]


class TestListAdSchedules:
    @patch("mcp_google_ads.tools.targeting.get_service")
    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", return_value="123")
    def test_returns_schedules(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.targeting import list_ad_schedules

        mock_row = MagicMock()
        mock_row.campaign_criterion.criterion_id = 999
        mock_row.campaign_criterion.ad_schedule.day_of_week.name = "MONDAY"
        mock_row.campaign_criterion.ad_schedule.start_hour = 9
        mock_row.campaign_criterion.ad_schedule.end_hour = 17
        mock_row.campaign_criterion.ad_schedule.start_minute.name = "ZERO"
        mock_row.campaign_criterion.ad_schedule.end_minute.name = "ZERO"
        mock_row.campaign_criterion.bid_modifier = 1.0

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_ad_schedules("123", "111"))
        assert result["data"]["count"] == 1
        assert result["data"]["schedules"][0]["day_of_week"] == "MONDAY"


class TestExcludeGeoLocation:
    @patch("mcp_google_ads.tools.targeting.get_service")
    @patch("mcp_google_ads.tools.targeting.get_client")
    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", return_value="123")
    def test_excludes_location(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.targeting import exclude_geo_location

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignCriteria/111~1234")]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(exclude_geo_location("123", "111", "2076"))
        assert "excluded" in result["message"]


class TestAddLanguageTargeting:
    @patch("mcp_google_ads.tools.targeting.get_service")
    @patch("mcp_google_ads.tools.targeting.get_client")
    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", return_value="123")
    def test_adds_language(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.targeting import add_language_targeting

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignCriteria/111~5555")]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(add_language_targeting("123", "111", "1014"))
        assert "Language" in result["message"]
