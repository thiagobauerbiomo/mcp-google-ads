"""Tests for diagnostics.py tools."""

from __future__ import annotations

import urllib.error
from unittest.mock import MagicMock, patch

from mcp_google_ads.tools.diagnostics import (
    budget_forecast,
    campaign_health_check,
    validate_landing_page,
)
from tests.conftest import assert_error, assert_success

# --- campaign_health_check ---


class TestCampaignHealthCheck:
    """Testa a tool campaign_health_check."""

    @patch("mcp_google_ads.tools.diagnostics.get_service")
    @patch("mcp_google_ads.tools.diagnostics.resolve_customer_id", return_value="1234567890")
    def test_returns_issues(self, mock_resolve, mock_get_service):
        mock_service = MagicMock()

        # Campaign query response
        campaign_row = MagicMock()
        campaign_row.campaign.id = 111
        campaign_row.campaign.name = "Campanha Search"
        campaign_row.campaign.status.name = "ENABLED"
        campaign_row.campaign_budget.amount_micros = 10_000_000
        campaign_row.campaign.advertising_channel_type.name = "SEARCH"

        # Ad strength query response (POOR ad)
        ad_row = MagicMock()
        ad_row.ad_group_ad.ad.id = 222
        ad_row.ad_group_ad.ad_strength.name = "POOR"
        ad_row.campaign.id = 111

        # Keyword quality score query response
        kw_row = MagicMock()
        kw_row.ad_group_criterion.keyword.text = "tarot online"
        kw_row.ad_group_criterion.quality_info.quality_score = 3
        kw_row.campaign.id = 111

        # Zero impressions query response
        zero_row = MagicMock()
        zero_row.campaign.id = 111
        zero_row.campaign.name = "Campanha Search"
        zero_row.metrics.impressions = 0

        mock_service.search.side_effect = [
            [campaign_row],  # campaigns
            [ad_row],        # ad strength
            [kw_row],        # keywords
            [zero_row],      # zero impressions
        ]
        mock_get_service.return_value = mock_service

        result = assert_success(campaign_health_check(customer_id="1234567890"))
        data = result["data"]

        assert data["total_issues"] == 3
        assert data["campaigns_checked"] == 1
        assert data["summary"]["critical"] == 2  # POOR ad + zero impressions
        assert data["summary"]["warning"] == 1   # low quality score (3)

        # Verify issue types
        issue_types = [i["type"] for i in data["issues"]]
        assert "weak_ad_strength" in issue_types
        assert "low_quality_score" in issue_types
        assert "zero_impressions" in issue_types

    @patch("mcp_google_ads.tools.diagnostics.get_service")
    @patch("mcp_google_ads.tools.diagnostics.resolve_customer_id", return_value="1234567890")
    def test_with_campaign_id(self, mock_resolve, mock_get_service):
        mock_service = MagicMock()
        mock_service.search.side_effect = [
            [],  # campaigns
            [],  # ad strength
            [],  # keywords
            [],  # zero impressions
        ]
        mock_get_service.return_value = mock_service

        result = assert_success(campaign_health_check(customer_id="1234567890", campaign_id="111"))
        data = result["data"]

        assert data["total_issues"] == 0
        assert data["campaigns_checked"] == 0

        # Verify campaign filter was included in all queries
        for call_args in mock_service.search.call_args_list:
            query = call_args[1]["query"]
            assert "campaign.id = 111" in query

    @patch("mcp_google_ads.tools.diagnostics.get_service")
    @patch("mcp_google_ads.tools.diagnostics.resolve_customer_id", return_value="1234567890")
    def test_no_issues_found(self, mock_resolve, mock_get_service):
        mock_service = MagicMock()

        campaign_row = MagicMock()
        campaign_row.campaign.id = 111
        campaign_row.campaign.name = "Campanha Saudavel"
        campaign_row.campaign.status.name = "ENABLED"
        campaign_row.campaign_budget.amount_micros = 10_000_000
        campaign_row.campaign.advertising_channel_type.name = "SEARCH"

        mock_service.search.side_effect = [
            [campaign_row],  # campaigns
            [],              # no weak ads
            [],              # no low quality keywords
            [],              # no zero impressions
        ]
        mock_get_service.return_value = mock_service

        result = assert_success(campaign_health_check(customer_id="1234567890"))
        data = result["data"]

        assert data["total_issues"] == 0
        assert data["campaigns_checked"] == 1
        assert data["summary"] == {"critical": 0, "warning": 0, "info": 0}

    @patch("mcp_google_ads.tools.diagnostics.get_service")
    @patch("mcp_google_ads.tools.diagnostics.resolve_customer_id", return_value="1234567890")
    def test_error_handling(self, mock_resolve, mock_get_service):
        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(campaign_health_check(customer_id="1234567890"))
        assert "Failed to run campaign health check" in result["error"]


# --- validate_landing_page ---


class TestValidateLandingPage:
    """Testa a tool validate_landing_page."""

    @patch("mcp_google_ads.tools.diagnostics.urllib.request.urlopen")
    def test_valid_url(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.url = "https://www.example.com/"
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        result = assert_success(validate_landing_page(url="https://www.example.com/"))
        data = result["data"]

        assert data["status_code"] == 200
        assert data["has_ssl"] is True
        assert data["redirected"] is False
        assert data["final_url"] == "https://www.example.com/"
        assert "response_time_ms" in data

    @patch("mcp_google_ads.tools.diagnostics.urllib.request.urlopen")
    def test_redirect(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.url = "https://www.example.com/new-page"
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        result = assert_success(validate_landing_page(url="https://www.example.com/old-page"))
        data = result["data"]

        assert data["redirected"] is True
        assert data["final_url"] == "https://www.example.com/new-page"
        assert data["url"] == "https://www.example.com/old-page"

    @patch("mcp_google_ads.tools.diagnostics.urllib.request.urlopen")
    def test_invalid_url(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://www.example.com/404",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

        result = assert_error(validate_landing_page(url="https://www.example.com/404"))
        assert "404" in result["error"]
        assert result["details"]["url"] == "https://www.example.com/404"
        assert result["details"]["status_code"] == 404

    @patch("mcp_google_ads.tools.diagnostics.urllib.request.urlopen")
    def test_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError(reason="timed out")

        result = assert_error(validate_landing_page(url="https://www.example.com/slow"))
        assert "timed out" in result["error"]
        assert result["details"]["url"] == "https://www.example.com/slow"


# --- budget_forecast ---


class TestBudgetForecast:
    """Testa a tool budget_forecast."""

    @patch("mcp_google_ads.tools.diagnostics.get_service")
    @patch("mcp_google_ads.tools.diagnostics.resolve_customer_id", return_value="1234567890")
    def test_forecast_all_campaigns(self, mock_resolve, mock_get_service):
        mock_service = MagicMock()

        # Budget query response
        budget_row = MagicMock()
        budget_row.campaign.id = 111
        budget_row.campaign.name = "Campanha Search"
        budget_row.campaign_budget.amount_micros = 10_000_000  # R$10/day

        # Spend query response (7 days of R$8/day = R$56 total)
        spend_row = MagicMock()
        spend_row.campaign.id = 111
        spend_row.metrics.cost_micros = 56_000_000  # R$56 total over 7 days

        mock_service.search.side_effect = [
            [budget_row],   # budget query
            [spend_row],    # spend query
        ]
        mock_get_service.return_value = mock_service

        result = assert_success(budget_forecast(customer_id="1234567890"))
        data = result["data"]

        assert data["forecast_days"] == 30
        assert data["campaigns_count"] == 1
        assert data["totals"]["daily_avg_spend"] == 8.0  # 56M / 7 = 8M micros = R$8
        assert data["totals"]["projected_spend"] == 240.0  # 8 * 30 = R$240
        assert data["totals"]["total_budget_daily"] == 10.0
        assert data["totals"]["utilization_pct"] == 80.0  # 8/10 * 100

        breakdown = data["breakdown"]
        assert len(breakdown) == 1
        assert breakdown[0]["campaign_id"] == "111"
        assert breakdown[0]["campaign_name"] == "Campanha Search"
        assert breakdown[0]["daily_avg_spend"] == 8.0
        assert breakdown[0]["utilization_pct"] == 80.0

    @patch("mcp_google_ads.tools.diagnostics.get_service")
    @patch("mcp_google_ads.tools.diagnostics.resolve_customer_id", return_value="1234567890")
    def test_forecast_specific_campaigns(self, mock_resolve, mock_get_service):
        mock_service = MagicMock()

        budget_row1 = MagicMock()
        budget_row1.campaign.id = 111
        budget_row1.campaign.name = "Campanha 1"
        budget_row1.campaign_budget.amount_micros = 10_000_000

        budget_row2 = MagicMock()
        budget_row2.campaign.id = 222
        budget_row2.campaign.name = "Campanha 2"
        budget_row2.campaign_budget.amount_micros = 20_000_000

        spend_row1 = MagicMock()
        spend_row1.campaign.id = 111
        spend_row1.metrics.cost_micros = 70_000_000  # R$10/day

        spend_row2 = MagicMock()
        spend_row2.campaign.id = 222
        spend_row2.metrics.cost_micros = 105_000_000  # R$15/day

        mock_service.search.side_effect = [
            [budget_row1, budget_row2],
            [spend_row1, spend_row2],
        ]
        mock_get_service.return_value = mock_service

        result = assert_success(
            budget_forecast(customer_id="1234567890", campaign_ids=["111", "222"], forecast_days=30)
        )
        data = result["data"]

        assert data["campaigns_count"] == 2

        # Verify campaign filter was included in queries
        for call_args in mock_service.search.call_args_list:
            query = call_args[1]["query"]
            assert "campaign.id IN (111, 222)" in query

    @patch("mcp_google_ads.tools.diagnostics.get_service")
    @patch("mcp_google_ads.tools.diagnostics.resolve_customer_id", return_value="1234567890")
    def test_error_handling(self, mock_resolve, mock_get_service):
        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(budget_forecast(customer_id="1234567890"))
        assert "Failed to generate budget forecast" in result["error"]
