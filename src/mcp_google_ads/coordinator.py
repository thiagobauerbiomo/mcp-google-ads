"""Singleton FastMCP instance for the Google Ads MCP Server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "google-ads",
    instructions="""MCP Server for Google Ads API v23 — Full CRUD operations for managing Google Ads campaigns.

## Account Structure
This server connects to an MCC (Manager) account that manages multiple client accounts.
Always start by listing accessible customers, then select a specific client account (customer_id) for operations.

## Typical Workflow
1. `list_accessible_customers` → discover the MCC account
2. `list_customer_clients` → list all client accounts under the MCC
3. `list_campaigns(customer_id)` → list campaigns for a specific client
4. Use reporting tools to analyze performance
5. Use mutation tools to create/update/remove resources

## Safety
- All newly created resources (campaigns, ad groups, ads) are set to PAUSED by default
- Setting status to ENABLED will start spending real budget — always confirm with the user first
- Setting status to REMOVED is permanent and cannot be undone
- The `execute_gaql` tool allows raw GAQL queries for advanced use cases

## Reports
All reporting tools support custom date ranges via `start_date`/`end_date` (YYYY-MM-DD) or predefined `date_range` (LAST_7_DAYS, LAST_30_DAYS, etc.). Default is LAST_30_DAYS.

## Currency
Monetary values are in micros (1 BRL = 1,000,000 micros). The response includes both raw micros and converted values for convenience.
""",
)
