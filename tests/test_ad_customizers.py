"""Tests for ad_customizers.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListCustomizerAttributes:
    @patch("mcp_google_ads.tools.ad_customizers.get_service")
    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", return_value="123")
    def test_returns_attributes(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_customizers import list_customizer_attributes

        mock_row = MagicMock()
        mock_row.customizer_attribute.resource_name = "customers/123/customizerAttributes/1"
        mock_row.customizer_attribute.id = 1
        mock_row.customizer_attribute.name = "Price"
        mock_row.customizer_attribute.type_.name = "TEXT"
        mock_row.customizer_attribute.status.name = "ENABLED"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_customizer_attributes("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["customizer_attributes"][0]["name"] == "Price"
        assert result["data"]["customizer_attributes"][0]["type"] == "TEXT"

    @patch("mcp_google_ads.tools.ad_customizers.get_service")
    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", return_value="123")
    def test_returns_empty_list(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_customizers import list_customizer_attributes

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_customizer_attributes("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["customizer_attributes"] == []

    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ad_customizers import list_customizer_attributes

        result = assert_error(list_customizer_attributes(""))
        assert "Failed to list customizer attributes" in result["error"]

    def test_rejects_invalid_limit(self):
        from mcp_google_ads.tools.ad_customizers import list_customizer_attributes

        result = assert_error(list_customizer_attributes("123", limit=-1))
        assert "Failed to list customizer attributes" in result["error"]


class TestCreateCustomizerAttribute:
    @patch("mcp_google_ads.tools.ad_customizers.get_service")
    @patch("mcp_google_ads.tools.ad_customizers.get_client")
    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", return_value="123")
    def test_creates_text_attribute(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.ad_customizers import create_customizer_attribute

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/customizerAttributes/99")]
        mock_service = MagicMock()
        mock_service.mutate_customizer_attributes.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_customizer_attribute("123", "Price"))
        assert result["data"]["customizer_attribute_id"] == "99"
        assert result["data"]["name"] == "Price"
        assert result["data"]["type"] == "TEXT"
        mock_service.mutate_customizer_attributes.assert_called_once()

    @patch("mcp_google_ads.tools.ad_customizers.get_service")
    @patch("mcp_google_ads.tools.ad_customizers.get_client")
    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", return_value="123")
    def test_creates_price_attribute(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.ad_customizers import create_customizer_attribute

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/customizerAttributes/100")]
        mock_service = MagicMock()
        mock_service.mutate_customizer_attributes.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_customizer_attribute("123", "Preco", type="PRICE"))
        assert result["data"]["customizer_attribute_id"] == "100"
        assert result["data"]["type"] == "PRICE"

    def test_rejects_invalid_type(self):
        from mcp_google_ads.tools.ad_customizers import create_customizer_attribute

        result = assert_error(create_customizer_attribute("123", "Test", type="DROP TABLE;"))
        assert "Failed to create customizer attribute" in result["error"]

    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ad_customizers import create_customizer_attribute

        result = assert_error(create_customizer_attribute("123", "Test"))
        assert "Failed to create customizer attribute" in result["error"]


class TestRemoveCustomizerAttribute:
    @patch("mcp_google_ads.tools.ad_customizers.get_service")
    @patch("mcp_google_ads.tools.ad_customizers.get_client")
    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", return_value="123")
    def test_removes_attribute(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.ad_customizers import remove_customizer_attribute

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        result = assert_success(remove_customizer_attribute("123", "99"))
        assert result["data"]["action"] == "removed"
        assert result["data"]["customizer_attribute_id"] == "99"
        mock_service.mutate_customizer_attributes.assert_called_once()

    def test_rejects_invalid_id(self):
        from mcp_google_ads.tools.ad_customizers import remove_customizer_attribute

        result = assert_error(remove_customizer_attribute("123", "abc"))
        assert "Failed to remove customizer attribute" in result["error"]

    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ad_customizers import remove_customizer_attribute

        result = assert_error(remove_customizer_attribute("123", "99"))
        assert "Failed to remove customizer attribute" in result["error"]


class TestSetCampaignCustomizerValue:
    @patch("mcp_google_ads.tools.ad_customizers.get_service")
    @patch("mcp_google_ads.tools.ad_customizers.get_client")
    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", return_value="123")
    def test_sets_campaign_value(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.ad_customizers import set_campaign_customizer_value

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignCustomizers/555~99")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_customizers.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(set_campaign_customizer_value("123", "555", "99", "R$ 29,90"))
        assert result["data"]["campaign_id"] == "555"
        assert result["data"]["customizer_attribute_id"] == "99"
        assert result["data"]["value"] == "R$ 29,90"
        mock_service.mutate_campaign_customizers.assert_called_once()

    def test_rejects_invalid_campaign_id(self):
        from mcp_google_ads.tools.ad_customizers import set_campaign_customizer_value

        result = assert_error(set_campaign_customizer_value("123", "abc", "99", "test"))
        assert "Failed to set campaign customizer value" in result["error"]

    def test_rejects_invalid_attribute_id(self):
        from mcp_google_ads.tools.ad_customizers import set_campaign_customizer_value

        result = assert_error(set_campaign_customizer_value("123", "555", "abc", "test"))
        assert "Failed to set campaign customizer value" in result["error"]

    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ad_customizers import set_campaign_customizer_value

        result = assert_error(set_campaign_customizer_value("123", "555", "99", "test"))
        assert "Failed to set campaign customizer value" in result["error"]


class TestSetAdGroupCustomizerValue:
    @patch("mcp_google_ads.tools.ad_customizers.get_service")
    @patch("mcp_google_ads.tools.ad_customizers.get_client")
    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", return_value="123")
    def test_sets_ad_group_value(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.ad_customizers import set_ad_group_customizer_value

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/adGroupCustomizers/777~99")]
        mock_service = MagicMock()
        mock_service.mutate_ad_group_customizers.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(set_ad_group_customizer_value("123", "777", "99", "Frete Gratis"))
        assert result["data"]["ad_group_id"] == "777"
        assert result["data"]["customizer_attribute_id"] == "99"
        assert result["data"]["value"] == "Frete Gratis"
        mock_service.mutate_ad_group_customizers.assert_called_once()

    def test_rejects_invalid_ad_group_id(self):
        from mcp_google_ads.tools.ad_customizers import set_ad_group_customizer_value

        result = assert_error(set_ad_group_customizer_value("123", "abc", "99", "test"))
        assert "Failed to set ad group customizer value" in result["error"]

    def test_rejects_invalid_attribute_id(self):
        from mcp_google_ads.tools.ad_customizers import set_ad_group_customizer_value

        result = assert_error(set_ad_group_customizer_value("123", "777", "abc", "test"))
        assert "Failed to set ad group customizer value" in result["error"]

    @patch("mcp_google_ads.tools.ad_customizers.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ad_customizers import set_ad_group_customizer_value

        result = assert_error(set_ad_group_customizer_value("123", "777", "99", "test"))
        assert "Failed to set ad group customizer value" in result["error"]
