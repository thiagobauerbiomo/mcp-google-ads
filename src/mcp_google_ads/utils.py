"""Utility helpers for Google Ads MCP Server."""

from __future__ import annotations

import json
import re
from typing import Any

from google.protobuf.json_format import MessageToDict

from .auth import get_config
from .exceptions import GoogleAdsMCPError


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


def format_micros(micros: int | None) -> float | None:
    """Convert micros to standard currency unit."""
    if micros is None:
        return None
    return round(micros / 1_000_000, 2)


def to_micros(amount: float) -> int:
    """Convert currency amount to micros."""
    return int(amount * 1_000_000)


# --- Validação GAQL ---

_VALID_STATUSES = {"ENABLED", "PAUSED", "REMOVED"}

_VALID_DATE_RANGES = {
    "TODAY", "YESTERDAY", "LAST_7_DAYS", "LAST_14_DAYS", "LAST_30_DAYS",
    "THIS_MONTH", "LAST_MONTH", "THIS_QUARTER", "LAST_QUARTER",
    "THIS_YEAR", "LAST_YEAR",
}

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_NUMERIC_PATTERN = re.compile(r"^\d+$")


def validate_status(status: str) -> str:
    """Validate and return a GAQL-safe status value."""
    upper = status.upper()
    if upper not in _VALID_STATUSES:
        raise GoogleAdsMCPError(f"Status inválido: '{status}'. Use: {_VALID_STATUSES}")
    return upper


def validate_date_range(date_range: str) -> str:
    """Validate a predefined GAQL date range."""
    upper = date_range.upper()
    if upper not in _VALID_DATE_RANGES:
        raise GoogleAdsMCPError(f"Date range inválido: '{date_range}'. Use: {_VALID_DATE_RANGES}")
    return upper


def validate_date(date_str: str) -> str:
    """Validate a YYYY-MM-DD date string."""
    if not _DATE_PATTERN.match(date_str):
        raise GoogleAdsMCPError(f"Data inválida: '{date_str}'. Formato esperado: YYYY-MM-DD")
    return date_str


def validate_numeric_id(value: str, field_name: str = "ID") -> str:
    """Validate that a value is a numeric ID (safe for GAQL)."""
    clean = value.replace("-", "")
    if not _NUMERIC_PATTERN.match(clean):
        raise GoogleAdsMCPError(f"{field_name} inválido: '{value}'. Deve ser numérico.")
    return clean


_ENUM_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_enum_value(value: str, field_name: str = "value") -> str:
    """Validate that a string looks like a GAQL enum (alphanumeric + underscores only)."""
    if not _ENUM_PATTERN.match(value):
        raise GoogleAdsMCPError(f"{field_name} inválido: '{value}'. Apenas letras, números e underscores.")
    return value.upper()


def validate_limit(limit: int, max_limit: int = 10000) -> int:
    """Validate that a limit is within acceptable bounds."""
    if limit < 1 or limit > max_limit:
        raise GoogleAdsMCPError(f"limit deve ser entre 1 e {max_limit}, recebido: {limit}")
    return limit


def build_date_clause(
    date_range: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    default: str = "LAST_30_DAYS",
) -> str:
    """Build a GAQL date clause (WHERE or DURING) from parameters.

    Returns a string like:
      "segments.date BETWEEN '2024-01-01' AND '2024-01-31'"
    or:
      "DURING LAST_30_DAYS"
    """
    if start_date and end_date:
        s = validate_date(start_date)
        e = validate_date(end_date)
        if s > e:
            raise GoogleAdsMCPError(f"start_date ({s}) deve ser anterior a end_date ({e})")
        return f"segments.date BETWEEN '{s}' AND '{e}'"
    if date_range:
        return f"DURING {validate_date_range(date_range)}"
    return f"DURING {validate_date_range(default)}"
