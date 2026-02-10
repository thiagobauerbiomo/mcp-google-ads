"""Custom exceptions for Google Ads MCP Server."""

from __future__ import annotations


class GoogleAdsMCPError(Exception):
    """Base exception for Google Ads MCP errors."""


class AuthenticationError(GoogleAdsMCPError):
    """Raised when authentication fails."""


class CustomerNotFoundError(GoogleAdsMCPError):
    """Raised when a customer ID is not found or inaccessible."""


class InvalidQueryError(GoogleAdsMCPError):
    """Raised when a GAQL query is malformed."""


class MutationError(GoogleAdsMCPError):
    """Raised when a mutate operation fails."""


class ResourceNotFoundError(GoogleAdsMCPError):
    """Raised when a requested resource does not exist."""


class QuotaExceededError(GoogleAdsMCPError):
    """Raised when API quota is exceeded."""
