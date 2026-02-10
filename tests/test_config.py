"""Tests for config.py."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from mcp_google_ads.config import GoogleAdsConfig, load_config


class TestGoogleAdsConfig:
    def test_validate_all_present(self):
        config = GoogleAdsConfig(
            client_id="id",
            client_secret="secret",
            developer_token="token",
            refresh_token="refresh",
            login_customer_id="123",
        )
        assert config.validate() == []

    def test_validate_missing_fields(self):
        config = GoogleAdsConfig(
            client_id="",
            client_secret="secret",
            developer_token="",
            refresh_token="refresh",
            login_customer_id="123",
        )
        missing = config.validate()
        assert "GOOGLE_ADS_CLIENT_ID" in missing
        assert "GOOGLE_ADS_DEVELOPER_TOKEN" in missing
        assert "GOOGLE_ADS_CLIENT_SECRET" not in missing

    def test_default_customer_id_optional(self):
        config = GoogleAdsConfig(
            client_id="id",
            client_secret="secret",
            developer_token="token",
            refresh_token="refresh",
            login_customer_id="123",
            default_customer_id="",
        )
        assert config.validate() == []

    def test_frozen(self):
        config = GoogleAdsConfig(
            client_id="id",
            client_secret="secret",
            developer_token="token",
            refresh_token="refresh",
            login_customer_id="123",
        )
        with pytest.raises(Exception):
            config.client_id = "new"  # type: ignore[misc]


class TestLoadConfig:
    @patch.dict(os.environ, {
        "GOOGLE_ADS_CLIENT_ID": "test-id",
        "GOOGLE_ADS_CLIENT_SECRET": "test-secret",
        "GOOGLE_ADS_DEVELOPER_TOKEN": "test-token",
        "GOOGLE_ADS_REFRESH_TOKEN": "test-refresh",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "123456",
    })
    def test_loads_from_env(self):
        config = load_config()
        assert config.client_id == "test-id"
        assert config.login_customer_id == "123456"

    @patch.dict(os.environ, {}, clear=True)
    def test_raises_on_missing(self):
        with pytest.raises(EnvironmentError, match="Missing required"):
            load_config()
