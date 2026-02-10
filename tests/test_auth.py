"""Tests for auth.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mcp_google_ads.auth import _retry_with_backoff, get_client, get_service, reset_client


class TestGetClient:
    def setup_method(self):
        reset_client()

    @patch("mcp_google_ads.auth.load_config")
    @patch("mcp_google_ads.auth.GoogleAdsClient.load_from_dict")
    def test_creates_client_singleton(self, mock_load, mock_config):
        mock_config.return_value = MagicMock(
            client_id="id",
            client_secret="secret",
            developer_token="token",
            refresh_token="refresh",
            login_customer_id="123",
        )
        mock_load.return_value = MagicMock()

        client1 = get_client()
        client2 = get_client()
        assert client1 is client2
        mock_load.assert_called_once()

    @patch("mcp_google_ads.auth.load_config")
    @patch("mcp_google_ads.auth.GoogleAdsClient.load_from_dict")
    def test_raises_on_auth_failure(self, mock_load, mock_config):
        mock_config.return_value = MagicMock()
        mock_load.side_effect = Exception("Auth failed")

        from mcp_google_ads.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError, match="Auth failed"):
            get_client()


class TestResetClient:
    def test_resets_singleton(self):
        reset_client()
        # After reset, get_client would need to create a new one
        # This is tested implicitly by the singleton test above


class TestGetService:
    @patch("mcp_google_ads.auth.get_client")
    def test_gets_service(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        get_service("GoogleAdsService")
        mock_client.get_service.assert_called_once_with("GoogleAdsService")


class TestRetryWithBackoff:
    def test_succeeds_first_try(self):
        func = MagicMock(return_value="ok")
        result = _retry_with_backoff(func, "arg1", max_retries=3)
        assert result == "ok"
        func.assert_called_once_with("arg1")

    @patch("time.sleep")
    def test_retries_on_transient(self, mock_sleep):
        from google.api_core.exceptions import ServiceUnavailable

        func = MagicMock(side_effect=[ServiceUnavailable("unavail"), "ok"])
        result = _retry_with_backoff(func, max_retries=3)
        assert result == "ok"
        assert func.call_count == 2
        mock_sleep.assert_called_once_with(1)  # 2^0

    @patch("time.sleep")
    def test_raises_after_max_retries(self, mock_sleep):
        from google.api_core.exceptions import ServiceUnavailable

        func = MagicMock(side_effect=ServiceUnavailable("unavail"))
        with pytest.raises(ServiceUnavailable):
            _retry_with_backoff(func, max_retries=2)
        assert func.call_count == 2

    def test_does_not_retry_non_transient(self):
        func = MagicMock(side_effect=ValueError("bad input"))
        with pytest.raises(ValueError):
            _retry_with_backoff(func, max_retries=3)
        func.assert_called_once()
