"""Entry point for the Google Ads MCP Server."""

from __future__ import annotations

import logging
import os
import sys

from . import __version__
from .coordinator import mcp

# Import all tool modules so they register with the coordinator
from .tools import (  # noqa: F401
    account_budget,
    account_management,
    accounts,
    ad_customizers,
    ad_groups,
    ads,
    ai_generation,
    audiences,
    batch,
    bidding,
    budgets,
    campaign_criteria,
    campaign_drafts,
    campaign_types,
    campaigns,
    conversions,
    dashboard,
    diagnostics,
    experiments,
    extensions,
    incentives,
    keywords,
    labels,
    recommendations,
    remarketing,
    reporting,
    search,
    shared_sets,
    simulations,
    smart_campaigns,
    targeting,
    user_lists,
    youtube_uploads,
)


def main() -> None:
    """Run the MCP server."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Google Ads MCP Server v%s", __version__)
    mcp.run()


if __name__ == "__main__":
    main()
