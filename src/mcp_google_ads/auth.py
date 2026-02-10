"""Google Ads API client authentication."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from google.ads.googleads.client import GoogleAdsClient

from .config import GoogleAdsConfig, load_config
from .exceptions import AuthenticationError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_client: GoogleAdsClient | None = None
_config: GoogleAdsConfig | None = None


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
        raise AuthenticationError(f"Failed to initialize Google Ads client: {e}") from e


def get_service(service_name: str):
    """Get a Google Ads API service by name."""
    return get_client().get_service(service_name)


def get_search_request(customer_id: str, query: str):
    """Create a SearchGoogleAdsRequest."""
    client = get_client()
    request = client.get_type("SearchGoogleAdsRequest")
    request.customer_id = customer_id
    request.query = query
    return request


def _retry_with_backoff(func, *args, max_retries: int = 3, **kwargs):
    """Retry a function call with exponential backoff for transient errors.

    Retries on ServiceUnavailable, DeadlineExceeded, and InternalServerError.
    """
    import time

    from google.api_core.exceptions import DeadlineExceeded, InternalServerError, ServiceUnavailable

    retryable = (ServiceUnavailable, DeadlineExceeded, InternalServerError)

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except retryable as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            logger.warning("Transient error (attempt %d/%d), retrying in %ds: %s", attempt + 1, max_retries, wait, e)
            time.sleep(wait)


def reset_client() -> None:
    """Reset client singleton (for testing)."""
    global _client, _config
    _client = None
    _config = None
