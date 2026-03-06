"""Tests for new bidding.py tools (data exclusions, seasonality adjustments, accessible strategies)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success

# --- Helper ---

def _mock_mutate_response(resource_name: str) -> MagicMock:
    response = MagicMock()
    response.results = [MagicMock(resource_name=resource_name)]
    return response


# --- list_bidding_data_exclusions ---

class TestListBiddingDataExclusions:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_returns_exclusions(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import list_bidding_data_exclusions

        mock_row = MagicMock()
        de = mock_row.bidding_data_exclusion
        de.data_exclusion_id = 111
        de.name = "Site outage"
        de.status.name = "ENABLED"
        de.description = "Server down"
        de.start_date_time = "2026-03-01 00:00:00"
        de.end_date_time = "2026-03-02 00:00:00"
        de.scope.name = "CHANNEL"
        ct_mock = MagicMock()
        ct_mock.name = "SEARCH"
        de.advertising_channel_types = [ct_mock]
        de.campaigns = []

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_bidding_data_exclusions("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["exclusions"][0]["name"] == "Site outage"
        assert result["data"]["exclusions"][0]["advertising_channel_types"] == ["SEARCH"]

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_empty_results(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import list_bidding_data_exclusions

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_bidding_data_exclusions("123"))
        assert result["data"]["count"] == 0

    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.bidding import list_bidding_data_exclusions

        result = assert_error(list_bidding_data_exclusions(""))
        assert "Failed to list bidding data exclusions" in result["error"]


# --- create_bidding_data_exclusion ---

class TestCreateBiddingDataExclusion:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_creates_channel_scope(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_data_exclusion

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_bidding_data_exclusions.return_value = _mock_mutate_response(
            "customers/123/biddingDataExclusions/777"
        )
        mock_get_service.return_value = mock_service

        result = assert_success(create_bidding_data_exclusion(
            "123", "Outage", "2026-03-01 00:00:00", "2026-03-02 00:00:00",
            "CHANNEL", advertising_channel_types=["SEARCH"],
        ))
        assert result["data"]["data_exclusion_id"] == "777"
        mock_service.mutate_bidding_data_exclusions.assert_called_once()

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_creates_campaign_scope(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_data_exclusion

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_bidding_data_exclusions.return_value = _mock_mutate_response(
            "customers/123/biddingDataExclusions/778"
        )
        mock_get_service.return_value = mock_service

        result = assert_success(create_bidding_data_exclusion(
            "123", "Campaign Exclusion", "2026-03-01 00:00:00", "2026-03-02 00:00:00",
            "CAMPAIGN", campaign_ids=["555", "666"],
        ))
        assert result["data"]["data_exclusion_id"] == "778"

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_creates_with_description(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_data_exclusion

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_bidding_data_exclusions.return_value = _mock_mutate_response(
            "customers/123/biddingDataExclusions/779"
        )
        mock_get_service.return_value = mock_service

        result = assert_success(create_bidding_data_exclusion(
            "123", "Desc Test", "2026-03-01 00:00:00", "2026-03-02 00:00:00",
            "CHANNEL", advertising_channel_types=["SEARCH"], description="Server was down",
        ))
        assert result["data"]["data_exclusion_id"] == "779"
        operation = client.get_type.return_value
        assert operation.create.description == "Server was down"

    def test_invalid_datetime(self):
        from mcp_google_ads.tools.bidding import create_bidding_data_exclusion

        result = assert_error(create_bidding_data_exclusion(
            "123", "Bad Date", "2026/03/01", "2026-03-02 00:00:00", "CHANNEL",
        ))
        assert "Failed to create bidding data exclusion" in result["error"]

    def test_invalid_scope(self):
        from mcp_google_ads.tools.bidding import create_bidding_data_exclusion

        result = assert_error(create_bidding_data_exclusion(
            "123", "Bad Scope", "2026-03-01 00:00:00", "2026-03-02 00:00:00", "INVALID",
        ))
        assert "Failed to create bidding data exclusion" in result["error"]

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_campaign_scope_missing_ids(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_data_exclusion

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(create_bidding_data_exclusion(
            "123", "No IDs", "2026-03-01 00:00:00", "2026-03-02 00:00:00", "CAMPAIGN",
        ))
        assert "campaign_ids is required" in result["error"]

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_channel_scope_missing_types(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_data_exclusion

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(create_bidding_data_exclusion(
            "123", "No Types", "2026-03-01 00:00:00", "2026-03-02 00:00:00", "CHANNEL",
        ))
        assert "advertising_channel_types is required" in result["error"]

    def test_invalid_channel_type(self):
        from mcp_google_ads.tools.bidding import create_bidding_data_exclusion

        result = assert_error(create_bidding_data_exclusion(
            "123", "Bad Channel", "2026-03-01 00:00:00", "2026-03-02 00:00:00",
            "CHANNEL", advertising_channel_types=["INVALID_CHANNEL"],
        ))
        assert "Failed to create bidding data exclusion" in result["error"]


# --- remove_bidding_data_exclusion ---

class TestRemoveBiddingDataExclusion:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_removes_exclusion(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import remove_bidding_data_exclusion

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_bidding_data_exclusions.return_value = _mock_mutate_response(
            "customers/123/biddingDataExclusions/777"
        )
        mock_get_service.return_value = mock_service

        result = assert_success(remove_bidding_data_exclusion("123", "777"))
        assert "removed" in result["message"]

    def test_invalid_id(self):
        from mcp_google_ads.tools.bidding import remove_bidding_data_exclusion

        result = assert_error(remove_bidding_data_exclusion("123", "abc"))
        assert "Failed to remove bidding data exclusion" in result["error"]

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_error_handling(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import remove_bidding_data_exclusion

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_bidding_data_exclusions.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(remove_bidding_data_exclusion("123", "777"))
        assert "Failed to remove bidding data exclusion" in result["error"]


# --- list_seasonality_adjustments ---

class TestListSeasonalityAdjustments:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_returns_adjustments(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import list_seasonality_adjustments

        mock_row = MagicMock()
        sa = mock_row.bidding_seasonality_adjustment
        sa.seasonality_adjustment_id = 222
        sa.name = "Black Friday"
        sa.status.name = "ENABLED"
        sa.description = "Expected +50% conversions"
        sa.start_date_time = "2026-11-27 00:00:00"
        sa.end_date_time = "2026-11-30 00:00:00"
        sa.scope.name = "CHANNEL"
        sa.conversion_rate_modifier = 1.5
        ct_mock = MagicMock()
        ct_mock.name = "SEARCH"
        sa.advertising_channel_types = [ct_mock]
        sa.campaigns = []

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_seasonality_adjustments("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["adjustments"][0]["name"] == "Black Friday"
        assert result["data"]["adjustments"][0]["conversion_rate_modifier"] == 1.5

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_empty_results(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import list_seasonality_adjustments

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_seasonality_adjustments("123"))
        assert result["data"]["count"] == 0

    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.bidding import list_seasonality_adjustments

        result = assert_error(list_seasonality_adjustments(""))
        assert "Failed to list seasonality adjustments" in result["error"]


# --- create_seasonality_adjustment ---

class TestCreateSeasonalityAdjustment:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_creates_channel_scope(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_seasonality_adjustment

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_bidding_seasonality_adjustments.return_value = _mock_mutate_response(
            "customers/123/biddingSeasonalityAdjustments/888"
        )
        mock_get_service.return_value = mock_service

        result = assert_success(create_seasonality_adjustment(
            "123", "Black Friday", "2026-11-27 00:00:00", "2026-11-30 00:00:00",
            1.5, "CHANNEL", advertising_channel_types=["SEARCH", "PERFORMANCE_MAX"],
        ))
        assert result["data"]["seasonality_adjustment_id"] == "888"
        mock_service.mutate_bidding_seasonality_adjustments.assert_called_once()

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_creates_campaign_scope(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_seasonality_adjustment

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_bidding_seasonality_adjustments.return_value = _mock_mutate_response(
            "customers/123/biddingSeasonalityAdjustments/889"
        )
        mock_get_service.return_value = mock_service

        result = assert_success(create_seasonality_adjustment(
            "123", "Campaign Sale", "2026-11-27 00:00:00", "2026-11-30 00:00:00",
            1.3, "CAMPAIGN", campaign_ids=["555"],
        ))
        assert result["data"]["seasonality_adjustment_id"] == "889"

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_creates_with_description(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_seasonality_adjustment

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_bidding_seasonality_adjustments.return_value = _mock_mutate_response(
            "customers/123/biddingSeasonalityAdjustments/890"
        )
        mock_get_service.return_value = mock_service

        result = assert_success(create_seasonality_adjustment(
            "123", "Desc Test", "2026-11-27 00:00:00", "2026-11-30 00:00:00",
            1.2, "CHANNEL", advertising_channel_types=["SEARCH"], description="Holiday sale",
        ))
        assert result["data"]["seasonality_adjustment_id"] == "890"
        operation = client.get_type.return_value
        assert operation.create.description == "Holiday sale"

    def test_invalid_datetime(self):
        from mcp_google_ads.tools.bidding import create_seasonality_adjustment

        result = assert_error(create_seasonality_adjustment(
            "123", "Bad", "bad-date", "2026-03-02 00:00:00", 1.5, "CHANNEL",
        ))
        assert "Failed to create seasonality adjustment" in result["error"]

    def test_invalid_scope(self):
        from mcp_google_ads.tools.bidding import create_seasonality_adjustment

        result = assert_error(create_seasonality_adjustment(
            "123", "Bad", "2026-03-01 00:00:00", "2026-03-02 00:00:00", 1.5, "INVALID",
        ))
        assert "Failed to create seasonality adjustment" in result["error"]

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_invalid_conversion_rate_modifier(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_seasonality_adjustment

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(create_seasonality_adjustment(
            "123", "Bad Rate", "2026-03-01 00:00:00", "2026-03-02 00:00:00",
            0.0, "CHANNEL", advertising_channel_types=["SEARCH"],
        ))
        assert "conversion_rate_modifier must be greater than 0" in result["error"]

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_campaign_scope_missing_ids(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_seasonality_adjustment

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(create_seasonality_adjustment(
            "123", "No IDs", "2026-03-01 00:00:00", "2026-03-02 00:00:00",
            1.5, "CAMPAIGN",
        ))
        assert "campaign_ids is required" in result["error"]

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_channel_scope_missing_types(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_seasonality_adjustment

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(create_seasonality_adjustment(
            "123", "No Types", "2026-03-01 00:00:00", "2026-03-02 00:00:00",
            1.5, "CHANNEL",
        ))
        assert "advertising_channel_types is required" in result["error"]

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_negative_conversion_rate_modifier(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_seasonality_adjustment

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(create_seasonality_adjustment(
            "123", "Negative", "2026-03-01 00:00:00", "2026-03-02 00:00:00",
            -0.5, "CHANNEL", advertising_channel_types=["SEARCH"],
        ))
        assert "conversion_rate_modifier must be greater than 0" in result["error"]


# --- remove_seasonality_adjustment ---

class TestRemoveSeasonalityAdjustment:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_removes_adjustment(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import remove_seasonality_adjustment

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_bidding_seasonality_adjustments.return_value = _mock_mutate_response(
            "customers/123/biddingSeasonalityAdjustments/888"
        )
        mock_get_service.return_value = mock_service

        result = assert_success(remove_seasonality_adjustment("123", "888"))
        assert "removed" in result["message"]

    def test_invalid_id(self):
        from mcp_google_ads.tools.bidding import remove_seasonality_adjustment

        result = assert_error(remove_seasonality_adjustment("123", "abc"))
        assert "Failed to remove seasonality adjustment" in result["error"]

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_error_handling(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import remove_seasonality_adjustment

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_bidding_seasonality_adjustments.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(remove_seasonality_adjustment("123", "888"))
        assert "Failed to remove seasonality adjustment" in result["error"]


# --- list_accessible_bidding_strategies ---

class TestListAccessibleBiddingStrategies:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_returns_strategies(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import list_accessible_bidding_strategies

        mock_row = MagicMock()
        abs_ = mock_row.accessible_bidding_strategy
        abs_.id = 999
        abs_.name = "MCC Strategy"
        abs_.type_.name = "TARGET_CPA"
        abs_.owner_customer_id = 5555
        abs_.owner_descriptive_name = "Manager Account"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_accessible_bidding_strategies("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["strategies"][0]["name"] == "MCC Strategy"
        assert result["data"]["strategies"][0]["type"] == "TARGET_CPA"
        assert result["data"]["strategies"][0]["owner_customer_id"] == "5555"

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_empty_results(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import list_accessible_bidding_strategies

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_accessible_bidding_strategies("123"))
        assert result["data"]["count"] == 0

    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.bidding import list_accessible_bidding_strategies

        result = assert_error(list_accessible_bidding_strategies(""))
        assert "Failed to list accessible bidding strategies" in result["error"]


# --- Validation helpers ---

class TestValidationHelpers:
    def test_validate_datetime_valid(self):
        from mcp_google_ads.tools.bidding import _validate_datetime

        assert _validate_datetime("2026-03-01 00:00:00") == "2026-03-01 00:00:00"

    def test_validate_datetime_invalid(self):
        import pytest

        from mcp_google_ads.tools.bidding import _validate_datetime

        with pytest.raises(ValueError, match="Formato esperado"):
            _validate_datetime("2026/03/01")

    def test_validate_scope_valid(self):
        from mcp_google_ads.tools.bidding import _validate_scope

        assert _validate_scope("campaign") == "CAMPAIGN"
        assert _validate_scope("CHANNEL") == "CHANNEL"

    def test_validate_scope_invalid(self):
        import pytest

        from mcp_google_ads.tools.bidding import _validate_scope

        with pytest.raises(ValueError, match="Scope inválido"):
            _validate_scope("ACCOUNT")

    def test_validate_channel_types_valid(self):
        from mcp_google_ads.tools.bidding import _validate_channel_types

        result = _validate_channel_types(["search", "PERFORMANCE_MAX"])
        assert result == ["SEARCH", "PERFORMANCE_MAX"]

    def test_validate_channel_types_invalid(self):
        import pytest

        from mcp_google_ads.tools.bidding import _validate_channel_types

        with pytest.raises(ValueError, match="Channel type inválido"):
            _validate_channel_types(["INVALID_CHANNEL"])
