# MCP Google Ads Server

MCP Server for Google Ads API v23 with full CRUD operations — **168 tools** across 23 modules. Built by [Biomo](https://biomo.com.br).

## Features

- **168 tools** for complete Google Ads management
- OAuth2 authentication with MCC (Manager) support
- Safety-first: all resources created PAUSED by default
- GAQL injection protection on all inputs
- Structured logging in all modules
- Consistent JSON responses with error handling
- Friendly error messages for common API errors (18 error codes mapped)
- Rate limit and quota detection with actionable messages
- AI-powered ad generation (text, images, audiences)
- Campaign health diagnostics and budget forecasting
- Batch operations for multi-resource status changes
- 630+ tests, 96% coverage

## Quick Start

### Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- Google Ads API credentials (OAuth2)

### Installation

```bash
# Clone
git clone git@github.com:thiagobauerbiomo/mcp-google-ads.git
cd mcp-google-ads

# Install dependencies
uv sync

# Run
uv run mcp-google-ads
```

### Environment Variables

```bash
GOOGLE_ADS_CLIENT_ID="your-oauth2-client-id"
GOOGLE_ADS_CLIENT_SECRET="your-oauth2-client-secret"
GOOGLE_ADS_DEVELOPER_TOKEN="your-developer-token"
GOOGLE_ADS_REFRESH_TOKEN="your-refresh-token"
GOOGLE_ADS_LOGIN_CUSTOMER_ID="your-mcc-id"

# Optional
GOOGLE_ADS_CUSTOMER_ID="default-customer-id"  # fallback when not specified per-tool
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

### Claude Code Integration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-google-ads", "mcp-google-ads"],
      "env": {
        "GOOGLE_ADS_DEVELOPER_TOKEN": "...",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "...",
        "GOOGLE_ADS_CLIENT_ID": "...",
        "GOOGLE_ADS_CLIENT_SECRET": "...",
        "GOOGLE_ADS_REFRESH_TOKEN": "..."
      }
    }
  }
}
```

## Tool Categories (168 tools)

| Category | Tools | Description |
|----------|-------|-------------|
| Accounts | 4 | List customers, get info, hierarchy, client list |
| Account Management | 3 | Account links, billing, users |
| Campaigns | 9 | CRUD, status, labels, tracking template, clone |
| Campaign Types | 14 | PMax, Display, Video, Shopping, Demand Gen, App, asset groups, listing groups |
| Ad Groups | 7 | CRUD, status management, clone |
| Ads | 7 | List, create RSA/RDA, update, status, ad strength |
| Keywords | 11 | CRUD, negatives (campaign/ad group/shared/PMax), ideas, forecasts |
| Budgets | 5 | CRUD + remove for campaign budgets |
| Bidding | 5 | Portfolio strategies, campaign assignment |
| Reporting | 21 | Campaign, ad group, ad, keyword, search terms, audience, geo, device, hourly, age/gender, placement, quality score, comparison, PMax insights, auction insights, landing page, asset performance, shopping, industry benchmarks |
| Dashboard | 2 | MCC summary, account dashboard |
| Audiences | 12 | Segments, targeting, geo suggestions, custom audiences, signals |
| Extensions | 16 | Assets: sitelinks, callouts, snippets, call, image, video, lead form, price, promotion, link/unlink |
| Labels | 8 | CRUD, apply to campaigns/ad groups/ads/keywords |
| Shared Sets | 6 | Negative keyword lists, campaign linking |
| Conversions | 6 | Actions, offline imports, goals |
| Targeting | 14 | Device bids, ad schedules, geo, language, demographics, proximity |
| Recommendations | 5 | List, get, apply, dismiss, optimization score |
| Experiments | 5 | A/B testing: create, promote, end |
| Batch | 1 | Multi-resource status changes in one call |
| Diagnostics | 3 | Campaign health check, landing page validation, budget forecast |
| AI Generation | 3 | AI-generated ad text, images, audience definitions |
| GAQL | 1 | Raw SELECT-only query execution |

## Safety

- All newly created resources (campaigns, ad groups, ads) are set to **PAUSED** by default
- Batch limits: max 5000 keywords/assets per call, 2000 conversions
- `execute_gaql` is SELECT-only with keyword blocklist and 10000 char limit
- All user inputs validated against GAQL injection (numeric IDs, enums, dates, statuses)
- Auth with retry and exponential backoff (3 attempts)

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Run linter
uv run ruff check src/ tests/

# Auto-fix lint issues
uv run ruff check src/ tests/ --fix
```

## License

MIT
