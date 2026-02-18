"""Tests for ads.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success

# --- Helpers ---

def _make_headline(text="Headline"):
    h = MagicMock()
    h.text = text
    h.pinned_field.name = "UNSPECIFIED"
    return h


def _make_description(text="Description"):
    d = MagicMock()
    d.text = text
    d.pinned_field.name = "UNSPECIFIED"
    return d


def _make_ad_row(
    ad_id=333,
    ad_name="Ad 1",
    type_name="RESPONSIVE_SEARCH_AD",
    status="ENABLED",
    ad_strength="GOOD",
    final_urls=None,
    final_mobile_urls=None,
    tracking_url_template="",
    headlines=None,
    descriptions=None,
    path1="",
    path2="",
    approval_status="APPROVED",
    ad_group_id=222,
    ad_group_name="Ad Group 1",
    campaign_id=111,
    campaign_name="Campaign 1",
):
    row = MagicMock()
    row.ad_group_ad.ad.id = ad_id
    row.ad_group_ad.ad.name = ad_name
    row.ad_group_ad.ad.type_.name = type_name
    row.ad_group_ad.status.name = status
    row.ad_group_ad.ad_strength.name = ad_strength
    row.ad_group_ad.ad.final_urls = final_urls or ["https://example.com"]
    row.ad_group_ad.ad.final_mobile_urls = final_mobile_urls or []
    row.ad_group_ad.ad.tracking_url_template = tracking_url_template

    row.ad_group_ad.ad.responsive_search_ad.headlines = headlines or []
    row.ad_group_ad.ad.responsive_search_ad.descriptions = descriptions or []
    row.ad_group_ad.ad.responsive_search_ad.path1 = path1
    row.ad_group_ad.ad.responsive_search_ad.path2 = path2
    row.ad_group_ad.policy_summary.approval_status.name = approval_status

    row.ad_group.id = ad_group_id
    row.ad_group.name = ad_group_name
    row.campaign.id = campaign_id
    row.campaign.name = campaign_name
    return row


def _mock_mutate_response(resource_name="customers/123/adGroupAds/222~333"):
    response = MagicMock()
    result = MagicMock()
    result.resource_name = resource_name
    response.results = [result]
    return response


class TestListAds:
    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_returns_ads(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        mock_row = _make_ad_row()
        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_ads("123"))
        assert result["data"]["count"] == 1

    @patch("mcp_google_ads.tools.ads.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ads import list_ads

        result = assert_error(list_ads(""))
        assert "Failed" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_filter_by_ad_group_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        mock_service = MagicMock()
        mock_service.search.return_value = [_make_ad_row()]
        mock_get_service.return_value = mock_service

        assert_success(list_ads("123", ad_group_id="222"))
        query_called = mock_service.search.call_args[1]["query"]
        assert "ad_group.id = 222" in query_called

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_filter_by_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        mock_service = MagicMock()
        mock_service.search.return_value = [_make_ad_row()]
        mock_get_service.return_value = mock_service

        assert_success(list_ads("123", campaign_id="111"))
        query_called = mock_service.search.call_args[1]["query"]
        assert "campaign.id = 111" in query_called

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_filter_by_status(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(list_ads("123", status_filter="PAUSED"))
        query_called = mock_service.search.call_args[1]["query"]
        assert "ad_group_ad.status = 'PAUSED'" in query_called

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_filter_combined(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(list_ads("123", ad_group_id="222", campaign_id="111", status_filter="ENABLED"))
        query_called = mock_service.search.call_args[1]["query"]
        assert "ad_group.id = 222" in query_called
        assert "campaign.id = 111" in query_called
        assert "ad_group_ad.status = 'ENABLED'" in query_called

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_invalid_ad_group_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        result = assert_error(list_ads("123", ad_group_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_invalid_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        result = assert_error(list_ads("123", campaign_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_invalid_status_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        result = assert_error(list_ads("123", status_filter="INVALID"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_empty_response(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_ads("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["ads"] == []

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_ad_with_headlines_and_descriptions(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        headlines = [_make_headline("H1"), _make_headline("H2")]
        descriptions = [_make_description("D1")]
        mock_row = _make_ad_row(headlines=headlines, descriptions=descriptions)
        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_ads("123"))
        ad = result["data"]["ads"][0]
        assert ad["headlines"] == ["H1", "H2"]
        assert ad["descriptions"] == ["D1"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_ad_fields_mapping(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import list_ads

        mock_row = _make_ad_row(
            ad_id=777,
            ad_name="Test Ad",
            type_name="RESPONSIVE_SEARCH_AD",
            status="PAUSED",
            ad_strength="EXCELLENT",
            final_urls=["https://test.com"],
            ad_group_id=888,
            ad_group_name="Group X",
            campaign_id=999,
            campaign_name="Campaign X",
        )
        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_ads("123"))
        ad = result["data"]["ads"][0]
        assert ad["ad_id"] == "777"
        assert ad["name"] == "Test Ad"
        assert ad["type"] == "RESPONSIVE_SEARCH_AD"
        assert ad["status"] == "PAUSED"
        assert ad["ad_strength"] == "EXCELLENT"
        assert ad["final_urls"] == ["https://test.com"]
        assert ad["ad_group_id"] == "888"
        assert ad["ad_group_name"] == "Group X"
        assert ad["campaign_id"] == "999"
        assert ad["campaign_name"] == "Campaign X"


class TestGetAd:
    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_returns_ad(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import get_ad

        headlines = [_make_headline("H1"), _make_headline("H2"), _make_headline("H3")]
        descriptions = [_make_description("D1"), _make_description("D2")]
        mock_row = _make_ad_row(
            headlines=headlines,
            descriptions=descriptions,
            path1="path1",
            path2="path2",
            final_mobile_urls=["https://m.example.com"],
            tracking_url_template="https://track.example.com",
        )
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter([mock_row]))
        mock_service.search.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(get_ad("123", "222", "333"))
        data = result["data"]
        assert data["ad_id"] == "333"
        assert data["status"] == "ENABLED"
        assert data["path1"] == "path1"
        assert data["path2"] == "path2"
        assert len(data["headlines"]) == 3
        assert data["headlines"][0]["text"] == "H1"
        assert data["headlines"][0]["pinned_field"] == "UNSPECIFIED"
        assert len(data["descriptions"]) == 2
        assert data["final_mobile_urls"] == ["https://m.example.com"]
        assert data["tracking_url_template"] == "https://track.example.com"
        assert data["approval_status"] == "APPROVED"

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_not_found(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import get_ad

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter([]))
        mock_service.search.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_error(get_ad("123", "222", "999"))
        assert "not found" in result["error"]

    def test_invalid_ad_group_id(self):
        from mcp_google_ads.tools.ads import get_ad

        result = assert_error(get_ad("123", "abc", "333"))
        assert "inválido" in result["error"]

    def test_invalid_ad_id(self):
        from mcp_google_ads.tools.ads import get_ad

        result = assert_error(get_ad("123", "222", "abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service", side_effect=Exception("API error"))
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_error_handling(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import get_ad

        result = assert_error(get_ad("123", "222", "333"))
        assert "Failed to get ad" in result["error"]


class TestCreateResponsiveSearchAd:
    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_create_success(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.PAUSED = 2
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response("customers/123/adGroupAds/222~444")
        mock_get_service.return_value = mock_service

        result = assert_success(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            final_url="https://example.com",
        ))
        assert result["data"]["status"] == "PAUSED"
        assert result["data"]["resource_name"] == "customers/123/adGroupAds/222~444"
        assert "PAUSED" in result["message"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_create_with_paths(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.PAUSED = 2
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            final_url="https://example.com",
            path1="products",
            path2="sale",
        ))
        assert result["data"]["status"] == "PAUSED"

    def test_too_few_headlines(self):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        result = assert_error(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2"],
            descriptions=["D1", "D2"],
            final_url="https://example.com",
        ))
        assert "Headlines must be between 3 and 15" in result["error"]

    def test_too_many_headlines(self):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        result = assert_error(create_responsive_search_ad(
            "123", "222",
            headlines=[f"H{i}" for i in range(16)],
            descriptions=["D1", "D2"],
            final_url="https://example.com",
        ))
        assert "Headlines must be between 3 and 15" in result["error"]

    def test_too_few_descriptions(self):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        result = assert_error(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1"],
            final_url="https://example.com",
        ))
        assert "Descriptions must be between 2 and 4" in result["error"]

    def test_too_many_descriptions(self):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        result = assert_error(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2", "D3", "D4", "D5"],
            final_url="https://example.com",
        ))
        assert "Descriptions must be between 2 and 4" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_create_api_error(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.PAUSED = 2
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            final_url="https://example.com",
        ))
        assert "Failed to create RSA" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_create_max_headlines_and_descriptions(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.PAUSED = 2
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(create_responsive_search_ad(
            "123", "222",
            headlines=[f"H{i}" for i in range(15)],
            descriptions=["D1", "D2", "D3", "D4"],
            final_url="https://example.com",
        ))
        assert result["data"]["status"] == "PAUSED"


    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_create_with_pinned_headlines(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.PAUSED = 2
        mock_client.enums.ServedAssetFieldTypeEnum.HEADLINE_1 = 2
        mock_client.enums.ServedAssetFieldTypeEnum.HEADLINE_2 = 3
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            final_url="https://example.com",
            pinned_headlines={0: "HEADLINE_1", 2: "HEADLINE_2"},
        ))
        assert result["data"]["pins"] == 2
        assert "2 pins" in result["message"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_create_with_pinned_descriptions(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.PAUSED = 2
        mock_client.enums.ServedAssetFieldTypeEnum.DESCRIPTION_1 = 5
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            final_url="https://example.com",
            pinned_descriptions={0: "DESCRIPTION_1"},
        ))
        assert result["data"]["pins"] == 1

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_create_with_all_pins(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.PAUSED = 2
        mock_client.enums.ServedAssetFieldTypeEnum.HEADLINE_1 = 2
        mock_client.enums.ServedAssetFieldTypeEnum.HEADLINE_3 = 4
        mock_client.enums.ServedAssetFieldTypeEnum.DESCRIPTION_1 = 5
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            final_url="https://example.com",
            pinned_headlines={0: "HEADLINE_1", 2: "HEADLINE_3"},
            pinned_descriptions={0: "DESCRIPTION_1"},
        ))
        assert result["data"]["pins"] == 3

    def test_create_with_invalid_headline_pin(self):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        result = assert_error(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            final_url="https://example.com",
            pinned_headlines={0: "DESCRIPTION_1"},
        ))
        assert "Invalid pin position" in result["error"]

    def test_create_with_invalid_description_pin(self):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        result = assert_error(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            final_url="https://example.com",
            pinned_descriptions={0: "HEADLINE_1"},
        ))
        assert "Invalid pin position" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_create_without_pins_zero_count(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import create_responsive_search_ad

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.PAUSED = 2
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(create_responsive_search_ad(
            "123", "222",
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            final_url="https://example.com",
        ))
        assert result["data"]["pins"] == 0
        assert "pins" not in result["message"]


class TestUpdateAd:
    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_update_final_url(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import update_ad

        mock_client = MagicMock()
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(update_ad("123", "222", "333", final_url="https://new.com"))
        assert "updated" in result["message"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_update_paths(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import update_ad

        mock_client = MagicMock()
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(update_ad("123", "222", "333", path1="new-path1", path2="new-path2"))
        assert result["data"]["resource_name"] == "customers/123/adGroupAds/222~333"

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_update_all_fields(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import update_ad

        mock_client = MagicMock()
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(update_ad(
            "123", "222", "333",
            final_url="https://new.com",
            path1="p1",
            path2="p2",
        ))
        assert "updated" in result["message"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_update_no_fields(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import update_ad

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = assert_error(update_ad("123", "222", "333"))
        assert "No fields to update" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_update_api_error(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import update_ad

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(update_ad("123", "222", "333", final_url="https://fail.com"))
        assert "Failed to update ad" in result["error"]


class TestSetAdStatus:
    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_set_status_enabled(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import set_ad_status

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.ENABLED = 1
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(set_ad_status("123", "222", "333", "ENABLED"))
        assert result["data"]["new_status"] == "ENABLED"
        assert "ENABLED" in result["message"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_set_status_paused(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import set_ad_status

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.PAUSED = 2
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(set_ad_status("123", "222", "333", "PAUSED"))
        assert result["data"]["new_status"] == "PAUSED"

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_set_status_removed(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import set_ad_status

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.REMOVED = 3
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(set_ad_status("123", "222", "333", "REMOVED"))
        assert result["data"]["new_status"] == "REMOVED"

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_invalid_status_with_spaces(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import set_ad_status

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = assert_error(set_ad_status("123", "222", "333", "NOT VALID"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_invalid_status_special_chars(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import set_ad_status

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = assert_error(set_ad_status("123", "222", "333", "DROP TABLE;"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_set_status_api_error(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ads import set_ad_status

        mock_client = MagicMock()
        mock_client.enums.AdGroupAdStatusEnum.ENABLED = 1
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(set_ad_status("123", "222", "333", "ENABLED"))
        assert "Failed to set ad status" in result["error"]


class TestGetAdStrength:
    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_returns_ad_strength(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import get_ad_strength

        mock_row = MagicMock()
        mock_row.ad_group_ad.ad.id = 333
        mock_row.ad_group_ad.ad_strength.name = "GOOD"
        mock_row.ad_group_ad.status.name = "ENABLED"
        mock_row.ad_group.id = 222
        mock_row.ad_group.name = "Ad Group 1"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Campaign 1"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_ad_strength("123"))
        assert result["data"]["count"] == 1
        ad = result["data"]["ads"][0]
        assert ad["ad_id"] == "333"
        assert ad["ad_strength"] == "GOOD"
        assert ad["status"] == "ENABLED"
        assert ad["ad_group_id"] == "222"
        assert ad["campaign_id"] == "111"

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_filter_by_ad_group_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import get_ad_strength

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(get_ad_strength("123", ad_group_id="222"))
        query_called = mock_service.search.call_args[1]["query"]
        assert "ad_group.id = 222" in query_called

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_filter_by_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import get_ad_strength

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(get_ad_strength("123", campaign_id="111"))
        query_called = mock_service.search.call_args[1]["query"]
        assert "campaign.id = 111" in query_called

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_empty_results(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import get_ad_strength

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(get_ad_strength("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["ads"] == []

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_multiple_ads(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import get_ad_strength

        rows = []
        for i, strength in enumerate(["POOR", "AVERAGE", "GOOD", "EXCELLENT"]):
            row = MagicMock()
            row.ad_group_ad.ad.id = 100 + i
            row.ad_group_ad.ad_strength.name = strength
            row.ad_group_ad.status.name = "ENABLED"
            row.ad_group.id = 222
            row.ad_group.name = "Group"
            row.campaign.id = 111
            row.campaign.name = "Campaign"
            rows.append(row)

        mock_service = MagicMock()
        mock_service.search.return_value = rows
        mock_get_service.return_value = mock_service

        result = assert_success(get_ad_strength("123"))
        assert result["data"]["count"] == 4
        strengths = [ad["ad_strength"] for ad in result["data"]["ads"]]
        assert "POOR" in strengths
        assert "EXCELLENT" in strengths

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_invalid_ad_group_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import get_ad_strength

        result = assert_error(get_ad_strength("123", ad_group_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_invalid_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import get_ad_strength

        result = assert_error(get_ad_strength("123", campaign_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service", side_effect=Exception("API error"))
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_error_handling(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ads import get_ad_strength

        result = assert_error(get_ad_strength("123"))
        assert "Failed to get ad strength" in result["error"]


class TestCreateResponsiveDisplayAd:
    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_creates_rda(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.ads import create_responsive_display_ad

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/adGroupAds/111~222")]
        mock_service.mutate_ad_group_ads.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_responsive_display_ad(
                "123", "111", "https://example.com",
                headlines=["Headline 1", "Headline 2"],
                long_headline="This is a long headline for display",
                descriptions=["Description 1"],
                business_name="Test Biz",
                marketing_images=["customers/123/assets/img1"],
            )
        )
        assert result["data"]["status"] == "PAUSED"
        assert "Responsive Display Ad created" in result["message"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_with_square_and_logo(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.ads import create_responsive_display_ad

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/adGroupAds/111~333")]
        mock_service.mutate_ad_group_ads.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            create_responsive_display_ad(
                "123", "111", "https://example.com",
                headlines=["H1"],
                long_headline="Long headline test",
                descriptions=["D1"],
                business_name="Biz",
                marketing_images=["customers/123/assets/img1"],
                square_marketing_images=["customers/123/assets/sq1"],
                logo_images=["customers/123/assets/logo1"],
            )
        )
        assert result["data"]["status"] == "PAUSED"

    def test_too_many_headlines(self):
        from mcp_google_ads.tools.ads import create_responsive_display_ad

        result = assert_error(
            create_responsive_display_ad(
                "123", "111", "https://example.com",
                headlines=["H1", "H2", "H3", "H4", "H5", "H6"],
                long_headline="Long",
                descriptions=["D1"],
                business_name="Biz",
                marketing_images=["customers/123/assets/img1"],
            )
        )
        assert "Headlines must be between 1 and 5" in result["error"]

    def test_no_marketing_images(self):
        from mcp_google_ads.tools.ads import create_responsive_display_ad

        result = assert_error(
            create_responsive_display_ad(
                "123", "111", "https://example.com",
                headlines=["H1"],
                long_headline="Long",
                descriptions=["D1"],
                business_name="Biz",
                marketing_images=[],
            )
        )
        assert "At least one marketing image" in result["error"]

    @patch("mcp_google_ads.tools.ads.get_service")
    @patch("mcp_google_ads.tools.ads.get_client")
    @patch("mcp_google_ads.tools.ads.resolve_customer_id", return_value="123")
    def test_api_exception(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.ads import create_responsive_display_ad

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_ad_group_ads.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(
            create_responsive_display_ad(
                "123", "111", "https://example.com",
                headlines=["H1"],
                long_headline="Long",
                descriptions=["D1"],
                business_name="Biz",
                marketing_images=["customers/123/assets/img1"],
            )
        )
        assert "Failed to create RDA" in result["error"]
