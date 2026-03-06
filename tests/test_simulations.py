"""Tests for simulations.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

from tests.conftest import assert_error, assert_success


def _make_point(list_type="cpc_bid", **overrides):
    """Create a mock simulation point with common fields."""
    p = MagicMock()
    if list_type == "cpc_bid":
        p.cpc_bid_micros = overrides.get("cpc_bid_micros", 1_000_000)
    elif list_type == "budget":
        p.budget_amount_micros = overrides.get("budget_amount_micros", 10_000_000)
    elif list_type == "target_cpa":
        p.target_cpa_micros = overrides.get("target_cpa_micros", 5_000_000)
    elif list_type == "target_roas":
        p.target_roas = overrides.get("target_roas", 3.5)
    p.clicks = overrides.get("clicks", 100)
    p.impressions = overrides.get("impressions", 1000)
    p.cost_micros = overrides.get("cost_micros", 500_000)
    p.biddable_conversions = overrides.get("biddable_conversions", 10.0)
    p.biddable_conversions_value = overrides.get("biddable_conversions_value", 250.0)
    p.top_slot_impressions = overrides.get("top_slot_impressions", 800)
    return p


def _make_point_list(list_type="cpc_bid", count=2):
    """Create a mock point list with N points."""
    pl = MagicMock()
    pl.points = [_make_point(list_type) for _ in range(count)]
    return pl


class TestParsePointList:
    def test_parses_cpc_bid_points(self):
        from mcp_google_ads.tools.simulations import _parse_point_list

        pl = _make_point_list("cpc_bid", count=2)
        result = _parse_point_list(pl, "cpc_bid")
        assert len(result) == 2
        assert result[0]["cpc_bid"] == 1.0
        assert result[0]["cpc_bid_micros"] == 1_000_000
        assert result[0]["clicks"] == 100
        assert result[0]["impressions"] == 1000
        assert result[0]["cost"] == 0.5
        assert result[0]["conversions"] == 10.0
        assert result[0]["top_impressions"] == 800

    def test_parses_budget_points(self):
        from mcp_google_ads.tools.simulations import _parse_point_list

        pl = _make_point_list("budget", count=1)
        result = _parse_point_list(pl, "budget")
        assert len(result) == 1
        assert result[0]["budget"] == 10.0
        assert result[0]["budget_micros"] == 10_000_000

    def test_parses_target_cpa_points(self):
        from mcp_google_ads.tools.simulations import _parse_point_list

        pl = _make_point_list("target_cpa", count=1)
        result = _parse_point_list(pl, "target_cpa")
        assert result[0]["target_cpa"] == 5.0
        assert result[0]["target_cpa_micros"] == 5_000_000

    def test_parses_target_roas_points(self):
        from mcp_google_ads.tools.simulations import _parse_point_list

        pl = _make_point_list("target_roas", count=1)
        result = _parse_point_list(pl, "target_roas")
        assert result[0]["target_roas"] == 3.5

    def test_returns_empty_for_none(self):
        from mcp_google_ads.tools.simulations import _parse_point_list

        assert _parse_point_list(None, "cpc_bid") == []

    def test_returns_empty_for_no_points_attr(self):
        from mcp_google_ads.tools.simulations import _parse_point_list

        obj = MagicMock(spec=[])
        assert _parse_point_list(obj, "cpc_bid") == []

    def test_handles_zero_conversions(self):
        from mcp_google_ads.tools.simulations import _parse_point_list

        pl = MagicMock()
        p = _make_point("cpc_bid")
        p.biddable_conversions = 0
        p.biddable_conversions_value = 0
        pl.points = [p]
        result = _parse_point_list(pl, "cpc_bid")
        assert result[0]["conversions"] == 0
        assert result[0]["conversions_value"] == 0


class TestListCampaignSimulations:
    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_simulations(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import list_campaign_simulations

        mock_row = MagicMock()
        sim = mock_row.campaign_simulation
        sim.campaign_id = 456
        sim.type_.name = "CPC_BID"
        sim.modification_method.name = "UNIFORM"
        sim.start_date = "2024-01-01"
        sim.end_date = "2024-01-07"
        sim.cpc_bid_point_list = _make_point_list("cpc_bid", count=3)
        sim.target_cpa_point_list = None
        sim.target_roas_point_list = None
        sim.budget_point_list = None

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_simulations("123", "456"))
        assert result["data"]["count"] == 1
        assert result["data"]["simulations"][0]["type"] == "CPC_BID"
        assert len(result["data"]["simulations"][0]["points"]) == 3

    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_empty_when_no_simulations(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import list_campaign_simulations

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_simulations("123", "456"))
        assert result["data"]["count"] == 0
        assert result["data"]["simulations"] == []

    def test_rejects_invalid_campaign_id(self):
        from mcp_google_ads.tools.simulations import list_campaign_simulations

        result = assert_error(list_campaign_simulations("123", "abc"))
        assert "Failed to list campaign simulations" in result["error"]

    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.simulations import list_campaign_simulations

        result = assert_error(list_campaign_simulations("", "456"))
        assert "Failed to list campaign simulations" in result["error"]


class TestListAdGroupSimulations:
    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_simulations(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import list_ad_group_simulations

        mock_row = MagicMock()
        sim = mock_row.ad_group_simulation
        sim.ad_group_id = 789
        sim.type_.name = "TARGET_CPA"
        sim.modification_method.name = "UNIFORM"
        sim.start_date = "2024-02-01"
        sim.end_date = "2024-02-07"
        sim.cpc_bid_point_list = None
        sim.target_cpa_point_list = _make_point_list("target_cpa", count=2)
        sim.target_roas_point_list = None

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_ad_group_simulations("123", "789"))
        assert result["data"]["count"] == 1
        assert result["data"]["simulations"][0]["type"] == "TARGET_CPA"
        assert len(result["data"]["simulations"][0]["points"]) == 2

    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_empty(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import list_ad_group_simulations

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_ad_group_simulations("123", "789"))
        assert result["data"]["count"] == 0

    def test_rejects_invalid_ad_group_id(self):
        from mcp_google_ads.tools.simulations import list_ad_group_simulations

        result = assert_error(list_ad_group_simulations("123", "abc"))
        assert "Failed to list ad group simulations" in result["error"]

    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", side_effect=Exception("Fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.simulations import list_ad_group_simulations

        result = assert_error(list_ad_group_simulations("", "789"))
        assert "Failed to list ad group simulations" in result["error"]


class TestListKeywordSimulations:
    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_simulations(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import list_keyword_simulations

        mock_row = MagicMock()
        sim = mock_row.ad_group_criterion_simulation
        sim.ad_group_id = 789
        sim.criterion_id = 111
        sim.type_.name = "CPC_BID"
        sim.modification_method.name = "UNIFORM"
        sim.start_date = "2024-03-01"
        sim.end_date = "2024-03-07"
        sim.cpc_bid_point_list = _make_point_list("cpc_bid", count=4)

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_keyword_simulations("123", "789", "111"))
        assert result["data"]["count"] == 1
        assert result["data"]["simulations"][0]["criterion_id"] == 111
        assert len(result["data"]["simulations"][0]["points"]) == 4

    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_empty(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import list_keyword_simulations

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_keyword_simulations("123", "789", "111"))
        assert result["data"]["count"] == 0

    def test_rejects_invalid_ad_group_id(self):
        from mcp_google_ads.tools.simulations import list_keyword_simulations

        result = assert_error(list_keyword_simulations("123", "abc", "111"))
        assert "Failed to list keyword simulations" in result["error"]

    def test_rejects_invalid_criterion_id(self):
        from mcp_google_ads.tools.simulations import list_keyword_simulations

        result = assert_error(list_keyword_simulations("123", "789", "abc"))
        assert "Failed to list keyword simulations" in result["error"]


class TestGetBidSimulationPoints:
    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_cpc_bid_points(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import get_bid_simulation_points

        mock_row = MagicMock()
        sim = mock_row.campaign_simulation
        sim.campaign_id = 456
        sim.start_date = "2024-01-01"
        sim.end_date = "2024-01-07"
        sim.cpc_bid_point_list = _make_point_list("cpc_bid", count=5)

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_bid_simulation_points("123", "456", "CPC_BID"))
        assert result["data"]["type"] == "CPC_BID"
        assert result["data"]["points_count"] == 5
        assert len(result["data"]["points"]) == 5
        assert result["data"]["points"][0]["cpc_bid"] == 1.0

    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_budget_points(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import get_bid_simulation_points

        mock_row = MagicMock()
        sim = mock_row.campaign_simulation
        sim.campaign_id = 456
        sim.start_date = "2024-01-01"
        sim.end_date = "2024-01-07"
        sim.budget_point_list = _make_point_list("budget", count=3)

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_bid_simulation_points("123", "456", "BUDGET"))
        assert result["data"]["type"] == "BUDGET"
        assert result["data"]["points_count"] == 3
        assert result["data"]["points"][0]["budget"] == 10.0

    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_not_found(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import get_bid_simulation_points

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_error(get_bid_simulation_points("123", "456", "CPC_BID"))
        assert "No CPC_BID simulation found" in result["error"]

    def test_rejects_invalid_simulation_type(self):
        from mcp_google_ads.tools.simulations import get_bid_simulation_points

        result = assert_error(get_bid_simulation_points("123", "456", "INVALID_TYPE!!"))
        assert "Failed to get bid simulation points" in result["error"]

    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_rejects_unsupported_type(self, mock_resolve):
        from mcp_google_ads.tools.simulations import get_bid_simulation_points

        result = assert_error(get_bid_simulation_points("123", "456", "PERCENT_CPC"))
        assert "Invalid simulation_type" in result["error"]

    def test_rejects_invalid_campaign_id(self):
        from mcp_google_ads.tools.simulations import get_bid_simulation_points

        result = assert_error(get_bid_simulation_points("123", "abc", "CPC_BID"))
        assert "Failed to get bid simulation points" in result["error"]


class TestListCampaignBudgetSimulations:
    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_budget_simulations(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import list_campaign_budget_simulations

        mock_row = MagicMock()
        sim = mock_row.campaign_simulation
        sim.campaign_id = 456
        sim.start_date = "2024-01-01"
        sim.end_date = "2024-01-07"
        sim.budget_point_list = _make_point_list("budget", count=3)

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_budget_simulations("123", "456"))
        assert result["data"]["count"] == 1
        assert len(result["data"]["simulations"][0]["points"]) == 3
        assert result["data"]["simulations"][0]["points"][0]["budget"] == 10.0

    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_empty(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import list_campaign_budget_simulations

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_budget_simulations("123", "456"))
        assert result["data"]["count"] == 0

    def test_rejects_invalid_campaign_id(self):
        from mcp_google_ads.tools.simulations import list_campaign_budget_simulations

        result = assert_error(list_campaign_budget_simulations("123", "abc"))
        assert "Failed to list campaign budget simulations" in result["error"]

    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", side_effect=Exception("Fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.simulations import list_campaign_budget_simulations

        result = assert_error(list_campaign_budget_simulations("", "456"))
        assert "Failed to list campaign budget simulations" in result["error"]


class TestGetKeywordPlanSimulation:
    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_forecast(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import get_keyword_plan_simulation

        mock_cfm = MagicMock()
        mock_cfm.clicks = 500
        mock_cfm.impressions = 5000
        mock_cfm.cost_micros = 2_500_000
        mock_cfm.conversions = 25.5
        mock_cfm.conversion_rate = 0.051
        mock_cfm.average_cpc_micros = 500_000

        mock_kf_forecast = MagicMock()
        mock_kf_forecast.clicks = 200
        mock_kf_forecast.impressions = 2000
        mock_kf_forecast.cost_micros = 1_000_000
        mock_kf_forecast.conversions = 10.0
        mock_kf_forecast.average_cpc_micros = 500_000

        mock_kf = MagicMock()
        mock_kf.keyword_plan_ad_group_keyword = "customers/123/keywordPlanAdGroupKeywords/999"
        mock_kf.keyword_forecast = mock_kf_forecast

        mock_response = MagicMock()
        mock_response.campaign_forecast_metrics = mock_cfm
        mock_response.keyword_forecasts = [mock_kf]

        mock_service = MagicMock()
        mock_service.generate_forecast_metrics.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(get_keyword_plan_simulation("123", "999"))
        assert result["data"]["keyword_plan_id"] == "999"
        assert result["data"]["campaign_forecast"]["clicks"] == 500
        assert result["data"]["campaign_forecast"]["cost"] == 2.5
        assert result["data"]["campaign_forecast"]["conversions"] == 25.5
        assert result["data"]["campaign_forecast"]["conversion_rate"] == 0.051
        assert result["data"]["keyword_count"] == 1
        assert result["data"]["keyword_forecasts"][0]["clicks"] == 200

    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_returns_empty_forecast(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import get_keyword_plan_simulation

        mock_response = MagicMock(spec=[])
        mock_service = MagicMock()
        mock_service.generate_forecast_metrics.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(get_keyword_plan_simulation("123", "999"))
        assert result["data"]["campaign_forecast"] is None
        assert result["data"]["keyword_count"] == 0

    def test_rejects_invalid_keyword_plan_id(self):
        from mcp_google_ads.tools.simulations import get_keyword_plan_simulation

        result = assert_error(get_keyword_plan_simulation("123", "abc"))
        assert "Failed to get keyword plan simulation" in result["error"]

    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_api_error(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import get_keyword_plan_simulation

        mock_service = MagicMock()
        mock_service.generate_forecast_metrics.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(get_keyword_plan_simulation("123", "999"))
        assert "Failed to get keyword plan simulation" in result["error"]

    @patch("mcp_google_ads.tools.simulations.get_service")
    @patch("mcp_google_ads.tools.simulations.resolve_customer_id", return_value="123")
    def test_calls_correct_resource_name(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.simulations import get_keyword_plan_simulation

        mock_response = MagicMock(spec=[])
        mock_service = MagicMock()
        mock_service.generate_forecast_metrics.return_value = mock_response
        mock_get_service.return_value = mock_service

        get_keyword_plan_simulation("123", "555")
        mock_service.generate_forecast_metrics.assert_called_once_with(
            keyword_plan="customers/123/keywordPlans/555"
        )
