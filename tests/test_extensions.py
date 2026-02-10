"""Tests for extensions.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListAssets:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_returns_assets(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.extensions import list_assets

        mock_row = MagicMock()
        mock_row.asset.id = 111
        mock_row.asset.name = "Test Asset"
        mock_row.asset.type_.name = "SITELINK"
        mock_row.asset.final_urls = ["https://example.com"]
        mock_row.asset.sitelink_asset.link_text = "Click Here"
        mock_row.asset.sitelink_asset.description1 = "Desc 1"
        mock_row.asset.sitelink_asset.description2 = "Desc 2"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_assets("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["assets"][0]["type"] == "SITELINK"

    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_with_type_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.extensions import list_assets

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(list_assets("123", asset_type="CALLOUT"))
        call_query = mock_service.search.call_args[1]["query"]
        assert "CALLOUT" in call_query

    def test_rejects_invalid_asset_type(self):
        from mcp_google_ads.tools.extensions import list_assets

        result = assert_error(list_assets("123", asset_type="'; DROP TABLE"))
        assert "Failed to list assets" in result["error"]


class TestCreateSitelinkAssets:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_creates_sitelinks(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_sitelink_assets

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assets/1")]
        mock_service = MagicMock()
        mock_service.mutate_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        sitelinks = [{"link_text": "Contact", "final_url": "https://example.com/contact"}]
        result = assert_success(create_sitelink_assets("123", sitelinks))
        assert result["data"]["created"] == 1

    def test_rejects_missing_required_fields(self):
        from mcp_google_ads.tools.extensions import create_sitelink_assets

        sitelinks = [{"link_text": "Contact"}]  # missing final_url
        result = assert_error(create_sitelink_assets("123", sitelinks))
        assert "link_text" in result["error"] or "final_url" in result["error"]

    def test_rejects_batch_too_large(self):
        from mcp_google_ads.tools.extensions import create_sitelink_assets

        sitelinks = [{"link_text": "x", "final_url": "https://x.com"}] * 5001
        result = assert_error(create_sitelink_assets("123", sitelinks))
        assert "5000" in result["error"]


class TestCreateCalloutAssets:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_creates_callouts(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_callout_assets

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assets/1")]
        mock_service = MagicMock()
        mock_service.mutate_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_callout_assets("123", ["Free Shipping"]))
        assert result["data"]["created"] == 1

    def test_rejects_batch_too_large(self):
        from mcp_google_ads.tools.extensions import create_callout_assets

        result = assert_error(create_callout_assets("123", ["x"] * 5001))
        assert "5000" in result["error"]


class TestCreatePriceAsset:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_creates_price_asset(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_price_asset

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assets/1")]
        mock_service = MagicMock()
        mock_service.mutate_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        items = [{"header": "Basic", "description": "Plan", "final_url": "https://x.com", "price_micros": 29_900_000}]
        result = assert_success(create_price_asset("123", "SERVICES", items))
        assert "resource_name" in result["data"]

    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_rejects_missing_price_fields(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_price_asset

        client = MagicMock()
        mock_client.return_value = client

        items = [{"header": "Basic"}]  # missing required fields
        result = assert_error(create_price_asset("123", "SERVICES", items))
        assert "must have" in result["error"]


class TestRemoveAsset:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_removes_asset(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import remove_asset

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assets/111")]
        mock_service = MagicMock()
        mock_service.mutate_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_asset("123", "111"))
        assert "Asset 111 removed" in result["message"]
