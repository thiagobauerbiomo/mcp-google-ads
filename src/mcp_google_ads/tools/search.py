"""Raw GAQL search tool (1 tool)."""

from __future__ import annotations

from typing import Annotated

from ..auth import get_service
from ..coordinator import mcp
from ..utils import error_response, proto_to_dict, resolve_customer_id, success_response


@mcp.tool()
def execute_gaql(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    query: Annotated[str, "GAQL (Google Ads Query Language) query to execute"],
) -> str:
    """Execute a raw GAQL query against the Google Ads API.

    Use this for advanced queries not covered by other tools. See
    https://developers.google.com/google-ads/api/fields/v23/overview for field reference.

    Example: SELECT campaign.id, campaign.name, metrics.clicks FROM campaign WHERE metrics.clicks > 100 DURING LAST_30_DAYS
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        response = service.search(customer_id=cid, query=query)
        rows = []
        for row in response:
            rows.append(proto_to_dict(row))

        return success_response({"rows": rows, "count": len(rows)})
    except Exception as e:
        return error_response(f"GAQL query failed: {e}")
