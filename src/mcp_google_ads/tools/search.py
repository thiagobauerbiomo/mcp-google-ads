"""Raw GAQL search tool (1 tool)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_service
from ..coordinator import mcp
from ..utils import error_response, proto_to_dict, resolve_customer_id, success_response

logger = logging.getLogger(__name__)

_MAX_QUERY_LENGTH = 10000


@mcp.tool()
def execute_gaql(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    query: Annotated[str, "GAQL (Google Ads Query Language) query to execute"],
) -> str:
    """Execute a raw GAQL query against the Google Ads API.

    For advanced queries not covered by other tools. READ-ONLY (SELECT only).
    See https://developers.google.com/google-ads/api/fields/v23/overview for field reference.

    Example: SELECT campaign.id, campaign.name, metrics.clicks FROM campaign WHERE metrics.clicks > 100 DURING LAST_30_DAYS
    """
    try:
        if len(query) > _MAX_QUERY_LENGTH:
            return error_response(f"Query too long ({len(query)} chars). Max: {_MAX_QUERY_LENGTH}")

        stripped = query.strip().upper()
        if not stripped.startswith("SELECT"):
            return error_response("Only SELECT queries are allowed in execute_gaql")

        for keyword in ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "MUTATE"):
            if keyword in stripped.split():
                return error_response(f"Keyword '{keyword}' not allowed in execute_gaql (read-only)")

        cid = resolve_customer_id(customer_id)
        logger.info("execute_gaql [customer=%s]: %s", cid, query[:200])

        service = get_service("GoogleAdsService")
        response = service.search(customer_id=cid, query=query)
        rows = []
        for row in response:
            rows.append(proto_to_dict(row))

        return success_response({"rows": rows, "count": len(rows)})
    except Exception as e:
        logger.error("GAQL query failed: %s", e, exc_info=True)
        return error_response(f"GAQL query failed: {e}")
