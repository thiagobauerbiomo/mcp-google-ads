"""Tests for ai_generation.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestGenerateAdText:
    @patch("mcp_google_ads.tools.ai_generation.get_client")
    @patch("mcp_google_ads.tools.ai_generation.resolve_customer_id", return_value="123")
    def test_generates_text(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.ai_generation import generate_ad_text

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        client.get_service.return_value = mock_service

        headline = MagicMock()
        headline.text = "Buy Now"
        headline.asset_type = "HEADLINE"
        description = MagicMock()
        description.text = "Best deals on shoes"
        description.asset_type = "DESCRIPTION"

        mock_response = MagicMock()
        mock_response.text_asset_suggestions = [headline, description]
        mock_service.suggest_assets.return_value = mock_response

        result = assert_success(generate_ad_text("123", "https://example.com"))
        assert result["data"]["headlines"] == ["Buy Now"]
        assert result["data"]["descriptions"] == ["Best deals on shoes"]

    @patch("mcp_google_ads.tools.ai_generation.get_client")
    @patch("mcp_google_ads.tools.ai_generation.resolve_customer_id", return_value="123")
    def test_fallback_when_service_unavailable(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.ai_generation import generate_ad_text

        client = MagicMock()
        mock_client.return_value = client
        client.get_service.side_effect = Exception("Service not found")

        result = assert_success(generate_ad_text("123", "https://example.com"))
        assert result["data"]["headlines"] == []
        assert result["data"]["descriptions"] == []
        assert "not available" in result["data"]["note"]
        assert "unavailable" in result["message"].lower()

    @patch("mcp_google_ads.tools.ai_generation.get_client")
    @patch("mcp_google_ads.tools.ai_generation.resolve_customer_id", return_value="123")
    def test_with_keywords(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.ai_generation import generate_ad_text

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        client.get_service.return_value = mock_service

        mock_request = MagicMock()
        client.get_type.return_value = mock_request

        mock_response = MagicMock()
        mock_response.text_asset_suggestions = []
        mock_service.suggest_assets.return_value = mock_response

        keywords = ["shoes", "sneakers", "boots"]
        result = assert_success(generate_ad_text("123", "https://example.com", keywords=keywords))
        assert result["data"]["headlines"] == []
        assert result["data"]["descriptions"] == []

    @patch("mcp_google_ads.tools.ai_generation.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ai_generation import generate_ad_text

        result = assert_error(generate_ad_text("", "https://example.com"))
        assert "Failed to generate ad text" in result["error"]


class TestGenerateAdImages:
    @patch("mcp_google_ads.tools.ai_generation.get_client")
    @patch("mcp_google_ads.tools.ai_generation.resolve_customer_id", return_value="123")
    def test_generates_images(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.ai_generation import generate_ad_images

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        client.get_service.return_value = mock_service

        img = MagicMock()
        img.url = "https://example.com/image.png"
        img.width = 1200
        img.height = 628

        mock_response = MagicMock()
        mock_response.image_asset_suggestions = [img]
        mock_service.suggest_image_assets.return_value = mock_response

        result = assert_success(generate_ad_images("123", "https://example.com"))
        assert result["data"]["count"] == 1
        assert result["data"]["images"][0]["url"] == "https://example.com/image.png"
        assert result["data"]["images"][0]["width"] == 1200
        assert result["data"]["images"][0]["height"] == 628

    @patch("mcp_google_ads.tools.ai_generation.get_client")
    @patch("mcp_google_ads.tools.ai_generation.resolve_customer_id", return_value="123")
    def test_fallback_when_service_unavailable(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.ai_generation import generate_ad_images

        client = MagicMock()
        mock_client.return_value = client
        client.get_service.side_effect = Exception("Service not found")

        result = assert_success(generate_ad_images("123", "https://example.com"))
        assert result["data"]["images"] == []
        assert result["data"]["count"] == 0
        assert "not available" in result["data"]["note"]
        assert "unavailable" in result["message"].lower()

    @patch("mcp_google_ads.tools.ai_generation.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ai_generation import generate_ad_images

        result = assert_error(generate_ad_images("", "https://example.com"))
        assert "Failed to generate ad images" in result["error"]


class TestGenerateAudienceDefinition:
    @patch("mcp_google_ads.tools.ai_generation.get_client")
    @patch("mcp_google_ads.tools.ai_generation.resolve_customer_id", return_value="123")
    def test_generates_audience(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.ai_generation import generate_audience_definition

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        client.get_service.return_value = mock_service

        segment1 = MagicMock()
        segment1.name = "Women 25-45"
        segment1.type_.name = "AFFINITY"
        segment2 = MagicMock()
        segment2.name = "Tarot Enthusiasts"
        segment2.type_.name = "IN_MARKET"

        mock_response = MagicMock()
        mock_response.audience_definition.audience_segments = [segment1, segment2]
        mock_service.generate_audience_definition.return_value = mock_response

        result = assert_success(generate_audience_definition("123", "women 25-45 interested in tarot"))
        assert result["data"]["count"] == 2
        assert result["data"]["segments"][0]["segment_name"] == "Women 25-45"
        assert result["data"]["segments"][0]["segment_type"] == "AFFINITY"
        assert result["data"]["segments"][1]["segment_name"] == "Tarot Enthusiasts"
        assert result["data"]["segments"][1]["segment_type"] == "IN_MARKET"
        assert "Generated 2" in result["message"]

    @patch("mcp_google_ads.tools.ai_generation.get_client")
    @patch("mcp_google_ads.tools.ai_generation.resolve_customer_id", return_value="123")
    def test_fallback_when_service_unavailable(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.ai_generation import generate_audience_definition

        client = MagicMock()
        mock_client.return_value = client
        client.get_service.side_effect = Exception("Service not found")

        result = assert_success(generate_audience_definition("123", "women 25-45"))
        assert result["data"]["segments"] == []
        assert result["data"]["count"] == 0
        assert "not available" in result["data"]["note"]
        assert "unavailable" in result["message"].lower()

    @patch("mcp_google_ads.tools.ai_generation.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ai_generation import generate_audience_definition

        result = assert_error(generate_audience_definition("", "women 25-45"))
        assert "Failed to generate audience definition" in result["error"]
