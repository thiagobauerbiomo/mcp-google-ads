"""Tests for recommendations.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListRecommendations:
    @patch("mcp_google_ads.tools.recommendations.get_service")
    @patch("mcp_google_ads.tools.recommendations.resolve_customer_id", return_value="123")
    def test_returns_recommendations(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.recommendations import list_recommendations

        mock_row = MagicMock()
        mock_row.recommendation.resource_name = "customers/123/recommendations/1"
        mock_row.recommendation.type_.name = "KEYWORD"
        mock_row.recommendation.dismissed = False
        mock_row.recommendation.campaign = "customers/123/campaigns/111"
        mock_row.recommendation.impact.base_metrics.impressions = 100
        mock_row.recommendation.impact.base_metrics.clicks = 10
        mock_row.recommendation.impact.base_metrics.cost_micros = 1_000_000
        mock_row.recommendation.impact.potential_metrics.impressions = 200
        mock_row.recommendation.impact.potential_metrics.clicks = 20
        mock_row.recommendation.impact.potential_metrics.cost_micros = 2_000_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_recommendations("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["recommendations"][0]["type"] == "KEYWORD"

    @patch("mcp_google_ads.tools.recommendations.get_service")
    @patch("mcp_google_ads.tools.recommendations.resolve_customer_id", return_value="123")
    def test_with_type_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.recommendations import list_recommendations

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(list_recommendations("123", recommendation_type="KEYWORD"))
        call_query = mock_service.search.call_args[1]["query"]
        assert "KEYWORD" in call_query

    def test_rejects_invalid_recommendation_type(self):
        from mcp_google_ads.tools.recommendations import list_recommendations

        result = assert_error(list_recommendations("123", recommendation_type="'; DROP"))
        assert "Failed to list recommendations" in result["error"]


class TestApplyRecommendation:
    @patch("mcp_google_ads.tools.recommendations.get_service")
    @patch("mcp_google_ads.tools.recommendations.get_client")
    @patch("mcp_google_ads.tools.recommendations.resolve_customer_id", return_value="123")
    def test_applies_recommendation(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.recommendations import apply_recommendation

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/recommendations/1")]
        mock_service = MagicMock()
        mock_service.apply_recommendation.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(apply_recommendation("123", "customers/123/recommendations/1"))
        assert result["data"]["applied"] == 1


class TestDismissRecommendation:
    @patch("mcp_google_ads.tools.recommendations.get_service")
    @patch("mcp_google_ads.tools.recommendations.get_client")
    @patch("mcp_google_ads.tools.recommendations.resolve_customer_id", return_value="123")
    def test_dismisses_recommendation(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.recommendations import dismiss_recommendation

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/recommendations/1")]
        mock_service = MagicMock()
        mock_service.dismiss_recommendation.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(dismiss_recommendation("123", "customers/123/recommendations/1"))
        assert result["data"]["dismissed"] == 1


class TestGetOptimizationScore:
    @patch("mcp_google_ads.tools.recommendations.get_service")
    @patch("mcp_google_ads.tools.recommendations.resolve_customer_id", return_value="123")
    def test_returns_score(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.recommendations import get_optimization_score

        mock_row = MagicMock()
        mock_row.customer.optimization_score = 0.75
        mock_row.customer.optimization_score_weight = 0.5

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_optimization_score("123"))
        assert result["data"]["optimization_score"] == 75.0

    @patch("mcp_google_ads.tools.recommendations.get_service")
    @patch("mcp_google_ads.tools.recommendations.resolve_customer_id", return_value="123")
    def test_no_score(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.recommendations import get_optimization_score

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_error(get_optimization_score("123"))
        assert "Could not retrieve" in result["error"]
