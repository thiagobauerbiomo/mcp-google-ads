"""Tests for campaigns.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListCampaigns:
    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_returns_campaigns(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaigns

        mock_row = MagicMock()
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Test Campaign"
        mock_row.campaign.status.name = "ENABLED"
        mock_row.campaign.advertising_channel_type.name = "SEARCH"
        mock_row.campaign.bidding_strategy_type.name = "MANUAL_CPC"
        mock_row.campaign_budget.amount_micros = 50_000_000
        mock_row.campaign.start_date = "2024-01-01"
        mock_row.campaign.end_date = ""

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaigns("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["campaigns"][0]["campaign_id"] == "111"
        assert result["data"]["campaigns"][0]["name"] == "Test Campaign"

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_empty_results(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaigns

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaigns("123"))
        assert result["data"]["count"] == 0

    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaigns import list_campaigns

        result = assert_error(list_campaigns(""))
        assert "Failed to list campaigns" in result["error"]


class TestCreateCampaign:
    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_creates_paused(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import create_campaign

        client = MagicMock()
        mock_client.return_value = client

        budget_response = MagicMock()
        budget_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/1")]
        budget_service = MagicMock()
        budget_service.mutate_campaign_budgets.return_value = budget_response

        campaign_response = MagicMock()
        campaign_response.results = [MagicMock(resource_name="customers/123/campaigns/222")]
        campaign_service = MagicMock()
        campaign_service.mutate_campaigns.return_value = campaign_response

        mock_get_service.side_effect = lambda name: {
            "CampaignBudgetService": budget_service,
            "CampaignService": campaign_service,
        }[name]

        result = assert_success(create_campaign("123", "Test", 50.0))
        assert result["data"]["campaign_id"] == "222"
        assert result["data"]["status"] == "PAUSED"


class TestSetCampaignStatus:
    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_sets_status(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import set_campaign_status

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaigns/111")]
        mock_service.mutate_campaigns.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(set_campaign_status("123", "111", "PAUSED"))
        assert result["data"]["new_status"] == "PAUSED"


class TestRemoveCampaign:
    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_removes_campaign(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import remove_campaign

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaigns/111")]
        mock_service.mutate_campaigns.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_campaign("123", "111"))
        assert "removed permanently" in result["message"]
