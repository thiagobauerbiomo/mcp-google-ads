"""Utility helpers for Google Ads MCP Server."""

from __future__ import annotations

import json
import logging
from typing import Any

from google.protobuf.json_format import MessageToDict

from .auth import get_config
from .exceptions import GoogleAdsMCPError

logger = logging.getLogger(__name__)


def resolve_customer_id(customer_id: str | None = None) -> str:
    """Resolve customer ID: use provided value or fall back to default."""
    cid = customer_id or get_config().default_customer_id
    if not cid:
        raise GoogleAdsMCPError(
            "customer_id is required (no default configured via GOOGLE_ADS_CUSTOMER_ID)"
        )
    return cid.replace("-", "")


def proto_to_dict(proto_message: Any) -> dict:
    """Convert a protobuf message to a Python dict."""
    try:
        return MessageToDict(
            proto_message._pb if hasattr(proto_message, "_pb") else proto_message,
            preserving_proto_field_name=True,
            including_default_value_fields=False,
        )
    except Exception:
        return {"raw": str(proto_message)}


def success_response(data: Any, message: str | None = None) -> str:
    """Build a consistent success JSON response."""
    result: dict[str, Any] = {"status": "success"}
    if message:
        result["message"] = message
    result["data"] = data
    return json.dumps(result, ensure_ascii=False, default=str)


def error_response(error: str, details: Any = None) -> str:
    """Build a consistent error JSON response."""
    result: dict[str, Any] = {"status": "error", "error": error}
    if details:
        result["details"] = details
    return json.dumps(result, ensure_ascii=False, default=str)


def parse_google_ads_error(error: Exception) -> str:
    """Extract a readable error message from a GoogleAdsException."""
    if hasattr(error, "failure"):
        messages = []
        for err in error.failure.errors:
            messages.append(f"{err.error_code}: {err.message}")
        return "; ".join(messages)
    return str(error)


def format_micros(micros: int | None) -> float | None:
    """Convert micros to standard currency unit."""
    if micros is None:
        return None
    return micros / 1_000_000


def to_micros(amount: float) -> int:
    """Convert currency amount to micros."""
    return int(amount * 1_000_000)


def build_resource_name(resource_type: str, customer_id: str, resource_id: str) -> str:
    """Build a Google Ads resource name string."""
    return f"customers/{customer_id}/{resource_type}/{resource_id}"
