"""Tests for accounts.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListAccessibleCustomers:
    @patch("mcp_google_ads.tools.accounts.get_service")
    def test_returns_customer_ids(self, mock_get_service):
        from mcp_google_ads.tools.accounts import list_accessible_customers

        mock_service = MagicMock()
        mock_service.list_accessible_customers.return_value = MagicMock(
            resource_names=["customers/111", "customers/222", "customers/333"]
        )
        mock_get_service.return_value = mock_service

        result = assert_success(list_accessible_customers())
        assert result["data"]["count"] == 3
        assert result["data"]["customer_ids"] == ["111", "222", "333"]
        assert result["message"] == "Accessible customers retrieved"

    @patch("mcp_google_ads.tools.accounts.get_service")
    def test_empty_results(self, mock_get_service):
        from mcp_google_ads.tools.accounts import list_accessible_customers

        mock_service = MagicMock()
        mock_service.list_accessible_customers.return_value = MagicMock(
            resource_names=[]
        )
        mock_get_service.return_value = mock_service

        result = assert_success(list_accessible_customers())
        assert result["data"]["count"] == 0
        assert result["data"]["customer_ids"] == []

    @patch("mcp_google_ads.tools.accounts.get_service", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_get_service):
        from mcp_google_ads.tools.accounts import list_accessible_customers

        result = assert_error(list_accessible_customers())
        assert "Failed to list accessible customers" in result["error"]


class TestGetCustomerInfo:
    @patch("mcp_google_ads.tools.accounts.get_service")
    @patch("mcp_google_ads.tools.accounts.resolve_customer_id", return_value="123")
    def test_returns_customer_info(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.accounts import get_customer_info

        mock_row = MagicMock()
        mock_row.customer.id = 123
        mock_row.customer.descriptive_name = "Conta Teste"
        mock_row.customer.currency_code = "BRL"
        mock_row.customer.time_zone = "America/Sao_Paulo"
        mock_row.customer.status.name = "ENABLED"
        mock_row.customer.manager = False
        mock_row.customer.test_account = True
        mock_row.customer.auto_tagging_enabled = False

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_customer_info("123"))
        data = result["data"]
        assert data["customer_id"] == "123"
        assert data["name"] == "Conta Teste"
        assert data["currency"] == "BRL"
        assert data["timezone"] == "America/Sao_Paulo"
        assert data["status"] == "ENABLED"
        assert data["is_manager"] is False
        assert data["is_test_account"] is True
        assert data["auto_tagging"] is False

    @patch("mcp_google_ads.tools.accounts.get_service")
    @patch("mcp_google_ads.tools.accounts.resolve_customer_id", return_value="123")
    def test_no_customer_data(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.accounts import get_customer_info

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_error(get_customer_info("123"))
        assert "No customer data found" in result["error"]

    @patch("mcp_google_ads.tools.accounts.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.accounts import get_customer_info

        result = assert_error(get_customer_info(""))
        assert "Failed to get customer info" in result["error"]


class TestGetAccountHierarchy:
    @patch("mcp_google_ads.tools.accounts.get_service")
    @patch("mcp_google_ads.tools.accounts.resolve_customer_id", return_value="123")
    def test_returns_hierarchy(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.accounts import get_account_hierarchy

        mock_row_mcc = MagicMock()
        mock_row_mcc.customer_client.id = 123
        mock_row_mcc.customer_client.descriptive_name = "MCC Principal"
        mock_row_mcc.customer_client.level = 0
        mock_row_mcc.customer_client.manager = True
        mock_row_mcc.customer_client.status.name = "ENABLED"
        mock_row_mcc.customer_client.currency_code = "BRL"
        mock_row_mcc.customer_client.time_zone = "America/Sao_Paulo"

        mock_row_child = MagicMock()
        mock_row_child.customer_client.id = 456
        mock_row_child.customer_client.descriptive_name = "Conta Filha"
        mock_row_child.customer_client.level = 1
        mock_row_child.customer_client.manager = False
        mock_row_child.customer_client.status.name = "ENABLED"
        mock_row_child.customer_client.currency_code = "BRL"
        mock_row_child.customer_client.time_zone = "America/Sao_Paulo"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row_mcc, mock_row_child]
        mock_get_service.return_value = mock_service

        result = assert_success(get_account_hierarchy("123"))
        assert result["data"]["count"] == 2
        accounts = result["data"]["accounts"]

        assert accounts[0]["customer_id"] == "123"
        assert accounts[0]["name"] == "MCC Principal"
        assert accounts[0]["level"] == 0
        assert accounts[0]["is_manager"] is True
        assert accounts[0]["status"] == "ENABLED"
        assert accounts[0]["currency"] == "BRL"
        assert accounts[0]["timezone"] == "America/Sao_Paulo"

        assert accounts[1]["customer_id"] == "456"
        assert accounts[1]["name"] == "Conta Filha"
        assert accounts[1]["level"] == 1
        assert accounts[1]["is_manager"] is False

    @patch("mcp_google_ads.tools.accounts.get_service")
    @patch("mcp_google_ads.tools.accounts.resolve_customer_id", return_value="123")
    def test_empty_hierarchy(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.accounts import get_account_hierarchy

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(get_account_hierarchy("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["accounts"] == []

    @patch("mcp_google_ads.tools.accounts.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.accounts import get_account_hierarchy

        result = assert_error(get_account_hierarchy(""))
        assert "Failed to get account hierarchy" in result["error"]

    @patch("mcp_google_ads.tools.accounts.get_service")
    @patch("mcp_google_ads.tools.accounts.resolve_customer_id", return_value="123")
    def test_uses_default_customer_id_when_none(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.accounts import get_account_hierarchy

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        get_account_hierarchy(None)
        mock_resolve.assert_called_once_with(None)


class TestListCustomerClients:
    @patch("mcp_google_ads.tools.accounts.get_service")
    @patch("mcp_google_ads.tools.accounts.resolve_customer_id", return_value="123")
    def test_returns_clients(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.accounts import list_customer_clients

        mock_row1 = MagicMock()
        mock_row1.customer_client.id = 456
        mock_row1.customer_client.descriptive_name = "Cliente A"
        mock_row1.customer_client.status.name = "ENABLED"
        mock_row1.customer_client.currency_code = "BRL"

        mock_row2 = MagicMock()
        mock_row2.customer_client.id = 789
        mock_row2.customer_client.descriptive_name = "Cliente B"
        mock_row2.customer_client.status.name = "PAUSED"
        mock_row2.customer_client.currency_code = "USD"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row1, mock_row2]
        mock_get_service.return_value = mock_service

        result = assert_success(list_customer_clients("123"))
        assert result["data"]["count"] == 2
        clients = result["data"]["clients"]

        assert clients[0]["customer_id"] == "456"
        assert clients[0]["name"] == "Cliente A"
        assert clients[0]["status"] == "ENABLED"
        assert clients[0]["currency"] == "BRL"

        assert clients[1]["customer_id"] == "789"
        assert clients[1]["name"] == "Cliente B"
        assert clients[1]["status"] == "PAUSED"
        assert clients[1]["currency"] == "USD"

    @patch("mcp_google_ads.tools.accounts.get_service")
    @patch("mcp_google_ads.tools.accounts.resolve_customer_id", return_value="123")
    def test_empty_clients(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.accounts import list_customer_clients

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_customer_clients("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["clients"] == []

    @patch("mcp_google_ads.tools.accounts.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.accounts import list_customer_clients

        result = assert_error(list_customer_clients(""))
        assert "Failed to list customer clients" in result["error"]

    @patch("mcp_google_ads.tools.accounts.get_service")
    @patch("mcp_google_ads.tools.accounts.resolve_customer_id", return_value="123")
    def test_uses_default_customer_id_when_none(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.accounts import list_customer_clients

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        list_customer_clients(None)
        mock_resolve.assert_called_once_with(None)
