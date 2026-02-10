"""Tests for utils.py helper functions."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from mcp_google_ads.utils import (
    build_date_clause,
    error_response,
    format_micros,
    resolve_customer_id,
    success_response,
    to_micros,
    validate_date,
    validate_date_range,
    validate_numeric_id,
    validate_status,
)


class TestResolveCustomerId:
    def test_returns_provided_id(self):
        assert resolve_customer_id("1234567890") == "1234567890"

    def test_strips_hyphens(self):
        assert resolve_customer_id("123-456-7890") == "1234567890"

    @patch("mcp_google_ads.utils.get_config")
    def test_falls_back_to_default(self, mock_config):
        mock_config.return_value.default_customer_id = "9999999999"
        assert resolve_customer_id(None) == "9999999999"

    @patch("mcp_google_ads.utils.get_config")
    def test_raises_when_no_id(self, mock_config):
        mock_config.return_value.default_customer_id = ""
        with pytest.raises(Exception, match="customer_id is required"):
            resolve_customer_id(None)


class TestSuccessResponse:
    def test_basic_success(self):
        result = json.loads(success_response({"key": "value"}))
        assert result["status"] == "success"
        assert result["data"]["key"] == "value"

    def test_with_message(self):
        result = json.loads(success_response({"a": 1}, message="Done"))
        assert result["message"] == "Done"

    def test_without_message(self):
        result = json.loads(success_response({"a": 1}))
        assert "message" not in result


class TestErrorResponse:
    def test_basic_error(self):
        result = json.loads(error_response("Something failed"))
        assert result["status"] == "error"
        assert result["error"] == "Something failed"

    def test_with_details(self):
        result = json.loads(error_response("fail", details={"field": "bad"}))
        assert result["details"]["field"] == "bad"

    def test_without_details(self):
        result = json.loads(error_response("fail"))
        assert "details" not in result


class TestFormatMicros:
    def test_converts_micros(self):
        assert format_micros(10_500_000) == 10.5

    def test_zero(self):
        assert format_micros(0) == 0.0

    def test_none(self):
        assert format_micros(None) is None


class TestToMicros:
    def test_converts_to_micros(self):
        assert to_micros(10.50) == 10_500_000

    def test_zero(self):
        assert to_micros(0) == 0

    def test_integer(self):
        assert to_micros(100) == 100_000_000


class TestValidateStatus:
    def test_valid_statuses(self):
        assert validate_status("ENABLED") == "ENABLED"
        assert validate_status("paused") == "PAUSED"
        assert validate_status("Removed") == "REMOVED"

    def test_invalid_status(self):
        with pytest.raises(Exception, match="Status inválido"):
            validate_status("ACTIVE")


class TestValidateDateRange:
    def test_valid_ranges(self):
        assert validate_date_range("LAST_30_DAYS") == "LAST_30_DAYS"
        assert validate_date_range("today") == "TODAY"
        assert validate_date_range("THIS_MONTH") == "THIS_MONTH"

    def test_invalid_range(self):
        with pytest.raises(Exception, match="Date range inválido"):
            validate_date_range("LAST_3_DAYS")


class TestValidateDate:
    def test_valid_date(self):
        assert validate_date("2024-01-15") == "2024-01-15"

    def test_invalid_date(self):
        with pytest.raises(Exception, match="Data inválida"):
            validate_date("01-15-2024")

    def test_invalid_format(self):
        with pytest.raises(Exception, match="Data inválida"):
            validate_date("2024/01/15")


class TestValidateNumericId:
    def test_valid_id(self):
        assert validate_numeric_id("1234567890") == "1234567890"

    def test_strips_hyphens(self):
        assert validate_numeric_id("123-456-7890") == "1234567890"

    def test_invalid_id(self):
        with pytest.raises(Exception, match="inválido"):
            validate_numeric_id("abc123")


class TestBuildDateClause:
    def test_with_start_end(self):
        result = build_date_clause(start_date="2024-01-01", end_date="2024-01-31")
        assert result == "segments.date BETWEEN '2024-01-01' AND '2024-01-31'"

    def test_with_date_range(self):
        result = build_date_clause(date_range="LAST_7_DAYS")
        assert result == "DURING LAST_7_DAYS"

    def test_default(self):
        result = build_date_clause()
        assert result == "DURING LAST_30_DAYS"

    def test_custom_default(self):
        result = build_date_clause(default="LAST_7_DAYS")
        assert result == "DURING LAST_7_DAYS"

    def test_start_end_overrides_date_range(self):
        result = build_date_clause(
            date_range="LAST_7_DAYS",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        assert "BETWEEN" in result
