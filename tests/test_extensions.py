"""Tests for extensions.py tools."""

from __future__ import annotations

import urllib.error
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


class TestCreateStructuredSnippetAssets:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_creates_snippet_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_structured_snippet_assets

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assets/501")]
        mock_service = MagicMock()
        mock_service.mutate_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_structured_snippet_assets("123", "Brands", ["Nike", "Adidas", "Puma"])
        )
        assert "resource_name" in result["data"]
        assert result["data"]["resource_name"] == "customers/123/assets/501"
        assert "Brands" in result["message"]

    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_creates_snippet_api_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_structured_snippet_assets

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_assets.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(
            create_structured_snippet_assets("123", "Brands", ["Nike"])
        )
        assert "Failed to create structured snippet" in result["error"]


class TestCreateCallAsset:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_creates_call_asset_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_call_asset

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assets/601")]
        mock_service = MagicMock()
        mock_service.mutate_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_call_asset("123", "+5511999999999", country_code="BR", call_tracking=True)
        )
        assert result["data"]["resource_name"] == "customers/123/assets/601"
        assert "+5511999999999" in result["message"]


class TestCreateImageAsset:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    @patch("urllib.request.urlopen")
    def test_creates_image_asset_success(self, mock_urlopen, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_image_asset

        mock_url_response = MagicMock()
        mock_url_response.read.return_value = b"\x89PNG\r\n\x1a\nfake_image_data"
        mock_urlopen.return_value = mock_url_response

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assets/701")]
        mock_service = MagicMock()
        mock_service.mutate_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_image_asset("123", "https://example.com/image.png", "Test Image")
        )
        assert result["data"]["resource_name"] == "customers/123/assets/701"
        assert result["data"]["asset_id"] == "701"
        assert "Test Image" in result["message"]

    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("urllib.request.urlopen")
    def test_handles_http_error(self, mock_urlopen, mock_get_service, mock_client, mock_resolve):
        from mcp_google_ads.tools.extensions import create_image_asset

        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://example.com/image.png",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

        result = assert_error(
            create_image_asset("123", "https://example.com/image.png", "Missing Image")
        )
        assert "HTTP error 404" in result["error"]

    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("urllib.request.urlopen")
    def test_handles_url_error(self, mock_urlopen, mock_get_service, mock_client, mock_resolve):
        from mcp_google_ads.tools.extensions import create_image_asset

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        result = assert_error(
            create_image_asset("123", "https://invalid-host.test/image.png", "Bad URL Image")
        )
        assert "network error" in result["error"]


class TestCreateVideoAsset:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_creates_video_asset_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_video_asset

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assets/801")]
        mock_service = MagicMock()
        mock_service.mutate_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_video_asset("123", "dQw4w9WgXcQ", "My Video Ad")
        )
        assert result["data"]["resource_name"] == "customers/123/assets/801"
        assert result["data"]["asset_id"] == "801"
        assert "My Video Ad" in result["message"]


class TestCreateLeadFormAsset:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_creates_lead_form_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_lead_form_asset

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assets/901")]
        mock_service = MagicMock()
        mock_service.mutate_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_lead_form_asset(
                customer_id="123",
                headline="Get a Free Quote",
                business_name="My Business",
                description="Fill out the form to get your free quote",
                fields=["FULL_NAME", "EMAIL", "PHONE_NUMBER"],
                privacy_policy_url="https://example.com/privacy",
                call_to_action="GET_QUOTE",
            )
        )
        assert result["data"]["resource_name"] == "customers/123/assets/901"
        assert result["data"]["asset_id"] == "901"
        assert "Get a Free Quote" in result["message"]
        assert "3 fields" in result["message"]

    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_lead_form_api_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_lead_form_asset

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_assets.side_effect = Exception("Permission denied")
        mock_get_service.return_value = mock_service

        result = assert_error(
            create_lead_form_asset(
                customer_id="123",
                headline="Quote",
                business_name="Biz",
                description="Desc",
                fields=["EMAIL"],
                privacy_policy_url="https://example.com/privacy",
            )
        )
        assert "Failed to create lead form asset" in result["error"]


class TestCreatePromotionAsset:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_creates_promotion_with_percent_off(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_promotion_asset

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assets/1001")]
        mock_service = MagicMock()
        mock_service.mutate_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_promotion_asset(
                customer_id="123",
                promotion_target="Summer Sale",
                final_url="https://example.com/sale",
                percent_off=20,
                occasion="BLACK_FRIDAY",
            )
        )
        assert result["data"]["resource_name"] == "customers/123/assets/1001"
        assert result["data"]["asset_id"] == "1001"
        assert "Summer Sale" in result["message"]

    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_creates_promotion_with_money_off(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import create_promotion_asset

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/assets/1002")]
        mock_service = MagicMock()
        mock_service.mutate_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_promotion_asset(
                customer_id="123",
                promotion_target="Winter Deal",
                final_url="https://example.com/winter",
                money_off_micros=50_000_000,
                currency_code="BRL",
            )
        )
        assert result["data"]["resource_name"] == "customers/123/assets/1002"


class TestLinkAssetToCampaign:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_links_asset_to_campaign_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import link_asset_to_campaign

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignAssets/555~777~SITELINK")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            link_asset_to_campaign("123", campaign_id="555", asset_id="777", field_type="SITELINK")
        )
        assert result["data"]["resource_name"] == "customers/123/campaignAssets/555~777~SITELINK"
        assert "777" in result["message"]
        assert "555" in result["message"]
        assert "SITELINK" in result["message"]


class TestLinkAssetToAdGroup:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_links_asset_to_ad_group_success(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import link_asset_to_ad_group

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/adGroupAssets/888~999~CALLOUT")]
        mock_service = MagicMock()
        mock_service.mutate_ad_group_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            link_asset_to_ad_group("123", ad_group_id="888", asset_id="999", field_type="CALLOUT")
        )
        assert result["data"]["resource_name"] == "customers/123/adGroupAssets/888~999~CALLOUT"
        assert "999" in result["message"]
        assert "888" in result["message"]
        assert "CALLOUT" in result["message"]


class TestUnlinkAsset:
    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_unlinks_from_campaign(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import unlink_asset

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignAssets/555~777~SITELINK")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            unlink_asset(
                customer_id="123",
                resource_name="customers/123/campaignAssets/555~777~SITELINK",
                resource_type="campaign",
            )
        )
        assert result["data"]["resource_name"] == "customers/123/campaignAssets/555~777~SITELINK"
        assert "campaign" in result["message"]

    @patch("mcp_google_ads.tools.extensions.get_service")
    @patch("mcp_google_ads.tools.extensions.get_client")
    @patch("mcp_google_ads.tools.extensions.resolve_customer_id", return_value="123")
    def test_unlinks_from_ad_group(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.extensions import unlink_asset

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/adGroupAssets/888~999~CALLOUT")]
        mock_service = MagicMock()
        mock_service.mutate_ad_group_assets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            unlink_asset(
                customer_id="123",
                resource_name="customers/123/adGroupAssets/888~999~CALLOUT",
                resource_type="ad_group",
            )
        )
        assert result["data"]["resource_name"] == "customers/123/adGroupAssets/888~999~CALLOUT"
        assert "ad_group" in result["message"]


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
        assert "missing required field" in result["error"]


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
