"""Environment configuration for Google Ads MCP Server."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GoogleAdsConfig:
    """Configuration loaded from environment variables."""

    client_id: str = field(default_factory=lambda: os.environ.get("GOOGLE_ADS_CLIENT_ID", ""))
    client_secret: str = field(default_factory=lambda: os.environ.get("GOOGLE_ADS_CLIENT_SECRET", ""))
    developer_token: str = field(default_factory=lambda: os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""))
    refresh_token: str = field(default_factory=lambda: os.environ.get("GOOGLE_ADS_REFRESH_TOKEN", ""))
    login_customer_id: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")
    )
    default_customer_id: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "")
    )

    def validate(self) -> list[str]:
        """Return list of missing required fields."""
        required = {
            "GOOGLE_ADS_CLIENT_ID": self.client_id,
            "GOOGLE_ADS_CLIENT_SECRET": self.client_secret,
            "GOOGLE_ADS_DEVELOPER_TOKEN": self.developer_token,
            "GOOGLE_ADS_REFRESH_TOKEN": self.refresh_token,
            "GOOGLE_ADS_LOGIN_CUSTOMER_ID": self.login_customer_id,
        }
        return [k for k, v in required.items() if not v]


def load_config() -> GoogleAdsConfig:
    """Load and validate configuration from environment."""
    config = GoogleAdsConfig()
    missing = config.validate()
    if missing:
        raise OSError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    return config
