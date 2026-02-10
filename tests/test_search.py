"""Tests for search.py (execute_gaql) tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestExecuteGaql:
    @patch("mcp_google_ads.tools.search.get_service")
    @patch("mcp_google_ads.tools.search.resolve_customer_id", return_value="123")
    def test_valid_select_query(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.search import execute_gaql

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(execute_gaql("123", "SELECT campaign.id FROM campaign"))
        assert result["data"]["count"] == 0
        assert result["data"]["rows"] == []

    @patch("mcp_google_ads.tools.search.get_service")
    @patch("mcp_google_ads.tools.search.resolve_customer_id", return_value="123")
    def test_returns_rows(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.search import execute_gaql

        mock_row = MagicMock()
        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        with patch("mcp_google_ads.tools.search.proto_to_dict", return_value={"campaign": {"id": "111"}}):
            result = assert_success(execute_gaql("123", "SELECT campaign.id FROM campaign"))
            assert result["data"]["count"] == 1

    def test_rejects_non_select_query(self):
        from mcp_google_ads.tools.search import execute_gaql

        result = assert_error(execute_gaql("123", "UPDATE campaign SET name = 'test'"))
        assert "Only SELECT" in result["error"]

    def test_rejects_delete_keyword(self):
        from mcp_google_ads.tools.search import execute_gaql

        result = assert_error(execute_gaql("123", "SELECT * FROM campaign DELETE"))
        assert "DELETE" in result["error"]

    def test_rejects_mutate_keyword(self):
        from mcp_google_ads.tools.search import execute_gaql

        result = assert_error(execute_gaql("123", "SELECT * FROM campaign MUTATE"))
        assert "MUTATE" in result["error"]

    def test_rejects_too_long_query(self):
        from mcp_google_ads.tools.search import execute_gaql

        long_query = "SELECT campaign.id FROM campaign WHERE " + "x" * 10001
        result = assert_error(execute_gaql("123", long_query))
        assert "too long" in result["error"]

    @patch("mcp_google_ads.tools.search.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.search import execute_gaql

        result = assert_error(execute_gaql("", "SELECT campaign.id FROM campaign"))
        assert "GAQL query failed" in result["error"]
