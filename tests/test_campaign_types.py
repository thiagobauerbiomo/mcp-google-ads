"""Tests for campaign_types.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListAssetGroups:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_returns_asset_groups(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_types import list_asset_groups

        mock_row = MagicMock()
        mock_row.asset_group.id = 111
        mock_row.asset_group.name = "Test Group"
        mock_row.asset_group.status.name = "ENABLED"
        mock_row.asset_group.campaign = "customers/123/campaigns/222"
        mock_row.asset_group.final_urls = ["https://example.com"]

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_asset_groups("123", "222"))
        assert result["data"]["count"] == 1
        assert result["data"]["asset_groups"][0]["name"] == "Test Group"

    def test_rejects_invalid_campaign_id(self):
        from mcp_google_ads.tools.campaign_types import list_asset_groups

        result = assert_error(list_asset_groups("123", "abc"))
        assert "Failed" in result["error"]


class TestCreatePerformanceMaxCampaign:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_pmax(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_performance_max_campaign

        client = MagicMock()
        mock_client.return_value = client

        # Mock the batch mutate response
        result1 = MagicMock(resource_name="customers/123/campaignBudgets/1")
        result2 = MagicMock(resource_name="customers/123/campaigns/2")
        result3 = MagicMock(resource_name="customers/123/assetGroups/3")

        mock_response = MagicMock()
        mock_response.mutate_operation_responses = [
            MagicMock(campaign_budget_result=result1),
            MagicMock(campaign_result=result2),
            MagicMock(asset_group_result=result3),
        ]

        mock_service = MagicMock()
        mock_service.mutate.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_performance_max_campaign(
            customer_id="123",
            name="PMax Test",
            budget_amount=50.0,
            final_url="https://example.com",
            asset_group_name="Test Group",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            long_headlines=["LH1"],
            business_name="Test Business",
        ))
        assert "campaign_id" in result["data"]

    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_types import create_performance_max_campaign

        result = assert_error(create_performance_max_campaign(
            customer_id="",
            name="PMax",
            budget_amount=50.0,
            final_url="https://example.com",
            asset_group_name="Group",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            long_headlines=["LH1"],
            business_name="Business",
        ))
        assert "Failed" in result["error"]
