"""Tests for reporting.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mcp_google_ads.tools.reporting import pmax_search_term_insights
from tests.conftest import assert_error, assert_success

# --- Helpers internos: _build_where e _run_report ---


class TestBuildWhere:
    """Testa a funcao helper _build_where diretamente."""

    def test_com_date_range_padrao_sem_conditions(self):
        from mcp_google_ads.tools.reporting import _build_where

        result = _build_where([], None, None, None, default_range="LAST_30_DAYS")
        assert "DURING LAST_30_DAYS" in result

    def test_com_date_range_customizado(self):
        from mcp_google_ads.tools.reporting import _build_where

        result = _build_where([], "LAST_7_DAYS", None, None, default_range="LAST_30_DAYS")
        assert "DURING LAST_7_DAYS" in result

    def test_com_start_date_e_end_date(self):
        from mcp_google_ads.tools.reporting import _build_where

        result = _build_where([], None, "2024-01-01", "2024-01-31", default_range="LAST_30_DAYS")
        assert "segments.date BETWEEN '2024-01-01' AND '2024-01-31'" in result
        assert "WHERE" in result

    def test_com_conditions_e_date_range(self):
        from mcp_google_ads.tools.reporting import _build_where

        result = _build_where(
            ["metrics.impressions > 0"], "LAST_7_DAYS", None, None, default_range="LAST_30_DAYS"
        )
        assert "WHERE metrics.impressions > 0" in result
        assert "DURING LAST_7_DAYS" in result

    def test_com_conditions_e_start_end_date(self):
        from mcp_google_ads.tools.reporting import _build_where

        result = _build_where(
            ["metrics.impressions > 0"], None, "2024-06-01", "2024-06-30", default_range="LAST_30_DAYS"
        )
        assert "WHERE" in result
        assert "metrics.impressions > 0" in result
        assert "segments.date BETWEEN" in result

    def test_sem_conditions_com_start_end_date(self):
        from mcp_google_ads.tools.reporting import _build_where

        result = _build_where([], None, "2024-01-01", "2024-01-31", default_range="LAST_30_DAYS")
        assert "WHERE segments.date BETWEEN" in result

    def test_multiplas_conditions(self):
        from mcp_google_ads.tools.reporting import _build_where

        result = _build_where(
            ["metrics.impressions > 0", "campaign.id = 123"],
            None, None, None,
            default_range="LAST_30_DAYS",
        )
        assert "WHERE metrics.impressions > 0 AND campaign.id = 123" in result
        assert "DURING LAST_30_DAYS" in result


class TestRunReport:
    """Testa a funcao helper _run_report diretamente."""

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_executa_query_e_retorna_sucesso(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import _run_report

        mock_row = MagicMock()
        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(
            _run_report(
                customer_id="123",
                query_template="SELECT campaign.id FROM campaign {where} LIMIT {limit}",
                field_extractor=lambda row: {"id": "1"},
                limit=10,
                report_name="test_report",
            )
        )
        assert result["data"]["count"] == 1
        assert result["data"]["test_report"][0]["id"] == "1"

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_sem_resultados(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import _run_report

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(
            _run_report(
                customer_id="123",
                query_template="SELECT campaign.id FROM campaign {where} LIMIT {limit}",
                field_extractor=lambda row: {"id": "1"},
                limit=10,
            )
        )
        assert result["data"]["count"] == 0
        assert result["data"]["report"] == []

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_com_conditions_e_start_end_date(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import _run_report

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        _run_report(
            customer_id="123",
            query_template="SELECT campaign.id FROM campaign {where} LIMIT {limit}",
            field_extractor=lambda row: {},
            conditions=["metrics.impressions > 0"],
            start_date="2024-01-01",
            end_date="2024-01-31",
            limit=50,
        )
        query_usado = mock_service.search.call_args[1]["query"]
        assert "segments.date BETWEEN" in query_usado
        assert "metrics.impressions > 0" in query_usado

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_default_date_range_none_sem_conditions(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import _run_report

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        _run_report(
            customer_id="123",
            query_template="SELECT campaign.id FROM campaign {where} LIMIT {limit}",
            field_extractor=lambda row: {},
            default_date_range=None,
            limit=10,
        )
        query_usado = mock_service.search.call_args[1]["query"]
        assert "DURING" not in query_usado
        assert "WHERE" not in query_usado

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_default_date_range_none_com_conditions(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import _run_report

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        _run_report(
            customer_id="123",
            query_template="SELECT campaign.id FROM campaign {where} LIMIT {limit}",
            field_extractor=lambda row: {},
            conditions=["ad_group_criterion.type = 'KEYWORD'"],
            default_date_range=None,
            limit=10,
        )
        query_usado = mock_service.search.call_args[1]["query"]
        assert "WHERE ad_group_criterion.type = 'KEYWORD'" in query_usado
        assert "DURING" not in query_usado


# --- Reports existentes ---


class TestCampaignPerformanceReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_returns_report(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import campaign_performance_report

        mock_row = MagicMock()
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Test"
        mock_row.campaign.status.name = "ENABLED"
        mock_row.metrics.impressions = 1000
        mock_row.metrics.clicks = 50
        mock_row.metrics.cost_micros = 25_000_000
        mock_row.metrics.conversions = 5.0
        mock_row.metrics.conversions_value = 500.0
        mock_row.metrics.ctr = 0.05
        mock_row.metrics.average_cpc = 500_000
        mock_row.metrics.average_cpm = 25_000_000
        mock_row.metrics.cost_per_conversion = 5_000_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(campaign_performance_report("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["report"][0]["impressions"] == 1000
        assert result["data"]["report"][0]["clicks"] == 50
        assert result["data"]["report"][0]["ctr"] == 5.0

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_com_campaign_id_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import campaign_performance_report

        mock_row = MagicMock()
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Test"
        mock_row.campaign.status.name = "ENABLED"
        mock_row.metrics.impressions = 1000
        mock_row.metrics.clicks = 50
        mock_row.metrics.cost_micros = 25_000_000
        mock_row.metrics.conversions = 5.0
        mock_row.metrics.conversions_value = 500.0
        mock_row.metrics.ctr = 0.05
        mock_row.metrics.average_cpc = 500_000
        mock_row.metrics.average_cpm = 25_000_000
        mock_row.metrics.cost_per_conversion = 5_000_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        assert_success(campaign_performance_report("123", campaign_id="111"))
        query_usado = mock_service.search.call_args[1]["query"]
        assert "campaign.id = 111" in query_usado

    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.reporting import campaign_performance_report

        result = assert_error(campaign_performance_report(""))
        assert "Failed" in result["error"]

    def test_campaign_id_invalido(self):
        from mcp_google_ads.tools.reporting import campaign_performance_report

        result = assert_error(campaign_performance_report("123", campaign_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_com_start_date_e_end_date(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import campaign_performance_report

        mock_row = MagicMock()
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Test"
        mock_row.campaign.status.name = "ENABLED"
        mock_row.metrics.impressions = 1000
        mock_row.metrics.clicks = 50
        mock_row.metrics.cost_micros = 25_000_000
        mock_row.metrics.conversions = 5.0
        mock_row.metrics.conversions_value = 500.0
        mock_row.metrics.ctr = 0.05
        mock_row.metrics.average_cpc = 500_000
        mock_row.metrics.average_cpm = 25_000_000
        mock_row.metrics.cost_per_conversion = 5_000_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        assert_success(
            campaign_performance_report("123", start_date="2024-01-01", end_date="2024-01-31")
        )
        query_usado = mock_service.search.call_args[1]["query"]
        assert "segments.date BETWEEN" in query_usado

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_api_exception(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import campaign_performance_report

        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("API error 500")
        mock_get_service.return_value = mock_service

        result = assert_error(campaign_performance_report("123"))
        assert "API error 500" in result["error"]


class TestDevicePerformanceReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_returns_device_report(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import device_performance_report

        mock_row = MagicMock()
        mock_row.segments.device.name = "MOBILE"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Test"
        mock_row.metrics.impressions = 500
        mock_row.metrics.clicks = 25
        mock_row.metrics.cost_micros = 10_000_000
        mock_row.metrics.conversions = 2.0
        mock_row.metrics.ctr = 0.05
        mock_row.metrics.average_cpc = 400_000
        mock_row.metrics.cost_per_conversion = 5_000_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(device_performance_report("123"))
        assert result["data"]["report"][0]["device"] == "MOBILE"


class TestQualityScoreReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_returns_quality_scores(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import quality_score_report

        mock_row = MagicMock()
        mock_row.ad_group_criterion.keyword.text = "test kw"
        mock_row.ad_group_criterion.keyword.match_type.name = "BROAD"
        mock_row.ad_group_criterion.quality_info.quality_score = 8
        mock_row.ad_group_criterion.quality_info.creative_quality_score.name = "ABOVE_AVERAGE"
        mock_row.ad_group_criterion.quality_info.post_click_quality_score.name = "AVERAGE"
        mock_row.ad_group_criterion.quality_info.search_predicted_ctr.name = "ABOVE_AVERAGE"
        mock_row.ad_group.id = 222
        mock_row.ad_group.name = "AG 1"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "C 1"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(quality_score_report("123"))
        assert result["data"]["report"][0]["quality_score"] == 8
        assert result["data"]["report"][0]["ad_relevance"] == "ABOVE_AVERAGE"

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_quality_score_nao_usa_date_clause(self, mock_resolve, mock_get_service):
        """quality_score_report usa default_date_range=None, sem clausula de data."""
        from mcp_google_ads.tools.reporting import quality_score_report

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(quality_score_report("123"))
        query_usado = mock_service.search.call_args[1]["query"]
        assert "DURING" not in query_usado


# --- Novos reports ---


class TestAdGroupPerformanceReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_retorna_report_basico(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import ad_group_performance_report

        mock_row = MagicMock()
        mock_row.ad_group.id = 222
        mock_row.ad_group.name = "Ad Group 1"
        mock_row.ad_group.status.name = "ENABLED"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Campaign 1"
        mock_row.metrics.impressions = 800
        mock_row.metrics.clicks = 40
        mock_row.metrics.cost_micros = 20_000_000
        mock_row.metrics.conversions = 3.0
        mock_row.metrics.ctr = 0.05
        mock_row.metrics.average_cpc = 500_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(ad_group_performance_report("123"))
        assert result["data"]["count"] == 1
        row = result["data"]["report"][0]
        assert row["ad_group_id"] == "222"
        assert row["ad_group_name"] == "Ad Group 1"
        assert row["status"] == "ENABLED"
        assert row["impressions"] == 800
        assert row["clicks"] == 40
        assert row["cost"] == 20.0
        assert row["ctr"] == 5.0

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_com_campaign_id_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import ad_group_performance_report

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(ad_group_performance_report("123", campaign_id="111"))
        query_usado = mock_service.search.call_args[1]["query"]
        assert "campaign.id = 111" in query_usado

    def test_campaign_id_invalido(self):
        from mcp_google_ads.tools.reporting import ad_group_performance_report

        result = assert_error(ad_group_performance_report("123", campaign_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_api_exception(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import ad_group_performance_report

        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("API timeout")
        mock_get_service.return_value = mock_service

        result = assert_error(ad_group_performance_report("123"))
        assert "Failed to get ad group performance" in result["error"]

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_com_date_range(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import ad_group_performance_report

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(ad_group_performance_report("123", date_range="LAST_7_DAYS"))
        query_usado = mock_service.search.call_args[1]["query"]
        assert "DURING LAST_7_DAYS" in query_usado


class TestSearchTermsReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_retorna_search_terms(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import search_terms_report

        mock_row = MagicMock()
        mock_row.search_term_view.search_term = "comprar tenis nike"
        mock_row.search_term_view.status.name = "ADDED"
        mock_row.ad_group.id = 222
        mock_row.ad_group.name = "Ad Group Tenis"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Campaign Search"
        mock_row.metrics.impressions = 500
        mock_row.metrics.clicks = 30
        mock_row.metrics.cost_micros = 15_000_000
        mock_row.metrics.conversions = 2.0
        mock_row.metrics.ctr = 0.06

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(search_terms_report("123"))
        assert result["data"]["count"] == 1
        row = result["data"]["report"][0]
        assert row["search_term"] == "comprar tenis nike"
        assert row["ad_group_id"] == "222"
        assert row["ad_group_name"] == "Ad Group Tenis"
        assert row["campaign_name"] == "Campaign Search"
        assert row["cost"] == 15.0
        assert row["ctr"] == 6.0

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_com_campaign_id_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import search_terms_report

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(search_terms_report("123", campaign_id="999"))
        query_usado = mock_service.search.call_args[1]["query"]
        assert "campaign.id = 999" in query_usado

    def test_campaign_id_invalido(self):
        from mcp_google_ads.tools.reporting import search_terms_report

        result = assert_error(search_terms_report("123", campaign_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_multiplas_rows(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import search_terms_report

        row1 = MagicMock()
        row1.search_term_view.search_term = "termo 1"
        row1.search_term_view.status.name = "ADDED"
        row1.ad_group.id = 222
        row1.ad_group.name = "AG1"
        row1.campaign.id = 111
        row1.campaign.name = "C1"
        row1.metrics.impressions = 100
        row1.metrics.clicks = 10
        row1.metrics.cost_micros = 5_000_000
        row1.metrics.conversions = 1.0
        row1.metrics.ctr = 0.1

        row2 = MagicMock()
        row2.search_term_view.search_term = "termo 2"
        row2.search_term_view.status.name = "NONE"
        row2.ad_group.id = 333
        row2.ad_group.name = "AG2"
        row2.campaign.id = 111
        row2.campaign.name = "C1"
        row2.metrics.impressions = 200
        row2.metrics.clicks = 20
        row2.metrics.cost_micros = 10_000_000
        row2.metrics.conversions = 2.5
        row2.metrics.ctr = 0.1

        mock_service = MagicMock()
        mock_service.search.return_value = [row1, row2]
        mock_get_service.return_value = mock_service

        result = assert_success(search_terms_report("123"))
        assert result["data"]["count"] == 2
        assert result["data"]["report"][0]["search_term"] == "termo 1"
        assert result["data"]["report"][1]["search_term"] == "termo 2"

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_error_api(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import search_terms_report

        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("Permission denied")
        mock_get_service.return_value = mock_service

        result = assert_error(search_terms_report("123"))
        assert "Failed to get search terms report" in result["error"]


class TestComparisonReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_retorna_comparacao_com_deltas(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import comparison_report

        mock_row_current = MagicMock()
        mock_row_current.campaign.id = 111
        mock_row_current.campaign.name = "Test Campaign"
        mock_row_current.metrics.impressions = 1000
        mock_row_current.metrics.clicks = 50
        mock_row_current.metrics.cost_micros = 25_000_000
        mock_row_current.metrics.conversions = 5.0
        mock_row_current.metrics.conversions_value = 500.0
        mock_row_current.metrics.ctr = 0.05
        mock_row_current.metrics.average_cpc = 500_000

        mock_row_previous = MagicMock()
        mock_row_previous.campaign.id = 111
        mock_row_previous.campaign.name = "Test Campaign"
        mock_row_previous.metrics.impressions = 800
        mock_row_previous.metrics.clicks = 40
        mock_row_previous.metrics.cost_micros = 20_000_000
        mock_row_previous.metrics.conversions = 4.0
        mock_row_previous.metrics.conversions_value = 400.0
        mock_row_previous.metrics.ctr = 0.05
        mock_row_previous.metrics.average_cpc = 500_000

        mock_service = MagicMock()
        mock_service.search.side_effect = [[mock_row_current], [mock_row_previous]]
        mock_get_service.return_value = mock_service

        result = assert_success(
            comparison_report(
                "123",
                current_start="2024-02-01",
                current_end="2024-02-28",
                previous_start="2024-01-01",
                previous_end="2024-01-31",
            )
        )
        data = result["data"]
        assert data["current_period"]["start"] == "2024-02-01"
        assert data["previous_period"]["start"] == "2024-01-01"
        assert "deltas" in data
        assert data["deltas"]["impressions"]["delta"] == 200
        assert data["deltas"]["clicks"]["delta"] == 10

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_com_campaign_id_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import comparison_report

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(
            comparison_report(
                "123",
                campaign_id="111",
                current_start="2024-02-01",
                current_end="2024-02-28",
                previous_start="2024-01-01",
                previous_end="2024-01-31",
            )
        )
        query_usado = mock_service.search.call_args_list[0][1]["query"]
        assert "campaign.id = 111" in query_usado

    def test_data_invalida(self):
        from mcp_google_ads.tools.reporting import comparison_report

        result = assert_error(
            comparison_report(
                "123",
                current_start="not-a-date",
                current_end="2024-02-28",
                previous_start="2024-01-01",
                previous_end="2024-01-31",
            )
        )
        assert "inválida" in result["error"] or "Failed" in result["error"]

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_campaign_id_invalido(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import comparison_report

        result = assert_error(
            comparison_report(
                "123",
                campaign_id="abc",
                current_start="2024-02-01",
                current_end="2024-02-28",
                previous_start="2024-01-01",
                previous_end="2024-01-31",
            )
        )
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_api_exception(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import comparison_report

        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("Quota exceeded")
        mock_get_service.return_value = mock_service

        result = assert_error(
            comparison_report(
                "123",
                current_start="2024-02-01",
                current_end="2024-02-28",
                previous_start="2024-01-01",
                previous_end="2024-01-31",
            )
        )
        assert "Failed to generate comparison report" in result["error"]

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_delta_zero_no_previous(self, mock_resolve, mock_get_service):
        """Quando periodo anterior tem 0 impressoes, pct_change deve ser 0."""
        from mcp_google_ads.tools.reporting import comparison_report

        mock_service = MagicMock()
        mock_service.search.side_effect = [[], []]
        mock_get_service.return_value = mock_service

        result = assert_success(
            comparison_report(
                "123",
                current_start="2024-02-01",
                current_end="2024-02-28",
                previous_start="2024-01-01",
                previous_end="2024-01-31",
            )
        )
        assert result["data"]["deltas"]["impressions"]["pct_change"] == 0


class TestAgeGenderPerformanceReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_retorna_age_e_gender(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import age_gender_performance_report

        age_row = MagicMock()
        age_row.ad_group_criterion.age_range.type_.name = "AGE_RANGE_25_34"
        age_row.campaign.id = 111
        age_row.campaign.name = "C1"
        age_row.metrics.impressions = 300
        age_row.metrics.clicks = 15
        age_row.metrics.cost_micros = 7_500_000
        age_row.metrics.conversions = 1.0
        age_row.metrics.ctr = 0.05

        gender_row = MagicMock()
        gender_row.ad_group_criterion.gender.type_.name = "MALE"
        gender_row.campaign.id = 111
        gender_row.campaign.name = "C1"
        gender_row.metrics.impressions = 600
        gender_row.metrics.clicks = 30
        gender_row.metrics.cost_micros = 15_000_000
        gender_row.metrics.conversions = 2.5
        gender_row.metrics.ctr = 0.05

        mock_service = MagicMock()
        mock_service.search.side_effect = [[age_row], [gender_row]]
        mock_get_service.return_value = mock_service

        result = assert_success(age_gender_performance_report("123"))
        data = result["data"]
        assert data["age_count"] == 1
        assert data["gender_count"] == 1
        assert data["age_report"][0]["age_range"] == "AGE_RANGE_25_34"
        assert data["gender_report"][0]["gender"] == "MALE"

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_com_campaign_id_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import age_gender_performance_report

        mock_service = MagicMock()
        mock_service.search.side_effect = [[], []]
        mock_get_service.return_value = mock_service

        assert_success(age_gender_performance_report("123", campaign_id="111"))
        query_usado = mock_service.search.call_args_list[0][1]["query"]
        assert "campaign.id = 111" in query_usado

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_campaign_id_invalido(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import age_gender_performance_report

        result = assert_error(age_gender_performance_report("123", campaign_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_error_api(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import age_gender_performance_report

        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("Network error")
        mock_get_service.return_value = mock_service

        result = assert_error(age_gender_performance_report("123"))
        assert "Failed to get age/gender performance" in result["error"]


class TestHourlyPerformanceReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_retorna_hourly_report(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import hourly_performance_report

        mock_row = MagicMock()
        mock_row.segments.hour = 14
        mock_row.segments.day_of_week.name = "MONDAY"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Test"
        mock_row.metrics.impressions = 200
        mock_row.metrics.clicks = 10
        mock_row.metrics.cost_micros = 5_000_000
        mock_row.metrics.conversions = 1.0
        mock_row.metrics.ctr = 0.05

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(hourly_performance_report("123"))
        row = result["data"]["report"][0]
        assert row["hour"] == 14
        assert row["day_of_week"] == "MONDAY"

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_default_date_range_last_7_days(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import hourly_performance_report

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(hourly_performance_report("123"))
        query_usado = mock_service.search.call_args[1]["query"]
        assert "DURING LAST_7_DAYS" in query_usado

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_error_api(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import hourly_performance_report

        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("Server error")
        mock_get_service.return_value = mock_service

        result = assert_error(hourly_performance_report("123"))
        assert "Failed to get hourly performance" in result["error"]


class TestPlacementReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_retorna_placement_report(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import placement_report

        mock_row = MagicMock()
        mock_row.detail_placement_view.display_name = "example.com"
        mock_row.detail_placement_view.target_url = "https://example.com"
        mock_row.detail_placement_view.placement_type.name = "WEBSITE"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Display Campaign"
        mock_row.metrics.impressions = 5000
        mock_row.metrics.clicks = 100
        mock_row.metrics.cost_micros = 50_000_000
        mock_row.metrics.conversions = 3.0
        mock_row.metrics.ctr = 0.02

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(placement_report("123"))
        row = result["data"]["report"][0]
        assert row["display_name"] == "example.com"
        assert row["placement_type"] == "WEBSITE"

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_error_api(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import placement_report

        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("Service unavailable")
        mock_get_service.return_value = mock_service

        result = assert_error(placement_report("123"))
        assert "Failed to get placement report" in result["error"]


class TestChangeHistoryReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_retorna_change_history(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import change_history_report

        mock_row = MagicMock()
        mock_row.change_event.change_date_time = "2024-02-01 10:00:00"
        mock_row.change_event.change_resource_type.name = "CAMPAIGN"
        mock_row.change_event.change_resource_name = "customers/123/campaigns/111"
        mock_row.change_event.resource_change_operation.name = "UPDATE"
        mock_row.change_event.user_email = "user@example.com"
        mock_row.change_event.client_type.name = "GOOGLE_ADS_WEB_CLIENT"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(change_history_report("123"))
        assert result["data"]["count"] == 1
        row = result["data"]["changes"][0]
        assert row["resource_type"] == "CAMPAIGN"
        assert row["operation"] == "UPDATE"
        assert row["user_email"] == "user@example.com"

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_default_date_range_last_7_days(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import change_history_report

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(change_history_report("123"))
        query_usado = mock_service.search.call_args[1]["query"]
        assert "DURING LAST_7_DAYS" in query_usado


class TestGeographicPerformanceReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_retorna_geo_report(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import geographic_performance_report

        mock_row = MagicMock()
        mock_row.geographic_view.country_criterion_id = 2076
        mock_row.geographic_view.location_type.name = "AREA_OF_INTEREST"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Campaign Brasil"
        mock_row.metrics.impressions = 2000
        mock_row.metrics.clicks = 100
        mock_row.metrics.cost_micros = 50_000_000
        mock_row.metrics.conversions = 5.0
        mock_row.metrics.ctr = 0.05

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(geographic_performance_report("123"))
        row = result["data"]["report"][0]
        assert row["country_criterion_id"] == "2076"
        assert row["location_type"] == "AREA_OF_INTEREST"


class TestAudiencePerformanceReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_retorna_audience_report(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import audience_performance_report

        mock_row = MagicMock()
        mock_row.campaign_audience_view.resource_name = "customers/123/campaignAudienceViews/111~222"
        mock_row.campaign.id = 111
        mock_row.campaign.name = "Campaign Audience"
        mock_row.metrics.impressions = 1500
        mock_row.metrics.clicks = 75
        mock_row.metrics.cost_micros = 37_500_000
        mock_row.metrics.conversions = 4.0
        mock_row.metrics.ctr = 0.05
        mock_row.metrics.average_cpc = 500_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(audience_performance_report("123"))
        row = result["data"]["report"][0]
        assert row["campaign_id"] == "111"
        assert row["impressions"] == 1500


class TestAdPerformanceReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_retorna_ad_report(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import ad_performance_report

        mock_row = MagicMock()
        mock_row.ad_group_ad.ad.id = 333
        mock_row.ad_group_ad.ad.type_.name = "RESPONSIVE_SEARCH_AD"
        mock_row.ad_group_ad.status.name = "ENABLED"
        mock_row.ad_group_ad.ad_strength.name = "GOOD"
        mock_row.ad_group.id = 222
        mock_row.campaign.id = 111
        mock_row.metrics.impressions = 600
        mock_row.metrics.clicks = 30
        mock_row.metrics.cost_micros = 15_000_000
        mock_row.metrics.conversions = 2.0
        mock_row.metrics.ctr = 0.05
        mock_row.metrics.average_cpc = 500_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(ad_performance_report("123"))
        row = result["data"]["report"][0]
        assert row["ad_id"] == "333"
        assert row["ad_type"] == "RESPONSIVE_SEARCH_AD"
        assert row["ad_strength"] == "GOOD"

    def test_campaign_id_invalido(self):
        from mcp_google_ads.tools.reporting import ad_performance_report

        result = assert_error(ad_performance_report("123", campaign_id="abc"))
        assert "inválido" in result["error"]

    def test_ad_group_id_invalido(self):
        from mcp_google_ads.tools.reporting import ad_performance_report

        result = assert_error(ad_performance_report("123", ad_group_id="xyz"))
        assert "inválido" in result["error"]


class TestKeywordPerformanceReport:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_retorna_keyword_report(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.reporting import keyword_performance_report

        mock_row = MagicMock()
        mock_row.ad_group_criterion.keyword.text = "comprar sapatos"
        mock_row.ad_group_criterion.keyword.match_type.name = "EXACT"
        mock_row.ad_group_criterion.status.name = "ENABLED"
        mock_row.ad_group_criterion.quality_info.quality_score = 7
        mock_row.ad_group.id = 222
        mock_row.campaign.id = 111
        mock_row.metrics.impressions = 400
        mock_row.metrics.clicks = 20
        mock_row.metrics.cost_micros = 10_000_000
        mock_row.metrics.conversions = 1.5
        mock_row.metrics.ctr = 0.05
        mock_row.metrics.average_cpc = 500_000

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(keyword_performance_report("123"))
        row = result["data"]["report"][0]
        assert row["keyword"] == "comprar sapatos"
        assert row["quality_score"] == 7

    def test_ad_group_id_invalido(self):
        from mcp_google_ads.tools.reporting import keyword_performance_report

        result = assert_error(keyword_performance_report("123", ad_group_id="abc"))
        assert "inválido" in result["error"]


class TestPmaxSearchTermInsights:
    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_success(self, mock_resolve, mock_get_service):
        row = MagicMock()
        row.campaign_search_term_insight.category_label = "web design services"
        row.campaign_search_term_insight.id = 12345
        row.campaign_search_term_insight.campaign_id = 111
        mock_service = MagicMock()
        mock_service.search.return_value = [row]
        mock_get_service.return_value = mock_service

        result = pmax_search_term_insights(customer_id="123")
        data = assert_success(result)
        assert data["data"]["count"] == 1
        assert data["data"]["insights"][0]["category_label"] == "web design services"

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_with_campaign_filter(self, mock_resolve, mock_get_service):
        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = pmax_search_term_insights(customer_id="123", campaign_id="456")
        data = assert_success(result)
        assert data["data"]["count"] == 0
        query = mock_service.search.call_args.kwargs["query"]
        assert "campaign_search_term_insight.campaign_id = 456" in query

    @patch("mcp_google_ads.tools.reporting.get_service")
    @patch("mcp_google_ads.tools.reporting.resolve_customer_id", return_value="123")
    def test_error(self, mock_resolve, mock_get_service):
        mock_service = MagicMock()
        mock_service.search.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = pmax_search_term_insights(customer_id="123")
        error_data = assert_error(result)
        assert "Failed to get PMax search term insights" in error_data["error"]
