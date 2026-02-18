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

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_com_status_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaigns

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(list_campaigns("123", status_filter="ENABLED"))
        query_usado = mock_service.search.call_args[1]["query"]
        assert "campaign.status = 'ENABLED'" in query_usado

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_status_filter_invalido(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaigns

        result = assert_error(list_campaigns("123", status_filter="INVALID"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_api_exception(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaigns

        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(list_campaigns("123"))
        assert "Failed to list campaigns" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_multiplas_campaigns(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaigns

        row1 = MagicMock()
        row1.campaign.id = 111
        row1.campaign.name = "Campaign A"
        row1.campaign.status.name = "ENABLED"
        row1.campaign.advertising_channel_type.name = "SEARCH"
        row1.campaign.bidding_strategy_type.name = "MANUAL_CPC"
        row1.campaign_budget.amount_micros = 50_000_000

        row2 = MagicMock()
        row2.campaign.id = 222
        row2.campaign.name = "Campaign B"
        row2.campaign.status.name = "PAUSED"
        row2.campaign.advertising_channel_type.name = "DISPLAY"
        row2.campaign.bidding_strategy_type.name = "MAXIMIZE_CLICKS"
        row2.campaign_budget.amount_micros = 100_000_000

        mock_service = MagicMock()
        mock_service.search.return_value = [row1, row2]
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaigns("123"))
        assert result["data"]["count"] == 2
        assert result["data"]["campaigns"][0]["name"] == "Campaign A"
        assert result["data"]["campaigns"][1]["name"] == "Campaign B"
        assert result["data"]["campaigns"][1]["budget"] == 100.0


class TestGetCampaign:
    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_retorna_campaign_detalhada(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import get_campaign

        mock_row = MagicMock()
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Test Campaign"
        mock_row.campaign.status.name = "ENABLED"
        mock_row.campaign.advertising_channel_type.name = "SEARCH"
        mock_row.campaign.advertising_channel_sub_type.name = "SEARCH_STANDARD"
        mock_row.campaign.bidding_strategy_type.name = "MANUAL_CPC"
        mock_row.campaign_budget.amount_micros = 50_000_000
        mock_row.campaign_budget.delivery_method.name = "STANDARD"
        mock_row.campaign.serving_status.name = "SERVING"
        mock_row.campaign.network_settings.target_google_search = True
        mock_row.campaign.network_settings.target_search_network = False
        mock_row.campaign.network_settings.target_content_network = False

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_campaign("123", "111"))
        data = result["data"]
        assert data["campaign_id"] == "111"
        assert data["name"] == "Test Campaign"
        assert data["status"] == "ENABLED"
        assert data["channel_type"] == "SEARCH"
        assert data["budget"] == 50.0
        assert data["budget_delivery"] == "STANDARD"
        assert data["serving_status"] == "SERVING"
        assert data["target_google_search"] is True
        assert data["target_search_network"] is False

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_campaign_nao_encontrada(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import get_campaign

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_error(get_campaign("123", "999"))
        assert "not found" in result["error"]

    def test_campaign_id_invalido(self):
        from mcp_google_ads.tools.campaigns import get_campaign

        result = assert_error(get_campaign("123", "abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_api_exception(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import get_campaign

        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("Permission denied")
        mock_get_service.return_value = mock_service

        result = assert_error(get_campaign("123", "111"))
        assert "Failed to get campaign" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_query_contem_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import get_campaign

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        get_campaign("123", "555")
        query_usado = mock_service.search.call_args[1]["query"]
        assert "campaign.id = 555" in query_usado


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

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_create_com_maximize_clicks(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import create_campaign

        client = MagicMock()
        mock_client.return_value = client

        budget_response = MagicMock()
        budget_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/1")]
        budget_service = MagicMock()
        budget_service.mutate_campaign_budgets.return_value = budget_response

        campaign_response = MagicMock()
        campaign_response.results = [MagicMock(resource_name="customers/123/campaigns/333")]
        campaign_service = MagicMock()
        campaign_service.mutate_campaigns.return_value = campaign_response

        mock_get_service.side_effect = lambda name: {
            "CampaignBudgetService": budget_service,
            "CampaignService": campaign_service,
        }[name]

        result = assert_success(
            create_campaign("123", "Maximize Test", 100.0, bidding_strategy="MAXIMIZE_CLICKS")
        )
        assert result["data"]["campaign_id"] == "333"

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_create_com_target_cpa(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import create_campaign

        client = MagicMock()
        mock_client.return_value = client

        budget_response = MagicMock()
        budget_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/1")]
        budget_service = MagicMock()
        budget_service.mutate_campaign_budgets.return_value = budget_response

        campaign_response = MagicMock()
        campaign_response.results = [MagicMock(resource_name="customers/123/campaigns/444")]
        campaign_service = MagicMock()
        campaign_service.mutate_campaigns.return_value = campaign_response

        mock_get_service.side_effect = lambda name: {
            "CampaignBudgetService": budget_service,
            "CampaignService": campaign_service,
        }[name]

        result = assert_success(
            create_campaign(
                "123", "CPA Test", 100.0,
                bidding_strategy="TARGET_CPA",
                target_cpa_micros=5_000_000,
            )
        )
        assert result["data"]["campaign_id"] == "444"

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_create_com_target_roas(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import create_campaign

        client = MagicMock()
        mock_client.return_value = client

        budget_response = MagicMock()
        budget_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/1")]
        budget_service = MagicMock()
        budget_service.mutate_campaign_budgets.return_value = budget_response

        campaign_response = MagicMock()
        campaign_response.results = [MagicMock(resource_name="customers/123/campaigns/555")]
        campaign_service = MagicMock()
        campaign_service.mutate_campaigns.return_value = campaign_response

        mock_get_service.side_effect = lambda name: {
            "CampaignBudgetService": budget_service,
            "CampaignService": campaign_service,
        }[name]

        result = assert_success(
            create_campaign(
                "123", "ROAS Test", 100.0,
                bidding_strategy="TARGET_ROAS",
                target_roas=3.0,
            )
        )
        assert result["data"]["campaign_id"] == "555"

    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaigns import create_campaign

        result = assert_error(create_campaign("", "Test", 50.0))
        assert "Failed to create campaign" in result["error"]


class TestUpdateCampaign:
    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_atualiza_nome(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import update_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaigns/111")]
        mock_service.mutate_campaigns.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_campaign("123", "111", name="Novo Nome"))
        assert "updated" in result["message"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_atualiza_datas(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import update_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaigns/111")]
        mock_service.mutate_campaigns.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            update_campaign("123", "111", start_date="2024-06-01", end_date="2024-12-31")
        )
        assert "updated" in result["message"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_atualiza_network_settings(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import update_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaigns/111")]
        mock_service.mutate_campaigns.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            update_campaign(
                "123", "111",
                network_search=True,
                network_search_partners=True,
                network_display=False,
            )
        )
        assert "updated" in result["message"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_sem_campos_retorna_erro(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import update_campaign

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(update_campaign("123", "111"))
        assert "No fields to update" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_api_exception(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import update_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_campaigns.side_effect = Exception("Mutate failed")
        mock_get_service.return_value = mock_service

        result = assert_error(update_campaign("123", "111", name="Novo"))
        assert "Failed to update campaign" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", side_effect=Exception("No ID"))
    def test_resolve_error(self, mock_resolve):
        from mcp_google_ads.tools.campaigns import update_campaign

        result = assert_error(update_campaign("", "111", name="Novo"))
        assert "Failed to update campaign" in result["error"]


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

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_sets_enabled(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import set_campaign_status

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaigns/111")]
        mock_service.mutate_campaigns.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(set_campaign_status("123", "111", "ENABLED"))
        assert result["data"]["new_status"] == "ENABLED"

    def test_status_invalido(self):
        from mcp_google_ads.tools.campaigns import set_campaign_status

        result = assert_error(set_campaign_status("123", "111", "INVALID_STATUS"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_api_exception(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import set_campaign_status

        mock_service = MagicMock()
        mock_service.mutate_campaigns.side_effect = Exception("Mutate error")
        mock_get_service.return_value = mock_service

        result = assert_error(set_campaign_status("123", "111", "PAUSED"))
        assert "Failed to set campaign status" in result["error"]


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

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_api_exception(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import remove_campaign

        mock_service = MagicMock()
        mock_service.mutate_campaigns.side_effect = Exception("Cannot remove")
        mock_get_service.return_value = mock_service

        result = assert_error(remove_campaign("123", "111"))
        assert "Failed to remove campaign" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", side_effect=Exception("No ID"))
    def test_resolve_error(self, mock_resolve):
        from mcp_google_ads.tools.campaigns import remove_campaign

        result = assert_error(remove_campaign("", "111"))
        assert "Failed to remove campaign" in result["error"]


class TestListCampaignLabels:
    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_retorna_labels(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaign_labels

        mock_row = MagicMock()
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Test Campaign"
        mock_row.label.id = 555
        mock_row.label.name = "Importante"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_labels("123"))
        assert result["data"]["count"] == 1
        label = result["data"]["labels"][0]
        assert label["campaign_id"] == "111"
        assert label["campaign_name"] == "Test Campaign"
        assert label["label_id"] == "555"
        assert label["label_name"] == "Importante"

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_com_campaign_id_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaign_labels

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(list_campaign_labels("123", campaign_id="111"))
        query_usado = mock_service.search.call_args[1]["query"]
        assert "campaign.id = 111" in query_usado

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_sem_resultados(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaign_labels

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_labels("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["labels"] == []

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_campaign_id_invalido(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaign_labels

        result = assert_error(list_campaign_labels("123", campaign_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_api_exception(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaign_labels

        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("Query failed")
        mock_get_service.return_value = mock_service

        result = assert_error(list_campaign_labels("123"))
        assert "Failed to list campaign labels" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_multiplas_labels(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaigns import list_campaign_labels

        row1 = MagicMock()
        row1.campaign.id = 111
        row1.campaign.name = "C1"
        row1.label.id = 501
        row1.label.name = "Label A"

        row2 = MagicMock()
        row2.campaign.id = 111
        row2.campaign.name = "C1"
        row2.label.id = 502
        row2.label.name = "Label B"

        mock_service = MagicMock()
        mock_service.search.return_value = [row1, row2]
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_labels("123"))
        assert result["data"]["count"] == 2
        assert result["data"]["labels"][0]["label_name"] == "Label A"
        assert result["data"]["labels"][1]["label_name"] == "Label B"


class TestSetCampaignTrackingTemplate:
    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_sets_tracking_template(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import set_campaign_tracking_template

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaigns/111")]
        mock_service.mutate_campaigns.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            set_campaign_tracking_template("123", "111", "{lpurl}?utm_source=google")
        )
        assert "Tracking template set" in result["message"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_with_custom_parameters(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import set_campaign_tracking_template

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaigns/111")]
        mock_service.mutate_campaigns.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            set_campaign_tracking_template(
                "123", "111", "{lpurl}?utm_campaign={_campaign}",
                custom_parameters=[{"key": "campaign", "value": "test_campaign"}],
            )
        )
        assert "Tracking template set" in result["message"]

    def test_invalid_campaign_id(self):
        from mcp_google_ads.tools.campaigns import set_campaign_tracking_template

        result = assert_error(
            set_campaign_tracking_template("123", "abc", "{lpurl}?utm_source=google")
        )
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_api_exception(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import set_campaign_tracking_template

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_campaigns.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(
            set_campaign_tracking_template("123", "111", "{lpurl}?utm_source=google")
        )
        assert "Failed to set campaign tracking template" in result["error"]


class TestCloneCampaign:
    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_clones_basic(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import clone_campaign

        client = MagicMock()
        mock_client.return_value = client

        source_row = MagicMock()
        source_row.campaign.id = 111
        source_row.campaign.name = "Original"
        source_row.campaign.advertising_channel_type = MagicMock()
        source_row.campaign.bidding_strategy_type.name = "MANUAL_CPC"
        source_row.campaign.network_settings.target_google_search = True
        source_row.campaign.network_settings.target_search_network = False
        source_row.campaign.network_settings.target_content_network = False
        source_row.campaign_budget.amount_micros = 50_000_000

        search_service = MagicMock()
        search_service.search.return_value = [source_row]

        budget_service = MagicMock()
        budget_response = MagicMock()
        budget_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/99")]
        budget_service.mutate_campaign_budgets.return_value = budget_response

        campaign_service = MagicMock()
        campaign_response = MagicMock()
        campaign_response.results = [MagicMock(resource_name="customers/123/campaigns/222")]
        campaign_service.mutate_campaigns.return_value = campaign_response

        mock_get_service.side_effect = lambda name: {
            "GoogleAdsService": search_service,
            "CampaignBudgetService": budget_service,
            "CampaignService": campaign_service,
        }[name]

        result = assert_success(clone_campaign("123", "111", copy_ad_groups=False))
        assert result["data"]["new_campaign_id"] == "222"
        assert result["data"]["status"] == "PAUSED"

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_source_not_found(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import clone_campaign

        client = MagicMock()
        mock_client.return_value = client

        search_service = MagicMock()
        search_service.search.return_value = []
        mock_get_service.return_value = search_service

        result = assert_error(clone_campaign("123", "999"))
        assert "not found" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.get_service")
    @patch("mcp_google_ads.tools.campaigns.get_client")
    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", return_value="123")
    def test_custom_name_and_budget(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaigns import clone_campaign

        client = MagicMock()
        mock_client.return_value = client

        source_row = MagicMock()
        source_row.campaign.id = 111
        source_row.campaign.name = "Original"
        source_row.campaign.advertising_channel_type = MagicMock()
        source_row.campaign.bidding_strategy_type.name = "MAXIMIZE_CLICKS"
        source_row.campaign.network_settings.target_google_search = True
        source_row.campaign.network_settings.target_search_network = False
        source_row.campaign.network_settings.target_content_network = False
        source_row.campaign_budget.amount_micros = 50_000_000

        search_service = MagicMock()
        search_service.search.return_value = [source_row]

        budget_service = MagicMock()
        budget_response = MagicMock()
        budget_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/99")]
        budget_service.mutate_campaign_budgets.return_value = budget_response

        campaign_service = MagicMock()
        campaign_response = MagicMock()
        campaign_response.results = [MagicMock(resource_name="customers/123/campaigns/333")]
        campaign_service.mutate_campaigns.return_value = campaign_response

        mock_get_service.side_effect = lambda name: {
            "GoogleAdsService": search_service,
            "CampaignBudgetService": budget_service,
            "CampaignService": campaign_service,
        }[name]

        result = assert_success(
            clone_campaign("123", "111", new_name="Custom Clone", budget_amount=100.0, copy_ad_groups=False)
        )
        assert result["data"]["new_campaign_id"] == "333"
        assert "Custom Clone" in result["message"]

    def test_invalid_campaign_id(self):
        from mcp_google_ads.tools.campaigns import clone_campaign

        result = assert_error(clone_campaign("123", "abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.campaigns.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaigns import clone_campaign

        result = assert_error(clone_campaign("", "111"))
        assert "Failed to clone campaign" in result["error"]
