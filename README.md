# MCP Google Ads Server

MCP Server for Google Ads API v23 with full CRUD operations — **123 tools** across 20 categories. Built by [Biomo](https://biomo.com.br).

## Features

- **123 tools** for complete Google Ads management
- OAuth2 authentication with MCC (Manager) support
- Safety-first: all resources created PAUSED by default
- GAQL injection protection on all inputs
- Structured logging in all modules
- Consistent JSON responses with error handling
- 430 tests, 82% coverage

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

## Tool Categories (123 tools)

| Category | Tools | Description |
|----------|-------|-------------|
| Accounts | 4 | List customers, get info, hierarchy, client list |
| Account Management | 3 | Account links, billing, users |
| Campaigns | 7 | CRUD, status management, labels |
| Campaign Types | 8 | PMax, Display, Video, Shopping, Demand Gen, App campaigns |
| Ad Groups | 6 | CRUD, status management |
| Ads | 6 | List, create RSA, update, status, ad strength |
| Keywords | 9 | CRUD, negatives, ideas, forecasts |
| Budgets | 4 | CRUD for campaign budgets |
| Bidding | 5 | Portfolio strategies, campaign assignment |
| Reporting | 14 | Performance reports across all dimensions |
| Dashboard | 2 | MCC summary, account dashboard |
| Audiences | 6 | Segments, targeting, geo suggestions |
| Extensions | 14 | Assets: sitelinks, callouts, snippets, call, image, video, lead form, price, promotion |
| Labels | 8 | CRUD, apply to campaigns/ad groups/ads/keywords |
| Shared Sets | 6 | Negative keyword lists, campaign linking |
| Conversions | 6 | Actions, offline imports, goals |
| Targeting | 7 | Device bids, ad schedules, geo, language |
| Recommendations | 5 | List, get, apply, dismiss, optimization score |
| Experiments | 5 | A/B testing: create, promote, end |
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
