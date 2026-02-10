"""Tests for dashboard.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestAccountDashboard:
    @patch("mcp_google_ads.tools.dashboard.get_service")
    @patch("mcp_google_ads.tools.dashboard.resolve_customer_id", return_value="123")
    def test_returns_dashboard_data(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.dashboard import account_dashboard

        mock_metrics_row = MagicMock()
        mock_metrics_row.metrics.impressions = 1000
        mock_metrics_row.metrics.clicks = 50
        mock_metrics_row.metrics.cost_micros = 10_000_000
        mock_metrics_row.metrics.conversions = 5.0
        mock_metrics_row.metrics.conversions_value = 500.0
        mock_metrics_row.metrics.ctr = 0.05
        mock_metrics_row.metrics.average_cpc = 200_000
        mock_metrics_row.metrics.cost_per_conversion = 2_000_000

        mock_campaign_row = MagicMock()
        mock_campaign_row.campaign.status.name = "ENABLED"

        mock_top_row = MagicMock()
        mock_top_row.campaign.id = 111
        mock_top_row.campaign.name = "Top Campaign"
        mock_top_row.campaign.status.name = "ENABLED"
        mock_top_row.metrics.cost_micros = 5_000_000
        mock_top_row.metrics.clicks = 30
        mock_top_row.metrics.conversions = 3.0
        mock_top_row.metrics.ctr = 0.06

        mock_opt_row = MagicMock()
        mock_opt_row.customer.optimization_score = 0.85

        mock_service = MagicMock()
        mock_service.search.side_effect = [
            [mock_metrics_row],       # metrics query
            [mock_campaign_row],      # campaign counts
            [mock_top_row],           # top campaigns
            [mock_opt_row],           # optimization score
            [MagicMock()] * 3,        # recommendations (3 items)
        ]
        mock_get_service.return_value = mock_service

        result = assert_success(account_dashboard("123"))
        assert result["data"]["metrics"]["impressions"] == 1000
        assert result["data"]["campaigns"]["enabled"] == 1
        assert len(result["data"]["top_campaigns"]) == 1
        assert result["data"]["optimization_score"] == 85.0
        assert result["data"]["pending_recommendations"] == 3

    @patch("mcp_google_ads.tools.dashboard.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.dashboard import account_dashboard

        result = assert_error(account_dashboard(""))
        assert "Failed to get account dashboard" in result["error"]


class TestMccPerformanceSummary:
    @patch("mcp_google_ads.tools.dashboard.get_service")
    @patch("mcp_google_ads.auth.get_config")
    def test_returns_summary(self, mock_config, mock_get_service):
        from mcp_google_ads.tools.dashboard import mcc_performance_summary

        mock_config.return_value.login_customer_id = "999"

        mock_client_row = MagicMock()
        mock_client_row.customer_client.id = 123
        mock_client_row.customer_client.descriptive_name = "Client A"

        mock_perf_row = MagicMock()
        mock_perf_row.metrics.impressions = 500
        mock_perf_row.metrics.clicks = 25
        mock_perf_row.metrics.cost_micros = 5_000_000
        mock_perf_row.metrics.conversions = 2.0
        mock_perf_row.metrics.ctr = 0.05
        mock_perf_row.metrics.average_cpc = 200_000

        mock_mcc_service = MagicMock()
        mock_mcc_service.search.return_value = [mock_client_row]

        mock_perf_service = MagicMock()
        mock_perf_service.search.return_value = [mock_perf_row]

        call_count = [0]

        def get_service_side_effect(name):
            if name == "GoogleAdsService":
                call_count[0] += 1
                if call_count[0] == 1:
                    return mock_mcc_service
                return mock_perf_service
            return MagicMock()

        mock_get_service.side_effect = get_service_side_effect

        result = assert_success(mcc_performance_summary())
        assert result["data"]["accounts_count"] == 1
        assert result["data"]["totals"]["clicks"] == 25

    @patch("mcp_google_ads.tools.dashboard.get_service", side_effect=Exception("API error"))
    def test_error_handling(self, mock_get_service):
        from mcp_google_ads.tools.dashboard import mcc_performance_summary

        result = assert_error(mcc_performance_summary())
        assert "Failed to get MCC performance summary" in result["error"]
