"""Singleton FastMCP instance for the Google Ads MCP Server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "google-ads",
    instructions="""MCP Server for Google Ads API v23 — 123 tools for full CRUD operations.

## Account Structure
This server connects to an MCC (Manager) account that manages multiple client accounts.
Always start by listing accessible customers, then select a specific client account (customer_id) for operations.

## Tool Categories (123 tools)
- **Accounts (4):** list_accessible_customers, get_customer_info, get_account_hierarchy, list_customer_clients
- **Account Management (3):** list_account_links, get_billing_info, list_account_users
- **Campaigns (7):** list, get, create, update, set_status, remove, list_labels
- **Campaign Types (8):** create_pmax, create_display, create_video, create_shopping, create_demand_gen, create_app, list/update asset_groups
- **Ad Groups (6):** list, get, create, update, set_status, remove
- **Ads (6):** list, get, create_rsa, update, set_status, get_strength
- **Keywords (9):** list, add, update, remove, neg_campaign, neg_shared, generate_ideas, forecast, list_negative
- **Budgets (4):** list, get, create, update
- **Bidding (5):** list, get, create, update, set_campaign_strategy
- **Reporting (14):** campaign/adgroup/ad/keyword perf, search_terms, audience, geo, change_history, device, hourly, age_gender, placement, quality_score, comparison
- **Dashboard (2):** mcc_performance_summary, account_dashboard
- **Audiences (6):** list_segments, add/remove targeting, suggest_geo, list_targeting, add_audience_to_ad_group
- **Extensions (14):** list_assets, sitelinks, callouts, snippets, call, remove, image, video, lead_form, price, promotion, link_campaign, link_ad_group, unlink
- **Labels (8):** list, create, remove, apply_to_campaign/ad_group/ad/keyword, remove_from_resource
- **Shared Sets (6):** list, create, remove, list_members, link/unlink_to_campaign
- **Conversions (6):** list_actions, get_action, create_action, update_action, import_offline, list_goals
- **Targeting (7):** device_bid, create/list/remove ad_schedule, exclude_geo, add/remove language
- **Recommendations (5):** list, get, apply, dismiss, get_optimization_score
- **Experiments (5):** list, create, get, promote, end
- **GAQL (1):** execute_gaql (raw SELECT-only queries)

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
- Batch limits: max 5000 keywords/assets per call, 2000 conversions
- execute_gaql is SELECT-only with keyword blocklist and 10000 char limit

## Reports
All 14 reporting tools support custom date ranges via `start_date`/`end_date` (YYYY-MM-DD) or predefined `date_range` (LAST_7_DAYS, LAST_30_DAYS, etc.). Default is LAST_30_DAYS.

## Currency
Monetary values are in micros (1 BRL = 1,000,000 micros). The response includes both raw micros and converted values for convenience.
""",
)
