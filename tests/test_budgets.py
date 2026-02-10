"""Tests for budgets.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListBudgets:
    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_returns_budgets(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.budgets import list_budgets

        mock_row = MagicMock()
        mock_row.campaign_budget.id = 555
        mock_row.campaign_budget.name = "Budget Diário"
        mock_row.campaign_budget.amount_micros = 50_000_000
        mock_row.campaign_budget.delivery_method.name = "STANDARD"
        mock_row.campaign_budget.status.name = "ENABLED"
        mock_row.campaign_budget.total_amount_micros = 0
        mock_row.campaign_budget.explicitly_shared = False

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_budgets("123"))
        assert result["data"]["count"] == 1
        budgets = result["data"]["budgets"]
        assert len(budgets) == 1
        assert budgets[0]["budget_id"] == "555"
        assert budgets[0]["name"] == "Budget Diário"
        assert budgets[0]["amount_micros"] == 50_000_000
        assert budgets[0]["amount"] == 50.0
        assert budgets[0]["delivery_method"] == "STANDARD"
        assert budgets[0]["status"] == "ENABLED"
        assert budgets[0]["shared"] is False

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_empty_results(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.budgets import list_budgets

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_budgets("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["budgets"] == []

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_multiple_budgets(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.budgets import list_budgets

        rows = []
        for i in range(3):
            row = MagicMock()
            row.campaign_budget.id = 100 + i
            row.campaign_budget.name = f"Budget {i}"
            row.campaign_budget.amount_micros = (i + 1) * 10_000_000
            row.campaign_budget.delivery_method.name = "STANDARD"
            row.campaign_budget.status.name = "ENABLED"
            row.campaign_budget.total_amount_micros = 0
            row.campaign_budget.explicitly_shared = False
            rows.append(row)

        mock_service = MagicMock()
        mock_service.search.return_value = rows
        mock_get_service.return_value = mock_service

        result = assert_success(list_budgets("123"))
        assert result["data"]["count"] == 3
        assert result["data"]["budgets"][0]["budget_id"] == "100"
        assert result["data"]["budgets"][1]["budget_id"] == "101"
        assert result["data"]["budgets"][2]["budget_id"] == "102"

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_format_micros_conversion(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.budgets import list_budgets

        mock_row = MagicMock()
        mock_row.campaign_budget.id = 555
        mock_row.campaign_budget.name = "Test"
        mock_row.campaign_budget.amount_micros = 123_456_789
        mock_row.campaign_budget.delivery_method.name = "STANDARD"
        mock_row.campaign_budget.status.name = "ENABLED"
        mock_row.campaign_budget.total_amount_micros = 0
        mock_row.campaign_budget.explicitly_shared = False

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_budgets("123"))
        assert result["data"]["budgets"][0]["amount"] == 123.46
        assert result["data"]["budgets"][0]["amount_micros"] == 123_456_789

    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.budgets import list_budgets

        result = assert_error(list_budgets(""))
        assert "Failed to list budgets" in result["error"]

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_validate_limit_default(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.budgets import list_budgets

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(list_budgets("123"))
        call_args = mock_service.search.call_args
        assert "LIMIT 100" in call_args.kwargs["query"]

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_validate_limit_custom(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.budgets import list_budgets

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(list_budgets("123", limit=50))
        call_args = mock_service.search.call_args
        assert "LIMIT 50" in call_args.kwargs["query"]

    def test_validate_limit_invalid_zero(self):
        from mcp_google_ads.tools.budgets import list_budgets

        result = assert_error(list_budgets("123", limit=0))
        assert "Failed to list budgets" in result["error"]

    def test_validate_limit_invalid_negative(self):
        from mcp_google_ads.tools.budgets import list_budgets

        result = assert_error(list_budgets("123", limit=-1))
        assert "Failed to list budgets" in result["error"]


class TestGetBudget:
    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_returns_budget(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.budgets import get_budget

        mock_row = MagicMock()
        mock_row.campaign_budget.id = 555
        mock_row.campaign_budget.name = "Budget Principal"
        mock_row.campaign_budget.amount_micros = 75_000_000
        mock_row.campaign_budget.delivery_method.name = "STANDARD"
        mock_row.campaign_budget.status.name = "ENABLED"
        mock_row.campaign_budget.explicitly_shared = True
        mock_row.campaign_budget.reference_count = 3
        mock_row.campaign_budget.recommended_budget_amount_micros = 100_000_000
        mock_row.campaign_budget.recommended_budget_estimated_change_weekly_clicks = 50

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_budget("123", "555"))
        data = result["data"]
        assert data["budget_id"] == "555"
        assert data["name"] == "Budget Principal"
        assert data["amount_micros"] == 75_000_000
        assert data["amount"] == 75.0
        assert data["delivery_method"] == "STANDARD"
        assert data["status"] == "ENABLED"
        assert data["shared"] is True
        assert data["reference_count"] == 3
        assert data["recommended_amount_micros"] == 100_000_000
        assert data["recommended_change_weekly_clicks"] == 50

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_budget_not_found(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.budgets import get_budget

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_error(get_budget("123", "999"))
        assert "Budget 999 not found" in result["error"]

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_format_micros_in_get(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.budgets import get_budget

        mock_row = MagicMock()
        mock_row.campaign_budget.id = 555
        mock_row.campaign_budget.name = "Test"
        mock_row.campaign_budget.amount_micros = 1_500_000
        mock_row.campaign_budget.delivery_method.name = "STANDARD"
        mock_row.campaign_budget.status.name = "ENABLED"
        mock_row.campaign_budget.explicitly_shared = False
        mock_row.campaign_budget.reference_count = 1
        mock_row.campaign_budget.recommended_budget_amount_micros = 0
        mock_row.campaign_budget.recommended_budget_estimated_change_weekly_clicks = 0

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_budget("123", "555"))
        assert result["data"]["amount"] == 1.5

    def test_rejects_invalid_budget_id(self):
        from mcp_google_ads.tools.budgets import get_budget

        result = assert_error(get_budget("123", "abc"))
        assert "Failed to get budget" in result["error"]

    def test_rejects_special_chars_budget_id(self):
        from mcp_google_ads.tools.budgets import get_budget

        result = assert_error(get_budget("123", "555; DROP TABLE"))
        assert "Failed to get budget" in result["error"]

    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.budgets import get_budget

        result = assert_error(get_budget("", "555"))
        assert "Failed to get budget" in result["error"]

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_validate_numeric_id_with_hyphens(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.budgets import get_budget

        mock_row = MagicMock()
        mock_row.campaign_budget.id = 555
        mock_row.campaign_budget.name = "Test"
        mock_row.campaign_budget.amount_micros = 10_000_000
        mock_row.campaign_budget.delivery_method.name = "STANDARD"
        mock_row.campaign_budget.status.name = "ENABLED"
        mock_row.campaign_budget.explicitly_shared = False
        mock_row.campaign_budget.reference_count = 0
        mock_row.campaign_budget.recommended_budget_amount_micros = 0
        mock_row.campaign_budget.recommended_budget_estimated_change_weekly_clicks = 0

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        assert_success(get_budget("123", "5-5-5"))
        call_args = mock_service.search.call_args
        assert "555" in call_args.kwargs["query"]


class TestCreateBudget:
    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_creates_budget(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import create_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/777")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_budgets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_budget("123", "Novo Budget", 50.0))
        assert result["data"]["budget_id"] == "777"
        assert result["data"]["resource_name"] == "customers/123/campaignBudgets/777"
        assert "Novo Budget" in result["message"]
        assert "50.0" in result["message"]

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_creates_shared_budget(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import create_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/888")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_budgets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_budget("123", "Shared Budget", 100.0, shared=True))
        assert result["data"]["budget_id"] == "888"

        operation = client.get_type("CampaignBudgetOperation")
        assert operation.create.explicitly_shared is True

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_creates_with_standard_delivery(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import create_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/999")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_budgets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_budget("123", "Test", 25.0, delivery_method="STANDARD"))
        assert result["data"]["budget_id"] == "999"

    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_rejects_invalid_delivery_method(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.budgets import create_budget

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(create_budget("123", "Test", 25.0, delivery_method="DROP; --"))
        assert "Failed to create budget" in result["error"]

    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.budgets import create_budget

        result = assert_error(create_budget("", "Test", 50.0))
        assert "Failed to create budget" in result["error"]

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_to_micros_conversion(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import create_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/111")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_budgets.return_value = mock_response
        mock_get_service.return_value = mock_service

        assert_success(create_budget("123", "Test", 75.50))

        operation = client.get_type("CampaignBudgetOperation")
        assert operation.create.amount_micros == 75_500_000


class TestUpdateBudget:
    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_updates_amount(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import update_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/555")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_budgets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_budget("123", "555", amount=100.0))
        assert result["data"]["resource_name"] == "customers/123/campaignBudgets/555"
        assert "Budget 555 updated" in result["message"]

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_updates_name(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import update_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/555")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_budgets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_budget("123", "555", name="Novo Nome"))
        assert "Budget 555 updated" in result["message"]

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_updates_delivery_method(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import update_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/555")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_budgets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_budget("123", "555", delivery_method="STANDARD"))
        assert "Budget 555 updated" in result["message"]

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_updates_multiple_fields(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import update_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/555")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_budgets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            update_budget("123", "555", amount=200.0, name="Atualizado", delivery_method="STANDARD")
        )
        assert "Budget 555 updated" in result["message"]

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_no_fields_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import update_budget

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(update_budget("123", "555"))
        assert "No fields to update" in result["error"]

    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_rejects_invalid_delivery_method(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.budgets import update_budget

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(update_budget("123", "555", delivery_method="INVALID;SQL"))
        assert "Failed to update budget" in result["error"]

    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.budgets import update_budget

        result = assert_error(update_budget("", "555", amount=50.0))
        assert "Failed to update budget" in result["error"]

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_resource_name_construction(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import update_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/555")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_budgets.return_value = mock_response
        mock_get_service.return_value = mock_service

        assert_success(update_budget("123", "555", amount=30.0))

        operation = client.get_type("CampaignBudgetOperation")
        assert operation.update.resource_name == "customers/123/campaignBudgets/555"

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_to_micros_conversion_on_update(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import update_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/555")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_budgets.return_value = mock_response
        mock_get_service.return_value = mock_service

        assert_success(update_budget("123", "555", amount=42.75))

        operation = client.get_type("CampaignBudgetOperation")
        assert operation.update.amount_micros == 42_750_000

    @patch("mcp_google_ads.tools.budgets.get_service")
    @patch("mcp_google_ads.tools.budgets.get_client")
    @patch("mcp_google_ads.tools.budgets.resolve_customer_id", return_value="123")
    def test_field_mask_contains_updated_fields(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.budgets import update_budget

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignBudgets/555")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_budgets.return_value = mock_response
        mock_get_service.return_value = mock_service

        update_budget("123", "555", amount=50.0, name="Test")

        # copy_from deve ter sido chamado com o field mask
        assert client.copy_from.called
