"""Tests for keywords.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListKeywords:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_returns_keywords(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.keywords import list_keywords

        mock_row = MagicMock()
        mock_row.ad_group_criterion.criterion_id = 444
        mock_row.ad_group_criterion.keyword.text = "test keyword"
        mock_row.ad_group_criterion.keyword.match_type.name = "BROAD"
        mock_row.ad_group_criterion.status.name = "ENABLED"
        mock_row.ad_group_criterion.cpc_bid_micros = 2_000_000
        mock_row.ad_group_criterion.quality_info.quality_score = 7
        mock_row.ad_group.id = 222
        mock_row.campaign.id = 111

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_keywords("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["keywords"][0]["keyword"] == "test keyword"
        assert result["data"]["keywords"][0]["quality_score"] == 7

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_filter_by_ad_group_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.keywords import list_keywords

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_keywords("123", ad_group_id="222"))
        assert result["data"]["count"] == 0
        query_used = mock_service.search.call_args[1]["query"]
        assert "ad_group.id = 222" in query_used

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_filter_by_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.keywords import list_keywords

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_keywords("123", campaign_id="333"))
        assert result["data"]["count"] == 0
        query_used = mock_service.search.call_args[1]["query"]
        assert "campaign.id = 333" in query_used

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_filter_by_status(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.keywords import list_keywords

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(list_keywords("123", status_filter="ENABLED"))
        query_used = mock_service.search.call_args[1]["query"]
        assert "ad_group_criterion.status = 'ENABLED'" in query_used

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_invalid_ad_group_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.keywords import list_keywords

        result = assert_error(list_keywords("123", ad_group_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_invalid_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.keywords import list_keywords

        result = assert_error(list_keywords("123", campaign_id="abc"))
        assert "inválido" in result["error"]


class TestAddKeywords:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_adds_keywords(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import add_keywords

        mock_service = MagicMock()
        mock_response = MagicMock()
        r1 = MagicMock()
        r1.resource_name = "customers/123/adGroupCriteria/222~444"
        mock_response.results = [r1]
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        kws = [{"text": "test keyword", "match_type": "BROAD"}]
        result = assert_success(add_keywords("123", "222", kws))
        assert result["data"]["added"] == 1

    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.keywords import add_keywords

        result = assert_error(add_keywords("", "222", []))
        assert "Failed" in result["error"]


class TestRemoveKeywords:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_removes_keywords(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import remove_keywords

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock()]
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_keywords("123", "222", ["444"]))
        assert result["data"]["removed"] == 1


class TestUpdateKeyword:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_update_with_bid(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import update_keyword

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/adGroupCriteria/222~444")]
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_keyword("123", "222", "444", cpc_bid=1.50))
        assert result["data"]["resource_name"] == "customers/123/adGroupCriteria/222~444"
        assert "updated" in result["message"].lower()

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_update_with_status(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import update_keyword

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/adGroupCriteria/222~444")]
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_keyword("123", "222", "444", status="PAUSED"))
        assert result["data"]["resource_name"] == "customers/123/adGroupCriteria/222~444"

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_update_with_final_url(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import update_keyword

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/adGroupCriteria/222~444")]
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_keyword("123", "222", "444", final_url="https://example.com"))
        assert result["data"]["resource_name"] == "customers/123/adGroupCriteria/222~444"

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_update_no_fields_returns_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import update_keyword

        result = assert_error(update_keyword("123", "222", "444"))
        assert "No fields" in result["error"]

    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", side_effect=Exception("fail"))
    def test_update_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.keywords import update_keyword

        result = assert_error(update_keyword("", "222", "444", cpc_bid=1.0))
        assert "Failed" in result["error"]


class TestAddNegativeKeywordsToCampaign:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_adds_negatives_to_campaign(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_campaign

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(), MagicMock()]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        kws = [
            {"text": "free stuff", "match_type": "BROAD"},
            {"text": "cheap stuff", "match_type": "EXACT"},
        ]
        result = assert_success(add_negative_keywords_to_campaign("123", "111", kws))
        assert result["data"]["added"] == 2
        assert "negative" in result["message"].lower()

    def test_batch_too_large_returns_error(self):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_campaign

        kws = [{"text": f"keyword_{i}"} for i in range(5001)]
        result = assert_error(add_negative_keywords_to_campaign("123", "111", kws))
        assert "Maximum" in result["error"] or "5000" in result["error"]

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_deduplicates_keywords(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_campaign

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock()]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        kws = [
            {"text": "free stuff", "match_type": "BROAD"},
            {"text": "free stuff", "match_type": "BROAD"},
        ]
        result = assert_success(add_negative_keywords_to_campaign("123", "111", kws))
        assert result["data"]["added"] == 1

    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", side_effect=Exception("api error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_campaign

        result = assert_error(add_negative_keywords_to_campaign("", "111", [{"text": "kw"}]))
        assert "Failed" in result["error"]


class TestAddNegativeKeywordsToSharedSet:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_adds_negatives_to_shared_set(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_shared_set

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.mutate_operation_responses = [MagicMock(), MagicMock()]
        mock_service.mutate.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            add_negative_keywords_to_shared_set("123", "999", ["free", "cheap"], match_type="EXACT")
        )
        assert result["data"]["added"] == 2
        assert "shared set" in result["message"].lower()

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_deduplicates_keywords(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_shared_set

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.mutate_operation_responses = [MagicMock()]
        mock_service.mutate.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            add_negative_keywords_to_shared_set("123", "999", ["free", "free"])
        )
        assert result["data"]["added"] == 1

    def test_batch_too_large_returns_error(self):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_shared_set

        kws = [f"keyword_{i}" for i in range(5001)]
        result = assert_error(add_negative_keywords_to_shared_set("123", "999", kws))
        assert "Maximum" in result["error"] or "5000" in result["error"]

    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", side_effect=Exception("api error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_shared_set

        result = assert_error(add_negative_keywords_to_shared_set("", "999", ["kw"]))
        assert "Failed" in result["error"]


class TestGenerateKeywordIdeas:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_generates_ideas_with_seed_keywords(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import generate_keyword_ideas

        mock_idea = MagicMock()
        mock_idea.text = "buy shoes online"
        mock_idea.keyword_idea_metrics.avg_monthly_searches = 10000
        mock_idea.keyword_idea_metrics.competition.name = "HIGH"
        mock_idea.keyword_idea_metrics.competition_index = 85
        mock_idea.keyword_idea_metrics.low_top_of_page_bid_micros = 500_000
        mock_idea.keyword_idea_metrics.high_top_of_page_bid_micros = 2_000_000

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter([mock_idea]))
        mock_service.generate_keyword_ideas.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(generate_keyword_ideas("123", seed_keywords=["shoes"]))
        assert result["data"]["count"] == 1
        assert result["data"]["ideas"][0]["keyword"] == "buy shoes online"
        assert result["data"]["ideas"][0]["avg_monthly_searches"] == 10000
        assert result["data"]["ideas"][0]["competition"] == "HIGH"

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_generates_ideas_with_page_url(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import generate_keyword_ideas

        mock_idea = MagicMock()
        mock_idea.text = "running shoes"
        mock_idea.keyword_idea_metrics.avg_monthly_searches = 5000
        mock_idea.keyword_idea_metrics.competition.name = "MEDIUM"
        mock_idea.keyword_idea_metrics.competition_index = 50
        mock_idea.keyword_idea_metrics.low_top_of_page_bid_micros = 300_000
        mock_idea.keyword_idea_metrics.high_top_of_page_bid_micros = 1_500_000

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter([mock_idea]))
        mock_service.generate_keyword_ideas.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(generate_keyword_ideas("123", page_url="https://example.com/shoes"))
        assert result["data"]["count"] == 1
        assert result["data"]["ideas"][0]["keyword"] == "running shoes"

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_no_seed_or_url_returns_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import generate_keyword_ideas

        result = assert_error(generate_keyword_ideas("123"))
        assert "seed_keywords" in result["error"] or "page_url" in result["error"]

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_respects_limit(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import generate_keyword_ideas

        ideas_list = []
        for i in range(5):
            mock_idea = MagicMock()
            mock_idea.text = f"keyword_{i}"
            mock_idea.keyword_idea_metrics.avg_monthly_searches = 100 * i
            mock_idea.keyword_idea_metrics.competition.name = "LOW"
            mock_idea.keyword_idea_metrics.competition_index = 10
            mock_idea.keyword_idea_metrics.low_top_of_page_bid_micros = 100_000
            mock_idea.keyword_idea_metrics.high_top_of_page_bid_micros = 500_000
            ideas_list.append(mock_idea)

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter(ideas_list))
        mock_service.generate_keyword_ideas.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(generate_keyword_ideas("123", seed_keywords=["test"], limit=3))
        assert result["data"]["count"] == 3

    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", side_effect=Exception("api error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.keywords import generate_keyword_ideas

        result = assert_error(generate_keyword_ideas("", seed_keywords=["test"]))
        assert "Failed" in result["error"]


class TestGetKeywordForecast:
    def _mock_campaign_metrics(self, clicks=150.0, impressions=5000.0, cost_micros=50_000_000, click_through_rate=0.03, avg_cpc=333_333, conversions=0.0, conversion_rate=0.0, average_cpa_micros=0):
        m = MagicMock()
        m.clicks = clicks
        m.impressions = impressions
        m.cost_micros = cost_micros
        m.click_through_rate = click_through_rate
        m.average_cpc_micros = avg_cpc
        m.conversions = conversions
        m.conversion_rate = conversion_rate
        m.average_cpa_micros = average_cpa_micros
        return m

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_returns_forecast_with_cpa(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import get_keyword_forecast

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.campaign_forecast_metrics = self._mock_campaign_metrics()

        mock_service.generate_keyword_forecast_metrics.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(get_keyword_forecast("123", ["shoes", "sneakers"]))
        total = result["data"]["campaign_total"]
        assert total["clicks"] == 150.0
        assert total["impressions"] == 5000.0
        assert total["cost_brl"] == 50.0
        assert total["estimated_conversions_custom"] == 4.5  # 150 * 0.03
        assert total["estimated_cpa_custom_brl"] == 11.11  # 50.0 / 4.5
        assert result["data"]["parameters"]["match_type"] == "EXACT"

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_returns_forecast_with_budget(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import get_keyword_forecast

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.campaign_forecast_metrics = self._mock_campaign_metrics(clicks=200.0, cost_micros=100_000_000)

        mock_service.generate_keyword_forecast_metrics.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            get_keyword_forecast("123", ["shoes"], daily_budget_micros=10_000_000)
        )
        assert result["data"]["campaign_total"]["cost_brl"] == 100.0
        assert result["data"]["parameters"]["daily_budget_brl"] == 10.0

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_no_forecast_metrics(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import get_keyword_forecast

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.campaign_forecast_metrics = None

        mock_service.generate_keyword_forecast_metrics.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(get_keyword_forecast("123", ["shoes"]))
        assert "campaign_total" not in result["data"]

    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", side_effect=Exception("api error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.keywords import get_keyword_forecast

        result = assert_error(get_keyword_forecast("", ["shoes"]))
        assert "Failed" in result["error"]

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_with_geo_and_language(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import get_keyword_forecast

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.campaign_forecast_metrics = self._mock_campaign_metrics()

        mock_service.generate_keyword_forecast_metrics.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            get_keyword_forecast("123", ["site"], geo_target_ids=["2076"], language_id="1014")
        )
        assert result["data"]["parameters"]["geo_target_ids"] == ["2076"]
        assert result["data"]["parameters"]["language_id"] == "1014"

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_with_max_cpc(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import get_keyword_forecast

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.campaign_forecast_metrics = self._mock_campaign_metrics()

        mock_service.generate_keyword_forecast_metrics.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            get_keyword_forecast("123", ["site"], max_cpc_bid_micros=4_000_000)
        )
        assert result["data"]["parameters"]["max_cpc_brl"] == 4.0

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_custom_conversion_rate(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import get_keyword_forecast

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.campaign_forecast_metrics = self._mock_campaign_metrics(clicks=100.0, cost_micros=40_000_000)

        mock_service.generate_keyword_forecast_metrics.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(get_keyword_forecast("123", ["site"], conversion_rate=0.05))
        total = result["data"]["campaign_total"]
        assert total["estimated_conversions_custom"] == 5.0  # 100 * 0.05
        assert total["estimated_cpa_custom_brl"] == 8.0  # 40.0 / 5.0
        assert total["custom_conversion_rate_used"] == 0.05


class TestListNegativeKeywords:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_returns_negative_keywords(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.keywords import list_negative_keywords

        mock_row = MagicMock()
        mock_row.campaign_criterion.criterion_id = 555
        mock_row.campaign_criterion.keyword.text = "free stuff"
        mock_row.campaign_criterion.keyword.match_type.name = "BROAD"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Test Campaign"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_negative_keywords("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["negative_keywords"][0]["keyword"] == "free stuff"
        assert result["data"]["negative_keywords"][0]["campaign_name"] == "Test Campaign"

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_filter_by_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.keywords import list_negative_keywords

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_negative_keywords("123", campaign_id="111"))
        assert result["data"]["count"] == 0
        query_used = mock_service.search.call_args[1]["query"]
        assert "campaign.id = 111" in query_used

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_invalid_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.keywords import list_negative_keywords

        result = assert_error(list_negative_keywords("123", campaign_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.keywords import list_negative_keywords

        result = assert_error(list_negative_keywords(""))
        assert "Failed" in result["error"]


class TestAddNegativeKeywordsToAdGroup:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_adds_negatives(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_ad_group

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(), MagicMock()]
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            add_negative_keywords_to_ad_group(
                "123", "111",
                [{"text": "free tarot", "match_type": "PHRASE"}, {"text": "curso", "match_type": "BROAD"}],
            )
        )
        assert result["data"]["added"] == 2

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_deduplicates(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_ad_group

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock()]
        mock_service.mutate_ad_group_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        assert_success(
            add_negative_keywords_to_ad_group(
                "123", "111",
                [{"text": "free", "match_type": "BROAD"}, {"text": "free", "match_type": "BROAD"}],
            )
        )
        # Should send only 1 operation (deduped)
        ops = mock_service.mutate_ad_group_criteria.call_args[1]["operations"]
        assert len(ops) == 1

    def test_invalid_ad_group_id(self):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_ad_group

        result = assert_error(
            add_negative_keywords_to_ad_group("123", "abc", [{"text": "test"}])
        )
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_missing_text_field(self, mock_resolve):
        from mcp_google_ads.tools.keywords import add_negative_keywords_to_ad_group

        result = assert_error(
            add_negative_keywords_to_ad_group("123", "111", [{"match_type": "BROAD"}])
        )
        assert "missing required field" in result["error"]


class TestAddPmaxNegativeKeywords:
    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_adds_pmax_negatives(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import add_pmax_negative_keywords

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(), MagicMock()]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(
            add_pmax_negative_keywords(
                "123", "555",
                [{"text": "free", "match_type": "BROAD"}, {"text": "curso tarot", "match_type": "PHRASE"}],
            )
        )
        assert result["data"]["added"] == 2
        assert "PMax campaign" in result["message"]

    @patch("mcp_google_ads.tools.keywords.get_service")
    @patch("mcp_google_ads.tools.keywords.get_client")
    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", return_value="123")
    def test_deduplicates(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.keywords import add_pmax_negative_keywords

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock()]
        mock_service.mutate_campaign_criteria.return_value = mock_response
        mock_get_service.return_value = mock_service

        add_pmax_negative_keywords(
            "123", "555",
            [{"text": "free", "match_type": "BROAD"}, {"text": "free", "match_type": "BROAD"}],
        )
        ops = mock_service.mutate_campaign_criteria.call_args[1]["operations"]
        assert len(ops) == 1

    @patch("mcp_google_ads.tools.keywords.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.keywords import add_pmax_negative_keywords

        result = assert_error(
            add_pmax_negative_keywords("", "555", [{"text": "test"}])
        )
        assert "Failed to add PMax negative keywords" in result["error"]
