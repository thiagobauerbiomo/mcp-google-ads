"""Tests for auth.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mcp_google_ads.auth import get_client, get_service, reset_client


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


class TestGetService:
    @patch("mcp_google_ads.auth.get_client")
    def test_gets_service(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        get_service("GoogleAdsService")
        mock_client.get_service.assert_called_once_with("GoogleAdsService")
