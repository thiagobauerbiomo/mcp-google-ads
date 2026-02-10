"""Custom exceptions for Google Ads MCP Server."""

from __future__ import annotations


class GoogleAdsMCPError(Exception):
    """Base exception for Google Ads MCP errors."""


class AuthenticationError(GoogleAdsMCPError):
    """Raised when authentication fails."""
