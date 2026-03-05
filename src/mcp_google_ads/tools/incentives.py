"""Incentive tools (2 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_client
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response

logger = logging.getLogger(__name__)


@mcp.tool()
def fetch_incentive(
    language_code: Annotated[str, "Language code (e.g. 'pt', 'en')"] = "pt",
    country_code: Annotated[str, "Country code (e.g. 'BR', 'US')"] = "BR",
) -> str:
    """Fetch available promotional incentive programs for Google Ads accounts.

    Returns incentive offers (e.g. 'Spend $X, get $Y credit') available for the region.
    """
    try:
        client = get_client()
        service = client.get_service("IncentiveService")

        request = client.get_type("FetchIncentiveRequest")
        request.language_code = language_code
        request.country_code = country_code

        response = service.fetch_incentive(request=request)

        incentives = []
        for incentive in response.incentives:
            incentives.append({
                "incentive_id": incentive.incentive_id,
                "name": incentive.name if hasattr(incentive, "name") else "",
                "description": incentive.description if hasattr(incentive, "description") else "",
            })

        return success_response({"incentives": incentives, "count": len(incentives)})
    except Exception as e:
        logger.error("Failed to fetch incentives: %s", e, exc_info=True)
        return error_response(f"Failed to fetch incentives: {e}")


@mcp.tool()
def apply_incentive(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    incentive_id: Annotated[str, "The incentive ID to apply"],
) -> str:
    """Apply a promotional incentive (coupon/credit) to a Google Ads account."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = client.get_service("IncentiveService")

        request = client.get_type("ApplyIncentiveRequest")
        request.customer_id = cid
        request.incentive_id = incentive_id

        service.apply_incentive(request=request)

        return success_response(
            {"customer_id": cid, "incentive_id": incentive_id},
            message=f"Incentive {incentive_id} applied to account {cid}",
        )
    except Exception as e:
        logger.error("Failed to apply incentive: %s", e, exc_info=True)
        return error_response(f"Failed to apply incentive: {e}")
