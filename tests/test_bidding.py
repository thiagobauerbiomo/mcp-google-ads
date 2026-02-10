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

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_target_roas_type(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import get_bidding_strategy

        mock_row = MagicMock()
        bs = mock_row.bidding_strategy
        bs.id = 222
        bs.name = "ROAS Strategy"
        bs.type_.name = "TARGET_ROAS"
        bs.status.name = "ENABLED"
        bs.campaign_count = 1
        bs.effective_currency_code = "BRL"
        bs.target_roas.target_roas = 3.5

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_bidding_strategy("123", "222"))
        assert result["data"]["target_roas"] == 3.5
        assert result["data"]["type"] == "TARGET_ROAS"

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_maximize_clicks_type(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import get_bidding_strategy

        mock_row = MagicMock()
        bs = mock_row.bidding_strategy
        bs.id = 333
        bs.name = "Max Clicks"
        bs.type_.name = "MAXIMIZE_CLICKS"
        bs.status.name = "ENABLED"
        bs.campaign_count = 2
        bs.effective_currency_code = "USD"
        bs.maximize_clicks.cpc_bid_ceiling_micros = 2_000_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_bidding_strategy("123", "333"))
        assert result["data"]["cpc_bid_ceiling_micros"] == 2_000_000
        assert result["data"]["type"] == "MAXIMIZE_CLICKS"

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_target_impression_share_type(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import get_bidding_strategy

        mock_row = MagicMock()
        bs = mock_row.bidding_strategy
        bs.id = 444
        bs.name = "Impression Share"
        bs.type_.name = "TARGET_IMPRESSION_SHARE"
        bs.status.name = "ENABLED"
        bs.campaign_count = 1
        bs.effective_currency_code = "BRL"
        bs.target_impression_share.location.name = "ANYWHERE_ON_PAGE"
        bs.target_impression_share.location_fraction_micros = 700_000
        bs.target_impression_share.cpc_bid_ceiling_micros = 3_000_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_bidding_strategy("123", "444"))
        assert result["data"]["location"] == "ANYWHERE_ON_PAGE"
        assert result["data"]["location_fraction_micros"] == 700_000
        assert result["data"]["cpc_bid_ceiling_micros"] == 3_000_000
        assert result["data"]["type"] == "TARGET_IMPRESSION_SHARE"

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_not_found(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.bidding import get_bidding_strategy

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_error(get_bidding_strategy("123", "999"))
        assert "not found" in result["error"]

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

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_maximize_conversions_with_target_cpa(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/501")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_bidding_strategy("123", "Max Conv CPA", "MAXIMIZE_CONVERSIONS", target_cpa_micros=5_000_000)
        )
        assert result["data"]["strategy_id"] == "501"
        operation = client.get_type.return_value
        assert operation.create.maximize_conversions.target_cpa_micros == 5_000_000

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_maximize_conversions_without_cpa(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/502")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_bidding_strategy("123", "Max Conv", "MAXIMIZE_CONVERSIONS"))
        assert result["data"]["strategy_id"] == "502"
        mock_service.mutate_bidding_strategies.assert_called_once()

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_target_cpa(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/503")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_bidding_strategy("123", "CPA Strategy", "TARGET_CPA", target_cpa_micros=3_000_000)
        )
        assert result["data"]["strategy_id"] == "503"
        operation = client.get_type.return_value
        assert operation.create.target_cpa.target_cpa_micros == 3_000_000

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_target_roas(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/504")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_bidding_strategy("123", "ROAS Strategy", "TARGET_ROAS", target_roas=3.0)
        )
        assert result["data"]["strategy_id"] == "504"
        operation = client.get_type.return_value
        assert operation.create.target_roas.target_roas == 3.0

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_target_impression_share(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/505")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_bidding_strategy("123", "Impression Share", "TARGET_IMPRESSION_SHARE")
        )
        assert result["data"]["strategy_id"] == "505"
        operation = client.get_type.return_value
        assert operation.create.target_impression_share.location == (
            client.enums.TargetImpressionShareLocationEnum.ANYWHERE_ON_PAGE
        )

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_target_impression_share_with_ceiling(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/506")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_bidding_strategy(
                "123", "Impression + Ceiling", "TARGET_IMPRESSION_SHARE", cpc_bid_ceiling_micros=5_000_000
            )
        )
        assert result["data"]["strategy_id"] == "506"
        operation = client.get_type.return_value
        assert operation.create.target_impression_share.cpc_bid_ceiling_micros == 5_000_000

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_maximize_clicks_with_ceiling(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import create_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/507")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_bidding_strategy("123", "Clicks + Ceiling", "MAXIMIZE_CLICKS", cpc_bid_ceiling_micros=2_000_000)
        )
        assert result["data"]["strategy_id"] == "507"
        operation = client.get_type.return_value
        assert operation.create.maximize_clicks.cpc_bid_ceiling_micros == 2_000_000


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

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_updates_name(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import update_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/111")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_bidding_strategy("123", "111", name="New Name"))
        assert "updated" in result["message"]
        operation = client.get_type.return_value
        assert operation.update.name == "New Name"

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_updates_target_cpa(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import update_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/111")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_bidding_strategy("123", "111", target_cpa_micros=3_000_000))
        assert "updated" in result["message"]
        operation = client.get_type.return_value
        assert operation.update.target_cpa.target_cpa_micros == 3_000_000

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_updates_target_roas(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import update_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/111")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_bidding_strategy("123", "111", target_roas=3.0))
        assert "updated" in result["message"]
        operation = client.get_type.return_value
        assert operation.update.target_roas.target_roas == 3.0

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_updates_cpc_bid_ceiling(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import update_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/111")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_bidding_strategy("123", "111", cpc_bid_ceiling_micros=2_000_000))
        assert "updated" in result["message"]
        operation = client.get_type.return_value
        assert operation.update.maximize_clicks.cpc_bid_ceiling_micros == 2_000_000

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_updates_multiple_fields(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import update_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/biddingStrategies/111")]
        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            update_bidding_strategy("123", "111", name="Updated", target_roas=4.0, cpc_bid_ceiling_micros=1_000_000)
        )
        assert "updated" in result["message"]
        operation = client.get_type.return_value
        assert operation.update.name == "Updated"
        assert operation.update.target_roas.target_roas == 4.0
        assert operation.update.maximize_clicks.cpc_bid_ceiling_micros == 1_000_000
        client.copy_from.assert_called_once()

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_error_handling(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import update_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_bidding_strategies.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(update_bidding_strategy("123", "111", name="Fail"))
        assert "Failed to update bidding strategy" in result["error"]


class TestSetCampaignBiddingStrategy:
    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_assigns_strategy_to_campaign(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import set_campaign_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaigns/555")]
        mock_service = MagicMock()
        mock_service.mutate_campaigns.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(set_campaign_bidding_strategy("123", "555", "999"))
        assert result["data"]["resource_name"] == "customers/123/campaigns/555"
        assert "555" in result["message"]
        assert "999" in result["message"]

        operation = client.get_type.return_value
        assert operation.update.resource_name == "customers/123/campaigns/555"
        assert operation.update.bidding_strategy == "customers/123/biddingStrategies/999"
        client.copy_from.assert_called_once()
        mock_service.mutate_campaigns.assert_called_once()

    @patch("mcp_google_ads.tools.bidding.get_service")
    @patch("mcp_google_ads.tools.bidding.get_client")
    @patch("mcp_google_ads.tools.bidding.resolve_customer_id", return_value="123")
    def test_error_handling(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.bidding import set_campaign_bidding_strategy

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_campaigns.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(set_campaign_bidding_strategy("123", "555", "999"))
        assert "Failed to set campaign bidding strategy" in result["error"]
