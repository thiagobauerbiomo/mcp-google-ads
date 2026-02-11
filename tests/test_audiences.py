"""Tests for audiences.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListAudienceSegments:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_returns_segments(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.audiences import list_audience_segments

        mock_row = MagicMock()
        mock_row.audience.id = 111
        mock_row.audience.name = "Test Audience"
        mock_row.audience.status.name = "ENABLED"
        mock_row.audience.description = "Test description"
        mock_row.audience.type_.name = "CUSTOM"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_audience_segments("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["segments"][0]["name"] == "Test Audience"

    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_with_type_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.audiences import list_audience_segments

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_audience_segments("123", segment_type="CUSTOM"))
        assert result["data"]["count"] == 0
        call_query = mock_service.search.call_args[1]["query"]
        assert "CUSTOM" in call_query

    def test_rejects_invalid_segment_type(self):
        from mcp_google_ads.tools.audiences import list_audience_segments

        result = assert_error(list_audience_segments("123", segment_type="DROP TABLE"))
        assert "Failed to list audience segments" in result["error"]


class TestListCampaignTargeting:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_returns_criteria(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.audiences import list_campaign_targeting

        mock_row = MagicMock()
        mock_row.campaign_criterion.criterion_id = 555
        mock_row.campaign_criterion.type_.name = "LOCATION"
        mock_row.campaign_criterion.negative = False
        mock_row.campaign_criterion.bid_modifier = 1.0
        mock_row.campaign_criterion.status.name = "ENABLED"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_targeting("123", "111"))
        assert result["data"]["count"] == 1
        assert result["data"]["criteria"][0]["type"] == "LOCATION"

    def test_rejects_invalid_campaign_id(self):
        from mcp_google_ads.tools.audiences import list_campaign_targeting

        result = assert_error(list_campaign_targeting("123", "abc"))
        assert "Failed to list campaign targeting" in result["error"]

    def test_rejects_invalid_criterion_type(self):
        from mcp_google_ads.tools.audiences import list_campaign_targeting

        result = assert_error(list_campaign_targeting("123", "111", criterion_type="'; DROP TABLE"))
        assert "Failed to list campaign targeting" in result["error"]


class TestAddAudienceTargeting:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_adds_targeting(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import add_audience_targeting

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignCriteria/111~222")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(add_audience_targeting("123", "111", "222"))
        assert "resource_name" in result["data"]

    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_with_bid_modifier(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import add_audience_targeting

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignCriteria/111~222")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(add_audience_targeting("123", "111", "222", bid_modifier=1.2))
        assert "resource_name" in result["data"]
        # Verifica que bid_modifier foi atribuído no critério
        operation = client.get_type.return_value
        criterion = operation.create
        assert criterion.bid_modifier == 1.2

    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.audiences import add_audience_targeting

        result = assert_error(add_audience_targeting("", "111", "222"))
        assert "Failed to add audience targeting" in result["error"]


class TestRemoveAudienceTargeting:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_removes_targeting(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import remove_audience_targeting

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignCriteria/111~555")]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_audience_targeting("123", "111", "555"))
        assert result["data"]["resource_name"] == "customers/123/campaignCriteria/111~555"
        assert "removed" in result["message"]

    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", side_effect=Exception("API error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.audiences import remove_audience_targeting

        result = assert_error(remove_audience_targeting("123", "111", "555"))
        assert "Failed to remove audience targeting" in result["error"]


class TestSuggestGeoTargets:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    def test_returns_suggestions(self, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import suggest_geo_targets

        client = MagicMock()
        mock_client.return_value = client

        mock_suggestion = MagicMock()
        geo = mock_suggestion.geo_target_constant
        geo.id = 2076
        geo.name = "São Paulo"
        geo.canonical_name = "São Paulo, SP, Brazil"
        geo.target_type = "City"
        geo.country_code = "BR"
        geo.status.name = "ENABLED"

        mock_response = MagicMock()
        mock_response.geo_target_constant_suggestions = [mock_suggestion]
        mock_service = MagicMock()
        mock_service.suggest_geo_target_constants.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(suggest_geo_targets())
        assert result["data"]["count"] == 1
        suggestion = result["data"]["suggestions"][0]
        assert suggestion["criterion_id"] == "2076"
        assert suggestion["name"] == "São Paulo"
        assert suggestion["country_code"] == "BR"
        assert suggestion["target_type"] == "City"
        assert suggestion["status"] == "ENABLED"

    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    def test_with_query_parameter(self, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import suggest_geo_targets

        client = MagicMock()
        mock_client.return_value = client

        mock_request = MagicMock()
        client.get_type.return_value = mock_request

        mock_response = MagicMock()
        mock_response.geo_target_constant_suggestions = []
        mock_service = MagicMock()
        mock_service.suggest_geo_target_constants.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(suggest_geo_targets(query="Curitiba"))
        assert result["data"]["count"] == 0
        # Verifica que o query foi adicionado ao request
        mock_request.location_names.names.append.assert_called_once_with("Curitiba")

    @patch("mcp_google_ads.tools.audiences.get_client", side_effect=Exception("API error"))
    def test_error_handling(self, mock_client):
        from mcp_google_ads.tools.audiences import suggest_geo_targets

        result = assert_error(suggest_geo_targets())
        assert "Failed to suggest geo targets" in result["error"]


class TestAddAudienceToAdGroup:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_adds_audience_to_ad_group(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import add_audience_to_ad_group

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/adGroupCriteria/444~222")]
        mock_service = MagicMock()
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(add_audience_to_ad_group("123", "444", "222"))
        assert result["data"]["resource_name"] == "customers/123/adGroupCriteria/444~222"
        assert "added" in result["message"]

    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_with_bid_modifier(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import add_audience_to_ad_group

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/adGroupCriteria/444~222")]
        mock_service = MagicMock()
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(add_audience_to_ad_group("123", "444", "222", bid_modifier=1.5))
        assert "resource_name" in result["data"]
        # Verifica que bid_modifier foi atribuído no critério
        operation = client.get_type.return_value
        criterion = operation.create
        assert criterion.bid_modifier == 1.5

    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", side_effect=Exception("API error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.audiences import add_audience_to_ad_group

        result = assert_error(add_audience_to_ad_group("123", "444", "222"))
        assert "Failed to add audience to ad group" in result["error"]


class TestCreateCustomAudience:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import create_custom_audience

        client = MagicMock()
        mock_client.return_value = client
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/customAudiences/999")]
        mock_service = MagicMock()
        mock_service.mutate_custom_audiences.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_custom_audience(
            "123", "Test Audience", "SEARCH",
            [{"type": "KEYWORD", "value": "test"}, {"type": "URL", "value": "https://example.com"}]
        ))
        assert result["data"]["audience_id"] == "999"
        assert "created" in result["message"]

    def test_invalid_type(self):
        from mcp_google_ads.tools.audiences import create_custom_audience

        result = assert_error(create_custom_audience("123", "Test", "DROP TABLE", []))
        assert "Failed to create custom audience" in result["error"]

    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import create_custom_audience

        client = MagicMock()
        mock_client.return_value = client
        mock_service = MagicMock()
        mock_service.mutate_custom_audiences.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(create_custom_audience("123", "Test", "SEARCH", [{"type": "KEYWORD", "value": "t"}]))
        assert "Failed to create custom audience" in result["error"]


class TestAddAudienceSignal:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import add_audience_signal

        client = MagicMock()
        mock_client.return_value = client
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assetGroupSignals/456~789")]
        mock_service = MagicMock()
        mock_service.mutate_asset_group_signals.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(add_audience_signal("123", "456", "789"))
        assert "resource_name" in result["data"]
        assert "added" in result["message"]

    def test_invalid_id(self):
        from mcp_google_ads.tools.audiences import add_audience_signal

        result = assert_error(add_audience_signal("123", "abc", "789"))
        assert "Failed to add audience signal" in result["error"]

    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import add_audience_signal

        client = MagicMock()
        mock_client.return_value = client
        mock_service = MagicMock()
        mock_service.mutate_asset_group_signals.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(add_audience_signal("123", "456", "789"))
        assert "Failed to add audience signal" in result["error"]


class TestAddSearchThemeSignal:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import add_search_theme_signal

        client = MagicMock()
        mock_client.return_value = client
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assetGroupSignals/456~1"), MagicMock(resource_name="customers/123/assetGroupSignals/456~2")]
        mock_service = MagicMock()
        mock_service.mutate_asset_group_signals.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(add_search_theme_signal("123", "456", ["criação de sites", "web design"]))
        assert result["data"]["count"] == 2

    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_exceeds_limit(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import add_search_theme_signal

        result = assert_error(add_search_theme_signal("123", "456", ["t"] * 26))
        assert "Maximum 25" in result["error"]

    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import add_search_theme_signal

        client = MagicMock()
        mock_client.return_value = client
        mock_service = MagicMock()
        mock_service.mutate_asset_group_signals.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(add_search_theme_signal("123", "456", ["test"]))
        assert "Failed to add search theme signals" in result["error"]


class TestListAssetGroupSignals:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_with_audience(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.audiences import list_asset_group_signals

        mock_row = MagicMock()
        mock_row.asset_group_signal.resource_name = "customers/123/assetGroupSignals/456~1"
        mock_row.asset_group_signal.approval_status.name = "APPROVED"
        mock_row.asset_group_signal.audience.audience = "customers/123/audiences/789"
        mock_row.asset_group_signal.search_theme.text = ""

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_asset_group_signals("123", "456"))
        assert result["data"]["count"] == 1
        assert result["data"]["signals"][0]["type"] == "audience"

    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_with_search_theme(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.audiences import list_asset_group_signals

        mock_row = MagicMock()
        mock_row.asset_group_signal.resource_name = "customers/123/assetGroupSignals/456~2"
        mock_row.asset_group_signal.approval_status.name = "APPROVED"
        mock_row.asset_group_signal.audience.audience = ""
        mock_row.asset_group_signal.search_theme.text = "web design"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_asset_group_signals("123", "456"))
        assert result["data"]["signals"][0]["type"] == "search_theme"
        assert result["data"]["signals"][0]["search_theme"] == "web design"

    def test_invalid_id(self):
        from mcp_google_ads.tools.audiences import list_asset_group_signals

        result = assert_error(list_asset_group_signals("123", "abc"))
        assert "Failed to list asset group signals" in result["error"]


class TestRemoveAssetGroupSignal:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import remove_asset_group_signal

        client = MagicMock()
        mock_client.return_value = client
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assetGroupSignals/456~1")]
        mock_service = MagicMock()
        mock_service.mutate_asset_group_signals.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_asset_group_signal("123", "customers/123/assetGroupSignals/456~1"))
        assert "resource_name" in result["data"]

    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", side_effect=Exception("API error"))
    def test_error(self, mock_resolve):
        from mcp_google_ads.tools.audiences import remove_asset_group_signal

        result = assert_error(remove_asset_group_signal("123", "customers/123/assetGroupSignals/456~1"))
        assert "Failed to remove asset group signal" in result["error"]


class TestRemoveAudienceFromAdGroup:
    @patch("mcp_google_ads.tools.audiences.get_service")
    @patch("mcp_google_ads.tools.audiences.get_client")
    @patch("mcp_google_ads.tools.audiences.resolve_customer_id", return_value="123")
    def test_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.audiences import remove_audience_from_ad_group

        client = MagicMock()
        mock_client.return_value = client
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/adGroupCriteria/444~555")]
        mock_service = MagicMock()
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_audience_from_ad_group("123", "444", "555"))
        assert "resource_name" in result["data"]
        assert "removed" in result["message"]

    def test_invalid_id(self):
        from mcp_google_ads.tools.audiences import remove_audience_from_ad_group

        result = assert_error(remove_audience_from_ad_group("123", "abc", "555"))
        assert "Failed to remove audience from ad group" in result["error"]
