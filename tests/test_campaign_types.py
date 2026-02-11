"""Tests for campaign_types.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_budget_service():
    """Create a mock CampaignBudgetService with a standard mutate response."""
    budget_service = MagicMock()
    budget_response = MagicMock()
    budget_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/1")]
    budget_service.mutate_campaign_budgets.return_value = budget_response
    return budget_service


def _make_campaign_service(campaign_id="2"):
    """Create a mock CampaignService with a standard mutate response."""
    campaign_service = MagicMock()
    campaign_response = MagicMock()
    campaign_response.results = [MagicMock(resource_name=f"customers/123/campaigns/{campaign_id}")]
    campaign_service.mutate_campaigns.return_value = campaign_response
    return campaign_service


# ---------------------------------------------------------------------------
# TestListAssetGroups
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# TestCreatePerformanceMaxCampaign
# ---------------------------------------------------------------------------

class TestCreatePerformanceMaxCampaign:
    _PMAX_BASE_KWARGS = {
        "customer_id": "123",
        "name": "PMax Test",
        "budget_amount": 50.0,
        "final_url": "https://example.com",
        "asset_group_name": "Test Group",
        "headlines": ["H1", "H2", "H3"],
        "descriptions": ["D1", "D2"],
        "long_headlines": ["LH1"],
        "business_name": "Test Business",
    }

    def _setup_pmax_mocks(self, mock_client, mock_get_service):
        client = MagicMock()
        mock_client.return_value = client

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

        return client

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_pmax(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_performance_max_campaign

        self._setup_pmax_mocks(mock_client, mock_get_service)

        result = assert_success(create_performance_max_campaign(**self._PMAX_BASE_KWARGS))
        assert "campaign_id" in result["data"]

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_pmax_maximize_conversion_value(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_performance_max_campaign

        self._setup_pmax_mocks(mock_client, mock_get_service)

        result = assert_success(create_performance_max_campaign(
            **self._PMAX_BASE_KWARGS,
            bidding_strategy="MAXIMIZE_CONVERSION_VALUE",
            target_roas=3.0,
        ))
        assert result["data"]["campaign_id"] == "2"
        assert result["data"]["status"] == "PAUSED"

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


# ---------------------------------------------------------------------------
# TestUpdateAssetGroup
# ---------------------------------------------------------------------------

class TestUpdateAssetGroup:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_updates_name(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import update_asset_group

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assetGroups/456")]
        mock_service.mutate_asset_groups.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_asset_group("123", "456", name="New Name"))
        assert result["data"]["resource_name"] == "customers/123/assetGroups/456"
        assert "updated" in result["message"]

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_updates_status(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import update_asset_group

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assetGroups/456")]
        mock_service.mutate_asset_groups.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_asset_group("123", "456", status="PAUSED"))
        assert result["data"]["resource_name"] == "customers/123/assetGroups/456"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_updates_final_url(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import update_asset_group

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assetGroups/456")]
        mock_service.mutate_asset_groups.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_asset_group("123", "456", final_url="https://new.example.com"))
        assert result["data"]["resource_name"] == "customers/123/assetGroups/456"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_updates_multiple_fields(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import update_asset_group

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assetGroups/456")]
        mock_service.mutate_asset_groups.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_asset_group(
            "123", "456",
            name="Updated",
            status="ENABLED",
            final_url="https://updated.example.com",
        ))
        assert result["data"]["resource_name"] == "customers/123/assetGroups/456"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_no_fields_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import update_asset_group

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(update_asset_group("123", "456"))
        assert "No fields" in result["error"]

    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", side_effect=Exception("Boom"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_types import update_asset_group

        result = assert_error(update_asset_group("123", "456", name="X"))
        assert "Failed" in result["error"]

    def test_rejects_invalid_status(self):
        from mcp_google_ads.tools.campaign_types import update_asset_group

        result = assert_error(update_asset_group("123", "456", status="DROP TABLE;"))
        assert "Failed" in result["error"]


# ---------------------------------------------------------------------------
# TestCreateDisplayCampaign
# ---------------------------------------------------------------------------

class TestCreateDisplayCampaign:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_display_maximize_clicks(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_display_campaign

        client = MagicMock()
        mock_client.return_value = client

        budget_service = _make_budget_service()
        campaign_service = _make_campaign_service()
        mock_get_service.side_effect = [budget_service, campaign_service]

        result = assert_success(create_display_campaign("123", "Display Test", 30.0))
        assert result["data"]["campaign_id"] == "2"
        assert result["data"]["status"] == "PAUSED"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_display_manual_cpc(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_display_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_display_campaign(
            "123", "Display Manual", 25.0,
            bidding_strategy="MANUAL_CPC",
        ))
        assert result["data"]["campaign_id"] == "2"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_display_maximize_conversions(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_display_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_display_campaign(
            "123", "Display MaxConv", 40.0,
            bidding_strategy="MAXIMIZE_CONVERSIONS",
            target_cpa_micros=5_000_000,
        ))
        assert result["data"]["campaign_id"] == "2"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_display_target_cpa(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_display_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_display_campaign(
            "123", "Display TargetCPA", 35.0,
            bidding_strategy="TARGET_CPA",
            target_cpa_micros=3_000_000,
        ))
        assert result["data"]["campaign_id"] == "2"

    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", side_effect=Exception("Boom"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_types import create_display_campaign

        result = assert_error(create_display_campaign("123", "Fail", 10.0))
        assert "Failed" in result["error"]


# ---------------------------------------------------------------------------
# TestCreateVideoCampaign
# ---------------------------------------------------------------------------

class TestCreateVideoCampaign:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_video_maximize_conversions(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_video_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_video_campaign("123", "Video Test", 50.0))
        assert result["data"]["campaign_id"] == "2"
        assert result["data"]["status"] == "PAUSED"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_video_target_cpa(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_video_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_video_campaign(
            "123", "Video TargetCPA", 60.0,
            bidding_strategy="TARGET_CPA",
            target_cpa_micros=4_000_000,
        ))
        assert result["data"]["campaign_id"] == "2"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_video_maximize_clicks(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_video_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_video_campaign(
            "123", "Video MaxClicks", 45.0,
            bidding_strategy="MAXIMIZE_CLICKS",
        ))
        assert result["data"]["campaign_id"] == "2"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_video_manual_cpv(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_video_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_video_campaign(
            "123", "Video ManualCPV", 55.0,
            bidding_strategy="MANUAL_CPV",
        ))
        assert result["data"]["campaign_id"] == "2"

    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", side_effect=Exception("Boom"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_types import create_video_campaign

        result = assert_error(create_video_campaign("123", "Fail", 10.0))
        assert "Failed" in result["error"]


# ---------------------------------------------------------------------------
# TestCreateShoppingCampaign
# ---------------------------------------------------------------------------

class TestCreateShoppingCampaign:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_shopping_manual_cpc(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_shopping_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_shopping_campaign(
            "123", "Shopping Test", 100.0, merchant_id="7890",
        ))
        assert result["data"]["campaign_id"] == "2"
        assert result["data"]["status"] == "PAUSED"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_shopping_maximize_clicks(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_shopping_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_shopping_campaign(
            "123", "Shopping MaxClicks", 80.0,
            merchant_id="7890",
            bidding_strategy="MAXIMIZE_CLICKS",
        ))
        assert result["data"]["campaign_id"] == "2"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_shopping_target_roas(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_shopping_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_shopping_campaign(
            "123", "Shopping TargetROAS", 90.0,
            merchant_id="7890",
            bidding_strategy="TARGET_ROAS",
            target_roas=4.5,
        ))
        assert result["data"]["campaign_id"] == "2"

    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", side_effect=Exception("Boom"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_types import create_shopping_campaign

        result = assert_error(create_shopping_campaign("123", "Fail", 10.0, merchant_id="7890"))
        assert "Failed" in result["error"]


# ---------------------------------------------------------------------------
# TestCreateDemandGenCampaign
# ---------------------------------------------------------------------------

class TestCreateDemandGenCampaign:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_demand_gen_maximize_conversions(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_demand_gen_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_demand_gen_campaign("123", "DG Test", 70.0))
        assert result["data"]["campaign_id"] == "2"
        assert result["data"]["status"] == "PAUSED"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_demand_gen_target_cpa(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_demand_gen_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_demand_gen_campaign(
            "123", "DG TargetCPA", 65.0,
            bidding_strategy="TARGET_CPA",
            target_cpa_micros=6_000_000,
        ))
        assert result["data"]["campaign_id"] == "2"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_demand_gen_maximize_conversion_value(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_demand_gen_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_demand_gen_campaign(
            "123", "DG MaxConvValue", 75.0,
            bidding_strategy="MAXIMIZE_CONVERSION_VALUE",
            target_roas=2.5,
        ))
        assert result["data"]["campaign_id"] == "2"

    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", side_effect=Exception("Boom"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_types import create_demand_gen_campaign

        result = assert_error(create_demand_gen_campaign("123", "Fail", 10.0))
        assert "Failed" in result["error"]


# ---------------------------------------------------------------------------
# TestCreateAppCampaign
# ---------------------------------------------------------------------------

class TestCreateAppCampaign:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_app_target_cpa(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_app_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_app_campaign(
            "123", "App Test", 40.0,
            app_id="com.example.app",
            app_store="GOOGLE_APP_STORE",
        ))
        assert result["data"]["campaign_id"] == "2"
        assert result["data"]["status"] == "PAUSED"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_creates_app_maximize_conversions(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_app_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_get_service.side_effect = [_make_budget_service(), _make_campaign_service()]

        result = assert_success(create_app_campaign(
            "123", "App MaxConv", 55.0,
            app_id="com.example.app2",
            app_store="APPLE_APP_STORE",
            bidding_strategy="MAXIMIZE_CONVERSIONS",
            target_cpa_micros=7_000_000,
        ))
        assert result["data"]["campaign_id"] == "2"

    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", side_effect=Exception("Boom"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_types import create_app_campaign

        result = assert_error(create_app_campaign(
            "123", "Fail", 10.0,
            app_id="com.example.fail",
            app_store="GOOGLE_APP_STORE",
        ))
        assert "Failed" in result["error"]

    def test_rejects_invalid_app_store(self):
        from mcp_google_ads.tools.campaign_types import create_app_campaign

        result = assert_error(create_app_campaign(
            "123", "App Bad", 10.0,
            app_id="com.example.bad",
            app_store="DROP TABLE;",
        ))
        assert "Failed" in result["error"]


# ---------------------------------------------------------------------------
# TestCreateAssetGroup
# ---------------------------------------------------------------------------

class TestCreateAssetGroup:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_asset_group

        client = MagicMock()
        mock_client.return_value = client
        mock_response = MagicMock()
        mock_response.mutate_operation_responses = [
            MagicMock(asset_group_result=MagicMock(resource_name="customers/123/assetGroups/999")),
            MagicMock(),
        ]
        mock_service = MagicMock()
        mock_service.mutate.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_asset_group("123", "456", "New AG", ["https://example.com"]))
        assert result["data"]["asset_group_id"] == "999"
        assert "PAUSED" in result["message"]

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_with_paths(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_asset_group

        client = MagicMock()
        mock_client.return_value = client
        mock_response = MagicMock()
        mock_response.mutate_operation_responses = [
            MagicMock(asset_group_result=MagicMock(resource_name="customers/123/assetGroups/999")),
            MagicMock(),
        ]
        mock_service = MagicMock()
        mock_service.mutate.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_asset_group("123", "456", "New AG", ["https://example.com"], path1="sites", path2="pro"))
        assert result["data"]["asset_group_id"] == "999"

    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", side_effect=Exception("API error"))
    def test_error(self, mock_resolve):
        from mcp_google_ads.tools.campaign_types import create_asset_group

        result = assert_error(create_asset_group("123", "456", "AG", ["https://example.com"]))
        assert "Failed to create asset group" in result["error"]


# ---------------------------------------------------------------------------
# TestAddAssetToAssetGroup
# ---------------------------------------------------------------------------

class TestAddAssetToAssetGroup:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import add_asset_to_asset_group

        client = MagicMock()
        mock_client.return_value = client
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assetGroupAssets/456~789~HEADLINE")]
        mock_service = MagicMock()
        mock_service.mutate_asset_group_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(add_asset_to_asset_group("123", "456", "789", "HEADLINE"))
        assert "resource_name" in result["data"]
        assert "linked" in result["message"]

    def test_invalid_field_type(self):
        from mcp_google_ads.tools.campaign_types import add_asset_to_asset_group

        result = assert_error(add_asset_to_asset_group("123", "456", "789", "DROP TABLE"))
        assert "Failed to add asset to asset group" in result["error"]

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import add_asset_to_asset_group

        client = MagicMock()
        mock_client.return_value = client
        mock_service = MagicMock()
        mock_service.mutate_asset_group_assets.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(add_asset_to_asset_group("123", "456", "789", "HEADLINE"))
        assert "Failed to add asset to asset group" in result["error"]


# ---------------------------------------------------------------------------
# TestRemoveAssetFromAssetGroup
# ---------------------------------------------------------------------------

class TestRemoveAssetFromAssetGroup:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import remove_asset_from_asset_group

        client = MagicMock()
        mock_client.return_value = client
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assetGroupAssets/456~789~HEADLINE")]
        mock_service = MagicMock()
        mock_service.mutate_asset_group_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_asset_from_asset_group("123", "456", "789", "HEADLINE"))
        assert "resource_name" in result["data"]

    def test_invalid_id(self):
        from mcp_google_ads.tools.campaign_types import remove_asset_from_asset_group

        result = assert_error(remove_asset_from_asset_group("123", "abc", "789", "HEADLINE"))
        assert "Failed to remove asset from asset group" in result["error"]


# ---------------------------------------------------------------------------
# TestListAssetGroupAssets
# ---------------------------------------------------------------------------

class TestListAssetGroupAssets:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_success(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_types import list_asset_group_assets

        mock_row = MagicMock()
        mock_row.asset.id = 789
        mock_row.asset.name = "Test Headline"
        mock_row.asset_group_asset.field_type.name = "HEADLINE"
        mock_row.asset_group_asset.status.name = "ENABLED"
        mock_row.asset.type_.name = "TEXT"
        mock_row.asset.text_asset.text = "Buy Now"
        mock_row.asset.image_asset.full_size.url = ""

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_asset_group_assets("123", "456"))
        assert result["data"]["count"] == 1
        assert result["data"]["assets"][0]["text"] == "Buy Now"
        assert result["data"]["assets"][0]["field_type"] == "HEADLINE"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_empty(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_types import list_asset_group_assets

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_asset_group_assets("123", "456"))
        assert result["data"]["count"] == 0

    def test_invalid_id(self):
        from mcp_google_ads.tools.campaign_types import list_asset_group_assets

        result = assert_error(list_asset_group_assets("123", "abc"))
        assert "Failed to list asset group assets" in result["error"]


# ---------------------------------------------------------------------------
# TestCreateListingGroupFilter
# ---------------------------------------------------------------------------

class TestCreateListingGroupFilter:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_unit_included(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_listing_group_filter

        client = MagicMock()
        mock_client.return_value = client
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assetGroupListingGroupFilters/456~1")]
        mock_service = MagicMock()
        mock_service.mutate_asset_group_listing_group_filters.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_listing_group_filter("123", "456", "UNIT_INCLUDED"))
        assert "resource_name" in result["data"]

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.get_client")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_with_dimension(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_types import create_listing_group_filter

        client = MagicMock()
        mock_client.return_value = client
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assetGroupListingGroupFilters/456~2")]
        mock_service = MagicMock()
        mock_service.mutate_asset_group_listing_group_filters.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_listing_group_filter(
            "123", "456", "UNIT_INCLUDED",
            parent_filter_id="1",
            dimension_type="product_brand",
            dimension_value="Nike"
        ))
        assert "resource_name" in result["data"]

    def test_invalid_filter_type(self):
        from mcp_google_ads.tools.campaign_types import create_listing_group_filter

        result = assert_error(create_listing_group_filter("123", "456", "DROP TABLE"))
        assert "Failed to create listing group filter" in result["error"]


# ---------------------------------------------------------------------------
# TestListListingGroupFilters
# ---------------------------------------------------------------------------

class TestListListingGroupFilters:
    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_success(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_types import list_listing_group_filters

        mock_row = MagicMock()
        mock_row.asset_group_listing_group_filter.id = 1
        mock_row.asset_group_listing_group_filter.type_.name = "UNIT_INCLUDED"
        mock_row.asset_group_listing_group_filter.parent_listing_group_filter = ""
        mock_row.asset_group_listing_group_filter.resource_name = "customers/123/assetGroupListingGroupFilters/456~1"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_listing_group_filters("123", "456"))
        assert result["data"]["count"] == 1
        assert result["data"]["filters"][0]["type"] == "UNIT_INCLUDED"

    @patch("mcp_google_ads.tools.campaign_types.get_service")
    @patch("mcp_google_ads.tools.campaign_types.resolve_customer_id", return_value="123")
    def test_empty(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_types import list_listing_group_filters

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_listing_group_filters("123", "456"))
        assert result["data"]["count"] == 0

    def test_invalid_id(self):
        from mcp_google_ads.tools.campaign_types import list_listing_group_filters

        result = assert_error(list_listing_group_filters("123", "abc"))
        assert "Failed to list listing group filters" in result["error"]
