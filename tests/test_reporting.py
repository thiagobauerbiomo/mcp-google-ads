"""Tests for reporting.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestCampaignPerformanceReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_returns_report(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import campaign_performance_report

        mock_row = MagicMock()
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Test"
        mock_row.campaign.status.name = "ENABLED"
        mock_row.metrics.impressions = 1000
        mock_row.metrics.clicks = 50
        mock_row.metrics.cost_micros = 25_000_000
        mock_row.metrics.conversions = 5.0
        mock_row.metrics.conversions_value = 500.0
        mock_row.metrics.ctr = 0.05
        mock_row.metrics.average_cpc = 500_000
        mock_row.metrics.average_cpm = 25_000_000
        mock_row.metrics.cost_per_conversion = 5_000_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(campaign_performance_report("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["report"][0]["impressions"] == 1000
        assert result["data"]["report"][0]["clicks"] == 50
        assert result["data"]["report"][0]["ctr"] == 5.0

    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.reporting import campaign_performance_report

        result = assert_error(campaign_performance_report(""))
        assert "Failed" in result["error"]


class TestDevicePerformanceReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_returns_device_report(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import device_performance_report

        mock_row = MagicMock()
        mock_row.segments.device.name = "MOBILE"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Test"
        mock_row.metrics.impressions = 500
        mock_row.metrics.clicks = 25
        mock_row.metrics.cost_micros = 10_000_000
        mock_row.metrics.conversions = 2.0
        mock_row.metrics.ctr = 0.05
        mock_row.metrics.average_cpc = 400_000
        mock_row.metrics.cost_per_conversion = 5_000_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(device_performance_report("123"))
        assert result["data"]["report"][0]["device"] == "MOBILE"


class TestQualityScoreReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_returns_quality_scores(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import quality_score_report

        mock_row = MagicMock()
        mock_row.ad_group_criterion.keyword.text = "test kw"
        mock_row.ad_group_criterion.keyword.match_type.name = "BROAD"
        mock_row.ad_group_criterion.quality_info.quality_score = 8
        mock_row.ad_group_criterion.quality_info.creative_quality_score.name = "ABOVE_AVERAGE"
        mock_row.ad_group_criterion.quality_info.post_click_quality_score.name = "AVERAGE"
        mock_row.ad_group_criterion.quality_info.search_predicted_ctr.name = "ABOVE_AVERAGE"
        mock_row.ad_group.id = 222
        mock_row.ad_group.name = "AG 1"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "C 1"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(quality_score_report("123"))
        assert result["data"]["report"][0]["quality_score"] == 8
        assert result["data"]["report"][0]["ad_relevance"] == "ABOVE_AVERAGE"
