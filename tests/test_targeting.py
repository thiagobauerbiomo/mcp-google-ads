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

    def test_rejects_invalid_device_type(self):
        from mcp_google_ads.tools.targeting import set_device_bid_adjustment

        result = assert_error(set_device_bid_adjustment("123", "111", "DROP TABLE", 1.2))
        assert "Failed to set device bid adjustment" in result["error"]

    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", side_effect=Exception("connection error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.targeting import set_device_bid_adjustment

        result = assert_error(set_device_bid_adjustment("123", "111", "MOBILE", 1.0))
        assert "Failed to set device bid adjustment" in result["error"]


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

    @patch("mcp_google_ads.tools.targeting.get_service")
    @patch("mcp_google_ads.tools.targeting.get_client")
    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", return_value="123")
    def test_with_bid_modifier(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.targeting import create_ad_schedule

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignCriteria/111~999")]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_ad_schedule("123", "111", "MONDAY", 9, 17, bid_modifier=1.5))
        assert "MONDAY" in result["message"]

    def test_rejects_invalid_day(self):
        from mcp_google_ads.tools.targeting import create_ad_schedule

        result = assert_error(create_ad_schedule("123", "111", "INVALID", 9, 17))
        assert "Failed to create ad schedule" in result["error"]

    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", side_effect=Exception("api error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.targeting import create_ad_schedule

        result = assert_error(create_ad_schedule("123", "111", "MONDAY", 9, 17))
        assert "Failed to create ad schedule" in result["error"]


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

    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", side_effect=Exception("search error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.targeting import list_ad_schedules

        result = assert_error(list_ad_schedules("123", "111"))
        assert "Failed to list ad schedules" in result["error"]


class TestRemoveAdSchedule:
    @patch("mcp_google_ads.tools.targeting.get_service")
    @patch("mcp_google_ads.tools.targeting.get_client")
    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", return_value="123")
    def test_removes_schedule(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.targeting import remove_ad_schedule

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignCriteria/111~999")]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_ad_schedule("123", "111", "999"))
        assert "removed" in result["message"]
        assert "999" in result["message"]

    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", side_effect=Exception("remove error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.targeting import remove_ad_schedule

        result = assert_error(remove_ad_schedule("123", "111", "999"))
        assert "Failed to remove ad schedule" in result["error"]


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

    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", side_effect=Exception("geo error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.targeting import exclude_geo_location

        result = assert_error(exclude_geo_location("123", "111", "2076"))
        assert "Failed to exclude geo location" in result["error"]


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

    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", side_effect=Exception("language error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.targeting import add_language_targeting

        result = assert_error(add_language_targeting("123", "111", "1014"))
        assert "Failed to add language targeting" in result["error"]


class TestRemoveLanguageTargeting:
    @patch("mcp_google_ads.tools.targeting.get_service")
    @patch("mcp_google_ads.tools.targeting.get_client")
    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", return_value="123")
    def test_removes_language(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.targeting import remove_language_targeting

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignCriteria/111~5555")]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_language_targeting("123", "111", "5555"))
        assert "removed" in result["message"]
        assert "5555" in result["message"]

    @patch("mcp_google_ads.tools.targeting.resolve_customer_id", side_effect=Exception("remove lang error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.targeting import remove_language_targeting

        result = assert_error(remove_language_targeting("123", "111", "5555"))
        assert "Failed to remove language targeting" in result["error"]
