"""Singleton FastMCP instance for the Google Ads MCP Server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "google-ads",
    instructions="MCP Server for Google Ads API v23 - Full CRUD operations",
)
