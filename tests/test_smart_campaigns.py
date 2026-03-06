"""Tests for smart_campaigns.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestSuggestSmartCampaignBudget:
    @patch("mcp_google_ads.tools.smart_campaigns.get_service")
    @patch("mcp_google_ads.tools.smart_campaigns.get_client")
    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", return_value="123")
    def test_returns_budget_suggestions(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.smart_campaigns import suggest_smart_campaign_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.low.daily_amount_micros = 5_000_000
        mock_response.recommended.daily_amount_micros = 10_000_000
        mock_response.high.daily_amount_micros = 20_000_000

        mock_service = MagicMock()
        mock_service.suggest_smart_campaign_budget_options.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(suggest_smart_campaign_budget("123", "My Biz", "https://example.com"))
        assert result["data"]["low"]["daily_amount"] == 5.0
        assert result["data"]["recommended"]["daily_amount"] == 10.0
        assert result["data"]["high"]["daily_amount"] == 20.0
        assert result["data"]["low"]["daily_amount_micros"] == 5_000_000

    @patch("mcp_google_ads.tools.smart_campaigns.get_service")
    @patch("mcp_google_ads.tools.smart_campaigns.get_client")
    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", return_value="123")
    def test_with_location_ids(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.smart_campaigns import suggest_smart_campaign_budget

        client = MagicMock()
        suggestion_info = MagicMock()
        suggestion_info.location_list.locations = []
        client.get_type.return_value = suggestion_info
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.low.daily_amount_micros = 3_000_000
        mock_response.recommended.daily_amount_micros = 7_000_000
        mock_response.high.daily_amount_micros = 15_000_000

        mock_service = MagicMock()
        mock_service.suggest_smart_campaign_budget_options.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            suggest_smart_campaign_budget("123", "My Biz", "https://example.com", location_ids=["1001566", "1031586"])
        )
        assert "recommended" in result["data"]
        # get_type called for SmartCampaignSuggestionInfo and LocationInfo (x2)
        assert client.get_type.call_count >= 2

    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.smart_campaigns import suggest_smart_campaign_budget

        result = assert_error(suggest_smart_campaign_budget("", "Biz", "https://example.com"))
        assert "Failed to suggest smart campaign budget" in result["error"]

    @patch("mcp_google_ads.tools.smart_campaigns.get_service")
    @patch("mcp_google_ads.tools.smart_campaigns.get_client")
    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", return_value="123")
    def test_rejects_invalid_location_id(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.smart_campaigns import suggest_smart_campaign_budget

        client = MagicMock()
        suggestion_info = MagicMock()
        suggestion_info.location_list.locations = []
        client.get_type.return_value = suggestion_info
        mock_client.return_value = client

        result = assert_error(
            suggest_smart_campaign_budget("123", "Biz", "https://example.com", location_ids=["abc"])
        )
        assert "Failed to suggest smart campaign budget" in result["error"]


class TestSuggestSmartCampaignAd:
    @patch("mcp_google_ads.tools.smart_campaigns.get_service")
    @patch("mcp_google_ads.tools.smart_campaigns.get_client")
    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", return_value="123")
    def test_returns_ad_suggestions(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.smart_campaigns import suggest_smart_campaign_ad

        client = MagicMock()
        mock_client.return_value = client

        headline1 = MagicMock()
        headline1.text = "Best Business Ever"
        headline2 = MagicMock()
        headline2.text = "Call Us Today"

        desc1 = MagicMock()
        desc1.text = "We provide the best services in the area."

        mock_response = MagicMock()
        mock_response.ad_info.headlines = [headline1, headline2]
        mock_response.ad_info.descriptions = [desc1]

        mock_service = MagicMock()
        mock_service.suggest_smart_campaign_ad.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(suggest_smart_campaign_ad("123", "My Biz", "https://example.com"))
        assert result["data"]["headline_count"] == 2
        assert result["data"]["description_count"] == 1
        assert result["data"]["headlines"][0] == "Best Business Ever"
        assert result["data"]["descriptions"][0] == "We provide the best services in the area."

    @patch("mcp_google_ads.tools.smart_campaigns.get_service")
    @patch("mcp_google_ads.tools.smart_campaigns.get_client")
    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", return_value="123")
    def test_empty_suggestions(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.smart_campaigns import suggest_smart_campaign_ad

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.ad_info.headlines = []
        mock_response.ad_info.descriptions = []

        mock_service = MagicMock()
        mock_service.suggest_smart_campaign_ad.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(suggest_smart_campaign_ad("123", "My Biz", "https://example.com"))
        assert result["data"]["headline_count"] == 0
        assert result["data"]["description_count"] == 0

    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", side_effect=Exception("Auth error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.smart_campaigns import suggest_smart_campaign_ad

        result = assert_error(suggest_smart_campaign_ad("", "Biz", "https://example.com"))
        assert "Failed to suggest smart campaign ad" in result["error"]


class TestSuggestKeywordThemes:
    @patch("mcp_google_ads.tools.smart_campaigns.get_service")
    @patch("mcp_google_ads.tools.smart_campaigns.get_client")
    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", return_value="123")
    def test_returns_keyword_themes(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.smart_campaigns import suggest_keyword_themes

        client = MagicMock()
        mock_client.return_value = client

        theme1 = MagicMock()
        theme1.resource_name = "keywordThemeConstants/100"
        theme1.display_name = "Tarot Online"

        theme2 = MagicMock()
        theme2.resource_name = "keywordThemeConstants/200"
        theme2.display_name = "Cartomante"

        mock_response = MagicMock()
        mock_response.keyword_theme_constants = [theme1, theme2]

        mock_service = MagicMock()
        mock_service.suggest_keyword_theme_constants.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(suggest_keyword_themes("123", "My Biz", "https://example.com"))
        assert result["data"]["count"] == 2
        assert result["data"]["keyword_themes"][0]["display_name"] == "Tarot Online"
        assert result["data"]["keyword_themes"][1]["resource_name"] == "keywordThemeConstants/200"

    @patch("mcp_google_ads.tools.smart_campaigns.get_service")
    @patch("mcp_google_ads.tools.smart_campaigns.get_client")
    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", return_value="123")
    def test_empty_themes(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.smart_campaigns import suggest_keyword_themes

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.keyword_theme_constants = []

        mock_service = MagicMock()
        mock_service.suggest_keyword_theme_constants.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(suggest_keyword_themes("123", "My Biz", "https://example.com"))
        assert result["data"]["count"] == 0
        assert result["data"]["keyword_themes"] == []

    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", side_effect=Exception("Fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.smart_campaigns import suggest_keyword_themes

        result = assert_error(suggest_keyword_themes("", "Biz", "https://example.com"))
        assert "Failed to suggest keyword themes" in result["error"]


class TestListSmartCampaignSettings:
    @patch("mcp_google_ads.tools.smart_campaigns.get_service")
    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", return_value="123")
    def test_returns_settings(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.smart_campaigns import list_smart_campaign_settings

        mock_row = MagicMock()
        mock_row.smart_campaign_setting.resource_name = "customers/123/smartCampaignSettings/456"
        mock_row.smart_campaign_setting.campaign = "customers/123/campaigns/456"
        mock_row.smart_campaign_setting.final_url = "https://example.com"
        mock_row.smart_campaign_setting.phone_number.country_code = "BR"
        mock_row.smart_campaign_setting.phone_number.phone_number = "+5531999999999"
        mock_row.smart_campaign_setting.advertising_language_code = "pt"
        mock_row.smart_campaign_setting.business_name = "My Business"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_smart_campaign_settings("123"))
        assert result["data"]["count"] == 1
        settings = result["data"]["settings"][0]
        assert settings["final_url"] == "https://example.com"
        assert settings["business_name"] == "My Business"
        assert settings["phone_country_code"] == "BR"
        assert settings["campaign"] == "customers/123/campaigns/456"

    @patch("mcp_google_ads.tools.smart_campaigns.get_service")
    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", return_value="123")
    def test_empty_results(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.smart_campaigns import list_smart_campaign_settings

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_smart_campaign_settings("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["settings"] == []

    @patch("mcp_google_ads.tools.smart_campaigns.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.smart_campaigns import list_smart_campaign_settings

        result = assert_error(list_smart_campaign_settings(""))
        assert "Failed to list smart campaign settings" in result["error"]
