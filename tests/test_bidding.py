"""Tests for bidding.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListBiddingStrategies:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_returns_strategies(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import list_bidding_strategies

        mock_row = MagicMock()
        mock_row.bidding_strategy.id = 111
        mock_row.bidding_strategy.name = "Max Clicks"
        mock_row.bidding_strategy.type_.name = "MAXIMIZE_CLICKS"
        mock_row.bidding_strategy.status.name = "ENABLED"
        mock_row.bidding_strategy.campaign_count = 3
        mock_row.bidding_strategy.effective_currency_code = "BRL"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_bidding_strategies("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["strategies"][0]["name"] == "Max Clicks"

    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.bidding import list_bidding_strategies

        result = assert_error(list_bidding_strategies(""))
        assert "Failed to list bidding strategies" in result["error"]


class TestGetBiddingStrategy:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_returns_strategy(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import get_bidding_strategy

        mock_row = MagicMock()
        bs = mock_row.bidding_strategy
        bs.id = 111
        bs.name = "Target CPA"
        bs.type_.name = "TARGET_CPA"
        bs.status.name = "ENABLED"
        bs.campaign_count = 2
        bs.effective_currency_code = "BRL"
        bs.target_cpa.target_cpa_micros = 5_000_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_bidding_strategy("123", "111"))
        assert result["data"]["name"] == "Target CPA"
        assert result["data"]["target_cpa_micros"] == 5_000_000

    def test_rejects_invalid_strategy_id(self):
        from mcp_google_ads.tools.bidding import get_bidding_strategy

        result = assert_error(get_bidding_strategy("123", "abc"))
        assert "Failed to get bidding strategy" in result["error"]


class TestCreateBiddingStrategy:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_creates_strategy(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/444")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_bidding_strategy("123", "Max Clicks", "MAXIMIZE_CLICKS"))
        assert result["data"]["strategy_id"] == "444"

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_unsupported_type(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(create_bidding_strategy("123", "Bad", "INVALID_TYPE"))
        assert "Unsupported strategy type" in result["error"]


class TestUpdateBiddingStrategy:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_no_fields_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import update_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        result = assert_error(update_bidding_strategy("123", "111"))
        assert "No fields to update" in result["error"]
