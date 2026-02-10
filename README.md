# MCP Google Ads Server

MCP Server for Google Ads API v23 with full CRUD operations. Built by [Biomo](https://biomo.com.br).

## Features

- **61 tools** across 11 categories: Accounts, Campaigns, Ad Groups, Ads, Keywords, Budgets, Bidding, Reporting, Audiences, Extensions, and raw GAQL
- OAuth2 authentication with MCC (Manager) support
- Safety-first: all resources created PAUSED by default
- Consistent JSON responses with error handling

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

## Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| Accounts | 4 | List customers, get info, hierarchy, client list |
| Campaigns | 7 | CRUD, status management, labels |
| Ad Groups | 6 | CRUD, status management |
| Ads | 6 | List, create RSA, update, status, ad strength |
| Keywords | 8 | CRUD, negatives, ideas, forecasts |
| Budgets | 4 | CRUD for campaign budgets |
| Bidding | 5 | Portfolio strategies, campaign assignment |
| Reporting | 8 | Performance reports, search terms, geo, change history |
| Audiences | 6 | Segments, targeting, geo suggestions |
| Extensions | 6 | Sitelinks, callouts, snippets, calls |
| GAQL | 1 | Raw query execution |

## License

MIT
