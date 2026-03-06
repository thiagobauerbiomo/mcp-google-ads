"""Campaign draft management tools (5 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response, validate_limit, validate_numeric_id

logger = logging.getLogger(__name__)


@mcp.tool()
def list_campaign_drafts(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by base campaign ID"] = None,
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """List campaign drafts.

    Drafts are copies of campaigns where changes can be tested before applying.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)

        where_clause = ""
        if campaign_id:
            safe_cid = validate_numeric_id(campaign_id, "campaign_id")
            where_clause = f"WHERE campaign_draft.base_campaign = 'customers/{cid}/campaigns/{safe_cid}'"

        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                campaign_draft.resource_name,
                campaign_draft.draft_id,
                campaign_draft.base_campaign,
                campaign_draft.name,
                campaign_draft.draft_campaign,
                campaign_draft.status,
                campaign_draft.has_experiment_running
            FROM campaign_draft
            {where_clause}
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        drafts = []
        for row in response:
            drafts.append({
                "resource_name": row.campaign_draft.resource_name,
                "draft_id": row.campaign_draft.draft_id,
                "base_campaign": row.campaign_draft.base_campaign,
                "name": row.campaign_draft.name,
                "draft_campaign": row.campaign_draft.draft_campaign,
                "status": row.campaign_draft.status.name,
                "has_experiment_running": row.campaign_draft.has_experiment_running,
            })
        return success_response({"drafts": drafts, "count": len(drafts)})
    except Exception as e:
        logger.error("Failed to list campaign drafts: %s", e, exc_info=True)
        return error_response(f"Failed to list campaign drafts: {e}")


@mcp.tool()
def get_campaign_draft(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    draft_id: Annotated[str, "The draft ID"],
    base_campaign_id: Annotated[str, "The base campaign ID"],
) -> str:
    """Get detailed information about a specific campaign draft."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_draft_id = validate_numeric_id(draft_id, "draft_id")
        safe_base_campaign_id = validate_numeric_id(base_campaign_id, "base_campaign_id")
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign_draft.resource_name,
                campaign_draft.draft_id,
                campaign_draft.base_campaign,
                campaign_draft.name,
                campaign_draft.draft_campaign,
                campaign_draft.status,
                campaign_draft.has_experiment_running
            FROM campaign_draft
            WHERE campaign_draft.resource_name = 'customers/{cid}/campaignDrafts/{safe_base_campaign_id}~{safe_draft_id}'
        """
        response = service.search(customer_id=cid, query=query)
        draft_data = None
        for row in response:
            draft_data = {
                "resource_name": row.campaign_draft.resource_name,
                "draft_id": row.campaign_draft.draft_id,
                "base_campaign": row.campaign_draft.base_campaign,
                "name": row.campaign_draft.name,
                "draft_campaign": row.campaign_draft.draft_campaign,
                "status": row.campaign_draft.status.name,
                "has_experiment_running": row.campaign_draft.has_experiment_running,
            }

        if not draft_data:
            return error_response(f"Campaign draft {draft_id} not found")

        return success_response(draft_data)
    except Exception as e:
        logger.error("Failed to get campaign draft: %s", e, exc_info=True)
        return error_response(f"Failed to get campaign draft: {e}")


@mcp.tool()
def create_campaign_draft(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    base_campaign_id: Annotated[str, "The base campaign ID to create a draft from"],
    name: Annotated[str, "Name for the draft"],
) -> str:
    """Create a campaign draft from an existing campaign.

    The draft is a copy of the base campaign where you can make changes
    without affecting the live campaign. Changes can later be promoted or discarded.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_base_id = validate_numeric_id(base_campaign_id, "base_campaign_id")
        client = get_client()
        draft_service = get_service("CampaignDraftService")

        operation = client.get_type("CampaignDraftOperation")
        draft = operation.create
        draft.base_campaign = f"customers/{cid}/campaigns/{safe_base_id}"
        draft.name = name

        response = draft_service.mutate_campaign_drafts(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name

        return success_response(
            {
                "resource_name": resource_name,
                "base_campaign_id": base_campaign_id,
                "name": name,
            },
            message=f"Campaign draft '{name}' created successfully",
        )
    except Exception as e:
        logger.error("Failed to create campaign draft: %s", e, exc_info=True)
        return error_response(f"Failed to create campaign draft: {e}")


@mcp.tool()
def promote_campaign_draft(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    draft_id: Annotated[str, "The draft ID to promote"],
    base_campaign_id: Annotated[str, "The base campaign ID"],
) -> str:
    """Promote a campaign draft — apply all draft changes to the base campaign.

    WARNING: This permanently applies all draft changes to the live campaign.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_draft_id = validate_numeric_id(draft_id, "draft_id")
        safe_base_id = validate_numeric_id(base_campaign_id, "base_campaign_id")
        draft_service = get_service("CampaignDraftService")

        campaign_draft = f"customers/{cid}/campaignDrafts/{safe_base_id}~{safe_draft_id}"
        draft_service.promote_campaign_draft(campaign_draft=campaign_draft)

        return success_response(
            {"draft_id": draft_id, "base_campaign_id": base_campaign_id, "action": "promoted"},
            message=f"Campaign draft {draft_id} promoted — changes applied to base campaign {base_campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to promote campaign draft: %s", e, exc_info=True)
        return error_response(f"Failed to promote campaign draft: {e}")


@mcp.tool()
def remove_campaign_draft(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    draft_id: Annotated[str, "The draft ID to remove"],
    base_campaign_id: Annotated[str, "The base campaign ID"],
) -> str:
    """Remove a campaign draft without applying changes.

    WARNING: This permanently deletes the draft and all its changes.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_draft_id = validate_numeric_id(draft_id, "draft_id")
        safe_base_id = validate_numeric_id(base_campaign_id, "base_campaign_id")
        client = get_client()
        draft_service = get_service("CampaignDraftService")

        operation = client.get_type("CampaignDraftOperation")
        operation.remove = f"customers/{cid}/campaignDrafts/{safe_base_id}~{safe_draft_id}"

        draft_service.mutate_campaign_drafts(customer_id=cid, operations=[operation])

        return success_response(
            {"draft_id": draft_id, "base_campaign_id": base_campaign_id, "action": "removed"},
            message=f"Campaign draft {draft_id} removed successfully",
        )
    except Exception as e:
        logger.error("Failed to remove campaign draft: %s", e, exc_info=True)
        return error_response(f"Failed to remove campaign draft: {e}")
