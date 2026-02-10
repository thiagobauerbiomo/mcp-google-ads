"""Google Ads API client authentication."""

from __future__ import annotations

import logging
import time

from google.ads.googleads.client import GoogleAdsClient

from .config import GoogleAdsConfig, load_config
from .exceptions import AuthenticationError

logger = logging.getLogger(__name__)

_client: GoogleAdsClient | None = None
_config: GoogleAdsConfig | None = None

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0


def get_config() -> GoogleAdsConfig:
    """Get or create the config singleton."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_client() -> GoogleAdsClient:
    """Get or create the GoogleAdsClient singleton using OAuth2 credentials."""
    global _client
    if _client is not None:
        return _client

    config = get_config()
    last_error = None

    for attempt in range(_MAX_RETRIES):
        try:
            _client = GoogleAdsClient.load_from_dict(
                {
                    "developer_token": config.developer_token,
                    "client_id": config.client_id,
                    "client_secret": config.client_secret,
                    "refresh_token": config.refresh_token,
                    "login_customer_id": config.login_customer_id,
                    "use_proto_plus": True,
                }
            )
            logger.info("Google Ads client initialized (MCC: %s)", config.login_customer_id)
            return _client
        except Exception as e:
            last_error = e
            if attempt < _MAX_RETRIES - 1:
                delay = _RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "Failed to initialize Google Ads client (attempt %d/%d): %s. Retrying in %.1fs...",
                    attempt + 1, _MAX_RETRIES, e, delay,
                )
                time.sleep(delay)

    raise AuthenticationError(f"Failed to initialize Google Ads client after {_MAX_RETRIES} attempts: {last_error}") from last_error


def get_service(service_name: str):
    """Get a Google Ads API service by name."""
    return get_client().get_service(service_name)


def reset_client() -> None:
    """Reset client singleton (for testing)."""
    global _client, _config
    _client = None
    _config = None
