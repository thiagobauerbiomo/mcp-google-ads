"""Tests for incentives.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestFetchIncentive:
    @patch("mcp_google_ads.tools.incentives.get_client")
    def test_returns_incentives(self, mock_get_client):
        from mcp_google_ads.tools.incentives import fetch_incentive

        client = MagicMock()
        mock_get_client.return_value = client

        mock_incentive = MagicMock()
        mock_incentive.incentive_id = "PROMO_123"
        mock_incentive.name = "Ganhe R$600"
        mock_incentive.description = "Gaste R$600, ganhe R$600 de crédito"

        mock_response = MagicMock()
        mock_response.incentives = [mock_incentive]
        client.get_service.return_value.fetch_incentive.return_value = mock_response

        result = assert_success(fetch_incentive("pt", "BR"))
        assert result["data"]["count"] == 1
        assert result["data"]["incentives"][0]["incentive_id"] == "PROMO_123"

    @patch("mcp_google_ads.tools.incentives.get_client")
    def test_error_handling(self, mock_get_client):
        from mcp_google_ads.tools.incentives import fetch_incentive

        mock_get_client.side_effect = Exception("API error")

        result = assert_error(fetch_incentive())
        assert "Failed to fetch incentives" in result["error"]


class TestApplyIncentive:
    @patch("mcp_google_ads.tools.incentives.get_client")
    @patch("mcp_google_ads.tools.incentives.resolve_customer_id", return_value="123")
    def test_applies_incentive(self, mock_resolve, mock_get_client):
        from mcp_google_ads.tools.incentives import apply_incentive

        client = MagicMock()
        mock_get_client.return_value = client

        result = assert_success(apply_incentive("123", "PROMO_123"))
        assert result["data"]["incentive_id"] == "PROMO_123"
        assert "applied" in result["message"].lower()

    @patch("mcp_google_ads.tools.incentives.get_client")
    @patch("mcp_google_ads.tools.incentives.resolve_customer_id", return_value="123")
    def test_error_handling(self, mock_resolve, mock_get_client):
        from mcp_google_ads.tools.incentives import apply_incentive

        client = MagicMock()
        mock_get_client.return_value = client
        client.get_service.return_value.apply_incentive.side_effect = Exception("Not eligible")

        result = assert_error(apply_incentive("123", "PROMO_123"))
        assert "Failed to apply incentive" in result["error"]
