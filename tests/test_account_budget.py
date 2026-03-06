"""Tests for account_budget.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListAccountBudgets:
    @patch("mcp_google_ads.tools.account_budget.get_service")
    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", return_value="123")
    def test_returns_budgets(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.account_budget import list_account_budgets

        mock_row = MagicMock()
        mock_row.account_budget.resource_name = "customers/123/accountBudgets/1"
        mock_row.account_budget.id = 1
        mock_row.account_budget.name = "Q1 Budget"
        mock_row.account_budget.status.name = "APPROVED"
        mock_row.account_budget.amount_micros = 5000000000
        mock_row.account_budget.total_adjustments_micros = 100000000
        mock_row.account_budget.approved_start_date_time = "2024-01-01 00:00:00"
        mock_row.account_budget.approved_end_date_time = "2024-03-31 23:59:59"
        mock_row.account_budget.proposed_start_date_time = "2024-01-01 00:00:00"
        mock_row.account_budget.proposed_end_date_time = "2024-03-31 23:59:59"
        mock_row.account_budget.approved_spending_limit_micros = 5000000000
        mock_row.account_budget.proposed_spending_limit_micros = 5000000000
        mock_row.account_budget.purchase_order_number = "PO-001"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_account_budgets("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["account_budgets"][0]["name"] == "Q1 Budget"
        assert result["data"]["account_budgets"][0]["amount"] == 5000.0
        assert result["data"]["account_budgets"][0]["status"] == "APPROVED"

    @patch("mcp_google_ads.tools.account_budget.get_service")
    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", return_value="123")
    def test_returns_empty_list(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.account_budget import list_account_budgets

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_account_budgets("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["account_budgets"] == []

    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.account_budget import list_account_budgets

        result = assert_error(list_account_budgets(""))
        assert "Failed to list account budgets" in result["error"]


class TestGetAccountBudget:
    @patch("mcp_google_ads.tools.account_budget.get_service")
    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", return_value="123")
    def test_returns_budget(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.account_budget import get_account_budget

        mock_row = MagicMock()
        mock_row.account_budget.resource_name = "customers/123/accountBudgets/42"
        mock_row.account_budget.id = 42
        mock_row.account_budget.name = "Annual Budget"
        mock_row.account_budget.status.name = "APPROVED"
        mock_row.account_budget.amount_micros = 10000000000
        mock_row.account_budget.total_adjustments_micros = 0
        mock_row.account_budget.approved_start_date_time = "2024-01-01 00:00:00"
        mock_row.account_budget.approved_end_date_time = "2024-12-31 23:59:59"
        mock_row.account_budget.proposed_start_date_time = "2024-01-01 00:00:00"
        mock_row.account_budget.proposed_end_date_time = "2024-12-31 23:59:59"
        mock_row.account_budget.approved_spending_limit_micros = 10000000000
        mock_row.account_budget.proposed_spending_limit_micros = 10000000000
        mock_row.account_budget.purchase_order_number = "PO-002"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_account_budget("123", "42"))
        assert result["data"]["name"] == "Annual Budget"
        assert result["data"]["id"] == 42
        assert result["data"]["amount"] == 10000.0

    @patch("mcp_google_ads.tools.account_budget.get_service")
    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", return_value="123")
    def test_not_found(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.account_budget import get_account_budget

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_error(get_account_budget("123", "999"))
        assert "not found" in result["error"]

    def test_rejects_invalid_id(self):
        from mcp_google_ads.tools.account_budget import get_account_budget

        result = assert_error(get_account_budget("123", "abc"))
        assert "Failed to get account budget" in result["error"]


class TestListAccountBudgetProposals:
    @patch("mcp_google_ads.tools.account_budget.get_service")
    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", return_value="123")
    def test_returns_proposals(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.account_budget import list_account_budget_proposals

        mock_row = MagicMock()
        mock_row.account_budget_proposal.resource_name = "customers/123/accountBudgetProposals/10"
        mock_row.account_budget_proposal.id = 10
        mock_row.account_budget_proposal.account_budget = "customers/123/accountBudgets/1"
        mock_row.account_budget_proposal.proposal_type.name = "CREATE"
        mock_row.account_budget_proposal.status.name = "APPROVED"
        mock_row.account_budget_proposal.proposed_name = "New Budget"
        mock_row.account_budget_proposal.proposed_start_date_time = "2024-01-01 00:00:00"
        mock_row.account_budget_proposal.proposed_end_date_time = "2024-06-30 23:59:59"
        mock_row.account_budget_proposal.proposed_spending_limit_micros = 3000000000
        mock_row.account_budget_proposal.proposed_purchase_order_number = "PO-003"
        mock_row.account_budget_proposal.approved_start_date_time = "2024-01-01 00:00:00"
        mock_row.account_budget_proposal.approved_end_date_time = "2024-06-30 23:59:59"
        mock_row.account_budget_proposal.approved_spending_limit_micros = 3000000000
        mock_row.account_budget_proposal.creation_date_time = "2023-12-15 10:00:00"
        mock_row.account_budget_proposal.approval_date_time = "2023-12-16 14:30:00"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_account_budget_proposals("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["proposals"][0]["proposed_name"] == "New Budget"
        assert result["data"]["proposals"][0]["proposal_type"] == "CREATE"
        assert result["data"]["proposals"][0]["proposed_spending_limit"] == 3000.0

    @patch("mcp_google_ads.tools.account_budget.get_service")
    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", return_value="123")
    def test_returns_empty_list(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.account_budget import list_account_budget_proposals

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_account_budget_proposals("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["proposals"] == []

    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", side_effect=Exception("Auth error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.account_budget import list_account_budget_proposals

        result = assert_error(list_account_budget_proposals(""))
        assert "Failed to list account budget proposals" in result["error"]


class TestCreateAccountBudgetProposal:
    @patch("mcp_google_ads.tools.account_budget.get_service")
    @patch("mcp_google_ads.tools.account_budget.get_client")
    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", return_value="123")
    def test_creates_proposal_basic(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.account_budget import create_account_budget_proposal

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.result.resource_name = "customers/123/accountBudgetProposals/50"
        mock_service = MagicMock()
        mock_service.mutate_account_budget_proposal.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_account_budget_proposal("123", "CREATE", "777", spending_limit=1000.0, name="Test Budget")
        )
        assert result["data"]["proposal_id"] == "50"
        assert result["data"]["proposal_type"] == "CREATE"
        mock_service.mutate_account_budget_proposal.assert_called_once()

        # Verifica que billing_setup foi atribuido
        operation = client.get_type.return_value
        assert operation.create.billing_setup == "customers/123/billingSetups/777"
        assert operation.create.proposed_name == "Test Budget"
        assert operation.create.proposed_spending_limit_micros == 1000000000

    @patch("mcp_google_ads.tools.account_budget.get_service")
    @patch("mcp_google_ads.tools.account_budget.get_client")
    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", return_value="123")
    def test_creates_proposal_with_dates(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.account_budget import create_account_budget_proposal

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.result.resource_name = "customers/123/accountBudgetProposals/51"
        mock_service = MagicMock()
        mock_service.mutate_account_budget_proposal.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_account_budget_proposal(
                "123",
                "CREATE",
                "777",
                spending_limit=2000.0,
                start_date_time="2024-01-01 00:00:00",
                end_date_time="2024-06-30 23:59:59",
            )
        )
        assert result["data"]["proposal_id"] == "51"

        operation = client.get_type.return_value
        assert operation.create.proposed_start_date_time == "2024-01-01 00:00:00"
        assert operation.create.proposed_end_date_time == "2024-06-30 23:59:59"

    @patch("mcp_google_ads.tools.account_budget.get_service")
    @patch("mcp_google_ads.tools.account_budget.get_client")
    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", return_value="123")
    def test_creates_update_proposal_with_account_budget(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.account_budget import create_account_budget_proposal

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.result.resource_name = "customers/123/accountBudgetProposals/52"
        mock_service = MagicMock()
        mock_service.mutate_account_budget_proposal.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_account_budget_proposal(
                "123", "UPDATE", "777", spending_limit=5000.0, account_budget_id="99"
            )
        )
        assert result["data"]["proposal_id"] == "52"
        assert result["data"]["proposal_type"] == "UPDATE"

        operation = client.get_type.return_value
        assert operation.create.account_budget == "customers/123/accountBudgets/99"

    def test_rejects_invalid_proposal_type(self):
        from mcp_google_ads.tools.account_budget import create_account_budget_proposal

        result = assert_error(create_account_budget_proposal("123", "DROP TABLE", "777"))
        assert "Failed to create account budget proposal" in result["error"]

    def test_rejects_invalid_billing_setup_id(self):
        from mcp_google_ads.tools.account_budget import create_account_budget_proposal

        result = assert_error(create_account_budget_proposal("123", "CREATE", "abc"))
        assert "Failed to create account budget proposal" in result["error"]

    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.account_budget import create_account_budget_proposal

        result = assert_error(create_account_budget_proposal("123", "CREATE", "777"))
        assert "Failed to create account budget proposal" in result["error"]


class TestRemoveAccountBudgetProposal:
    @patch("mcp_google_ads.tools.account_budget.get_service")
    @patch("mcp_google_ads.tools.account_budget.get_client")
    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", return_value="123")
    def test_removes_proposal(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.account_budget import remove_account_budget_proposal

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.result.resource_name = "customers/123/accountBudgetProposals/60"
        mock_service = MagicMock()
        mock_service.mutate_account_budget_proposal.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_account_budget_proposal("123", "60"))
        assert result["data"]["action"] == "removed"
        assert result["data"]["proposal_id"] == "60"
        mock_service.mutate_account_budget_proposal.assert_called_once()

        # Verifica que o remove resource name foi montado corretamente
        operation = client.get_type.return_value
        assert operation.remove == "customers/123/accountBudgetProposals/60"

    def test_rejects_invalid_id(self):
        from mcp_google_ads.tools.account_budget import remove_account_budget_proposal

        result = assert_error(remove_account_budget_proposal("123", "abc"))
        assert "Failed to remove account budget proposal" in result["error"]

    @patch("mcp_google_ads.tools.account_budget.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.account_budget import remove_account_budget_proposal

        result = assert_error(remove_account_budget_proposal("123", "60"))
        assert "Failed to remove account budget proposal" in result["error"]
