"""Tests for account_management.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListAccountLinks:
    @patch("mcp_google_ads.tools.account_management.get_service")
    @patch("mcp_google_ads.tools.account_management.resolve_customer_id", return_value="123")
    def test_returns_links(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.account_management import list_account_links

        mock_row = MagicMock()
        mock_row.account_link.account_link_id = 111
        mock_row.account_link.status.name = "ENABLED"
        mock_row.account_link.resource_name = "customers/123/accountLinks/111"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_account_links("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["account_links"][0]["account_link_id"] == "111"

    @patch("mcp_google_ads.tools.account_management.get_service")
    @patch("mcp_google_ads.tools.account_management.resolve_customer_id", return_value="123")
    def test_empty_results(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.account_management import list_account_links

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_account_links("123"))
        assert result["data"]["count"] == 0

    @patch("mcp_google_ads.tools.account_management.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.account_management import list_account_links

        result = assert_error(list_account_links(""))
        assert "Failed to list account links" in result["error"]


class TestGetBillingInfo:
    @patch("mcp_google_ads.tools.account_management.get_service")
    @patch("mcp_google_ads.tools.account_management.resolve_customer_id", return_value="123")
    def test_returns_billing(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.account_management import get_billing_info

        mock_row = MagicMock()
        mock_row.billing_setup.id = 222
        mock_row.billing_setup.status.name = "APPROVED"
        mock_row.billing_setup.payments_account = "accounts/333"
        mock_row.billing_setup.payments_account_info.payments_account_id = "333"
        mock_row.billing_setup.payments_account_info.payments_account_name = "Main"
        mock_row.billing_setup.payments_account_info.payments_profile_id = "444"
        mock_row.billing_setup.payments_account_info.payments_profile_name = "Profile"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_billing_info("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["billing_setups"][0]["status"] == "APPROVED"

    @patch("mcp_google_ads.tools.account_management.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.account_management import get_billing_info

        result = assert_error(get_billing_info(""))
        assert "Failed to get billing info" in result["error"]


class TestListAccountUsers:
    @patch("mcp_google_ads.tools.account_management.get_service")
    @patch("mcp_google_ads.tools.account_management.resolve_customer_id", return_value="123")
    def test_returns_users(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.account_management import list_account_users

        mock_row = MagicMock()
        mock_row.customer_user_access.user_id = 555
        mock_row.customer_user_access.email_address = "user@example.com"
        mock_row.customer_user_access.access_role.name = "ADMIN"
        mock_row.customer_user_access.access_creation_date_time = "2024-01-01"
        mock_row.customer_user_access.inviter_user_email_address = "admin@example.com"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_account_users("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["users"][0]["email"] == "user@example.com"
        assert result["data"]["users"][0]["access_role"] == "ADMIN"

    @patch("mcp_google_ads.tools.account_management.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.account_management import list_account_users

        result = assert_error(list_account_users(""))
        assert "Failed to list account users" in result["error"]
