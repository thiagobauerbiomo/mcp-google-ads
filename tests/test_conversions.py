"""Tests for conversions.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListConversionActions:
    @patch("mcp_google_ads.tools.conversions.get_service")
    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", return_value="123")
    def test_returns_actions(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.conversions import list_conversion_actions

        mock_row = MagicMock()
        mock_row.conversion_action.id = 666
        mock_row.conversion_action.name = "Purchase"
        mock_row.conversion_action.type_.name = "WEBPAGE"
        mock_row.conversion_action.category.name = "PURCHASE"
        mock_row.conversion_action.status.name = "ENABLED"
        mock_row.conversion_action.counting_type.name = "ONE_PER_CLICK"
        mock_row.conversion_action.value_settings.default_value = 50.0
        mock_row.conversion_action.value_settings.always_use_default_value = False
        mock_row.conversion_action.attribution_model_settings.attribution_model.name = "GOOGLE_ADS_LAST_CLICK"
        mock_row.conversion_action.click_through_lookback_window_days = 30
        mock_row.conversion_action.include_in_conversions_metric = True

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_conversion_actions("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["conversion_actions"][0]["name"] == "Purchase"

    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.conversions import list_conversion_actions

        result = assert_error(list_conversion_actions(""))
        assert "Failed" in result["error"]


class TestGetConversionAction:
    @patch("mcp_google_ads.tools.conversions.get_service")
    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", return_value="123")
    def test_returns_action_details(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.conversions import get_conversion_action

        mock_row = MagicMock()
        mock_row.conversion_action.id = 666
        mock_row.conversion_action.name = "Purchase"
        mock_row.conversion_action.type_.name = "WEBPAGE"
        mock_row.conversion_action.category.name = "PURCHASE"
        mock_row.conversion_action.status.name = "ENABLED"
        mock_row.conversion_action.counting_type.name = "ONE_PER_CLICK"
        mock_row.conversion_action.value_settings.default_value = 50.0
        mock_row.conversion_action.value_settings.always_use_default_value = False
        mock_row.conversion_action.attribution_model_settings.attribution_model.name = "GOOGLE_ADS_LAST_CLICK"
        mock_row.conversion_action.click_through_lookback_window_days = 30
        mock_row.conversion_action.view_through_lookback_window_days = 7
        mock_row.conversion_action.include_in_conversions_metric = True

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter([mock_row]))
        mock_service.search.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(get_conversion_action("123", "666"))
        assert result["data"]["conversion_action_id"] == "666"
        assert result["data"]["name"] == "Purchase"
        assert result["data"]["type"] == "WEBPAGE"
        assert result["data"]["click_lookback_days"] == 30
        assert result["data"]["view_lookback_days"] == 7

    @patch("mcp_google_ads.tools.conversions.get_service")
    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", return_value="123")
    def test_not_found(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.conversions import get_conversion_action

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter([]))
        mock_service.search.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_error(get_conversion_action("123", "999"))
        assert "not found" in result["error"]

    def test_rejects_invalid_id(self):
        from mcp_google_ads.tools.conversions import get_conversion_action

        result = assert_error(get_conversion_action("123", "abc_invalid"))
        assert "Failed to get conversion action" in result["error"]


class TestCreateConversionAction:
    @patch("mcp_google_ads.tools.conversions.get_service")
    @patch("mcp_google_ads.tools.conversions.get_client")
    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", return_value="123")
    def test_creates_action(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.conversions import create_conversion_action

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/conversionActions/666")]
        mock_service.mutate_conversion_actions.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_conversion_action("123", "Purchase", "WEBPAGE", "PURCHASE"))
        assert result["data"]["conversion_action_id"] == "666"


class TestUpdateConversionAction:
    @patch("mcp_google_ads.tools.conversions.get_service")
    @patch("mcp_google_ads.tools.conversions.get_client")
    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", return_value="123")
    def test_updates_action_name(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.conversions import update_conversion_action

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/conversionActions/666")]
        mock_service = MagicMock()
        mock_service.mutate_conversion_actions.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            update_conversion_action("123", "666", name="Updated Purchase")
        )
        assert result["data"]["resource_name"] == "customers/123/conversionActions/666"
        assert "666" in result["message"]

    @patch("mcp_google_ads.tools.conversions.get_service")
    @patch("mcp_google_ads.tools.conversions.get_client")
    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", return_value="123")
    def test_updates_multiple_fields(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.conversions import update_conversion_action

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/conversionActions/666")]
        mock_service = MagicMock()
        mock_service.mutate_conversion_actions.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            update_conversion_action(
                "123", "666",
                name="New Name",
                status="PAUSED",
                default_value=99.5,
                counting_type="MANY_PER_CLICK",
            )
        )
        assert result["data"]["resource_name"] == "customers/123/conversionActions/666"

    @patch("mcp_google_ads.tools.conversions.get_service")
    @patch("mcp_google_ads.tools.conversions.get_client")
    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", return_value="123")
    def test_rejects_no_fields(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.conversions import update_conversion_action

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(
            update_conversion_action("123", "666")
        )
        assert "No fields to update" in result["error"]


class TestImportOfflineConversions:
    @patch("mcp_google_ads.tools.conversions.get_service")
    @patch("mcp_google_ads.tools.conversions.get_client")
    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", return_value="123")
    def test_uploads_conversions(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.conversions import import_offline_conversions

        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.gclid = "abc123"
        mock_result.conversion_action = "customers/123/conversionActions/666"
        mock_result.conversion_date_time = "2024-01-15 14:30:00-03:00"
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        mock_response.partial_failure_error = None
        mock_service.upload_click_conversions.return_value = mock_response
        mock_get_service.return_value = mock_service

        conversions = [{"gclid": "abc123", "conversion_action_id": "666", "conversion_date_time": "2024-01-15 14:30:00-03:00"}]
        result = assert_success(import_offline_conversions("123", conversions))
        assert result["data"]["uploaded"] == 1

    def test_rejects_batch_too_large(self):
        from mcp_google_ads.tools.conversions import import_offline_conversions

        conversions = [
            {"gclid": f"gclid_{i}", "conversion_action_id": "666", "conversion_date_time": "2024-01-15 14:30:00-03:00"}
            for i in range(2001)
        ]
        result = assert_error(import_offline_conversions("123", conversions))
        assert "2000" in result["error"]

    def test_rejects_missing_required_fields(self):
        from mcp_google_ads.tools.conversions import import_offline_conversions

        conversions = [{"gclid": "abc123"}]  # faltando conversion_action_id e conversion_date_time
        result = assert_error(import_offline_conversions("123", conversions))
        assert "missing required field" in result["error"]

    @patch("mcp_google_ads.tools.conversions.get_service")
    @patch("mcp_google_ads.tools.conversions.get_client")
    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", return_value="123")
    def test_uploads_with_partial_failure(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.conversions import import_offline_conversions

        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.gclid = "abc123"
        mock_result.conversion_action = "customers/123/conversionActions/666"
        mock_result.conversion_date_time = "2024-01-15 14:30:00-03:00"
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        mock_response.partial_failure_error = MagicMock()
        mock_response.partial_failure_error.__str__ = MagicMock(return_value="Some conversion failed")
        mock_service.upload_click_conversions.return_value = mock_response
        mock_get_service.return_value = mock_service

        conversions = [
            {"gclid": "abc123", "conversion_action_id": "666", "conversion_date_time": "2024-01-15 14:30:00-03:00"},
        ]
        result = assert_success(import_offline_conversions("123", conversions))
        assert result["data"]["uploaded"] == 1
        assert result["data"]["partial_failure_error"] is not None


class TestListConversionGoals:
    @patch("mcp_google_ads.tools.conversions.get_service")
    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", return_value="123")
    def test_returns_goals(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.conversions import list_conversion_goals

        mock_row = MagicMock()
        mock_row.customer_conversion_goal.category.name = "PURCHASE"
        mock_row.customer_conversion_goal.origin.name = "WEBSITE"
        mock_row.customer_conversion_goal.biddable = True

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter([mock_row]))
        mock_service.search.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(list_conversion_goals("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["conversion_goals"][0]["category"] == "PURCHASE"
        assert result["data"]["conversion_goals"][0]["origin"] == "WEBSITE"
        assert result["data"]["conversion_goals"][0]["biddable"] is True

    @patch("mcp_google_ads.tools.conversions.get_service")
    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", return_value="123")
    def test_returns_empty_goals(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.conversions import list_conversion_goals

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter([]))
        mock_service.search.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(list_conversion_goals("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["conversion_goals"] == []

    @patch("mcp_google_ads.tools.conversions.resolve_customer_id", side_effect=Exception("Network error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.conversions import list_conversion_goals

        result = assert_error(list_conversion_goals("123"))
        assert "Failed to list conversion goals" in result["error"]
