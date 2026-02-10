"""Entry point for the Google Ads MCP Server."""

from __future__ import annotations

import logging
import sys

from . import __version__
from .coordinator import mcp

# Import all tool modules so they register with the coordinator
from .tools import (  # noqa: F401
    account_management,
    accounts,
    ad_groups,
    ads,
    audiences,
    bidding,
    budgets,
    campaign_types,
    campaigns,
    conversions,
    dashboard,
    experiments,
    extensions,
    keywords,
    labels,
    recommendations,
    reporting,
    search,
    shared_sets,
    targeting,
)


def main() -> None:
    """Run the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Google Ads MCP Server v%s", __version__)
    mcp.run()


if __name__ == "__main__":
    main()
