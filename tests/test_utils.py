"""Tests for utils.py helper functions."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from mcp_google_ads.utils import (
    build_resource_name,
    error_response,
    format_micros,
    handle_rate_limit,
    log_api_error,
    log_tool_call,
    parse_google_ads_error,
    resolve_customer_id,
    success_response,
    to_micros,
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


class TestBuildResourceName:
    def test_builds_name(self):
        result = build_resource_name("campaigns", "123", "456")
        assert result == "customers/123/campaigns/456"


class TestParseGoogleAdsError:
    def test_with_failure_attr(self):
        error = MagicMock()
        err1 = MagicMock()
        err1.error_code = "CAMPAIGN_ERROR"
        err1.message = "Invalid campaign"
        error.failure.errors = [err1]
        result = parse_google_ads_error(error)
        assert "CAMPAIGN_ERROR" in result
        assert "Invalid campaign" in result

    def test_without_failure(self):
        error = Exception("simple error")
        result = parse_google_ads_error(error)
        assert result == "simple error"


class TestHandleRateLimit:
    def test_detects_quota(self):
        error = Exception("QUOTA exceeded for project")
        assert handle_rate_limit(error) is True

    def test_detects_rate_limit(self):
        error = Exception("rate limit reached")
        assert handle_rate_limit(error) is True

    def test_not_rate_limit(self):
        error = Exception("invalid campaign name")
        assert handle_rate_limit(error) is False


class TestLogToolCall:
    @patch("mcp_google_ads.utils.logger")
    def test_logs_info(self, mock_logger):
        log_tool_call("list_campaigns", "123", status_filter="ENABLED", limit=None)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0]
        assert "list_campaigns" in call_args[1]
        assert "123" in call_args[2]


class TestLogApiError:
    @patch("mcp_google_ads.utils.logger")
    def test_logs_error(self, mock_logger):
        log_api_error("create_campaign", Exception("fail"), "123")
        mock_logger.error.assert_called_once()
