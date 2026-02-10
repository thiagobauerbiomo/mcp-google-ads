"""Tests for labels.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListLabels:
    @patch("mcp_google_ads.tools.labels.get_service")
    @patch("mcp_google_ads.tools.labels.resolve_customer_id", return_value="123")
    def test_returns_labels(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.labels import list_labels

        mock_row = MagicMock()
        mock_row.label.id = 555
        mock_row.label.name = "Test Label"
        mock_row.label.description = "A test label"
        mock_row.label.text_label.background_color = "#FF0000"
        mock_row.label.status.name = "ENABLED"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_labels("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["labels"][0]["name"] == "Test Label"

    @patch("mcp_google_ads.tools.labels.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.labels import list_labels

        result = assert_error(list_labels(""))
        assert "Failed" in result["error"]


class TestCreateLabel:
    @patch("mcp_google_ads.tools.labels.get_service")
    @patch("mcp_google_ads.tools.labels.get_client")
    @patch("mcp_google_ads.tools.labels.resolve_customer_id", return_value="123")
    def test_creates_label(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.labels import create_label

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/labels/555")]
        mock_service.mutate_labels.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_label("123", "New Label"))
        assert result["data"]["label_id"] == "555"


class TestApplyLabelToCampaign:
    @patch("mcp_google_ads.tools.labels.get_service")
    @patch("mcp_google_ads.tools.labels.get_client")
    @patch("mcp_google_ads.tools.labels.resolve_customer_id", return_value="123")
    def test_applies_label(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.labels import apply_label_to_campaign

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignLabels/111~555")]
        mock_service.mutate_campaign_labels.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(apply_label_to_campaign("123", "111", "555"))
        assert "applied" in result["message"]


class TestRemoveLabelFromResource:
    @patch("mcp_google_ads.tools.labels.get_service")
    @patch("mcp_google_ads.tools.labels.get_client")
    @patch("mcp_google_ads.tools.labels.resolve_customer_id", return_value="123")
    def test_invalid_resource_type(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.labels import remove_label_from_resource

        result = assert_error(remove_label_from_resource("123", "invalid_type", "some/resource"))
        assert "Invalid resource_type" in result["error"]
