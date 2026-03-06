"""Remarketing tag and action management tools (5 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response, validate_limit, validate_numeric_id

logger = logging.getLogger(__name__)


@mcp.tool()
def list_remarketing_actions(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """List all remarketing actions for the account.

    Remarketing actions are tag configurations that collect visitor data
    for building remarketing audiences.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                remarketing_action.resource_name,
                remarketing_action.id,
                remarketing_action.name,
                remarketing_action.tag_snippets
            FROM remarketing_action
            ORDER BY remarketing_action.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        actions = []
        for row in response:
            snippets = []
            for snippet in row.remarketing_action.tag_snippets:
                snippets.append({
                    "type": snippet.type_.name if hasattr(snippet.type_, "name") else str(snippet.type_),
                    "page_tag": snippet.global_site_tag if hasattr(snippet, "global_site_tag") else "",
                    "event_snippet": snippet.event_snippet if hasattr(snippet, "event_snippet") else "",
                })
            actions.append({
                "resource_name": row.remarketing_action.resource_name,
                "id": str(row.remarketing_action.id),
                "name": row.remarketing_action.name,
                "tag_snippets": snippets,
            })
        return success_response({"remarketing_actions": actions, "count": len(actions)})
    except Exception as e:
        logger.error("Failed to list remarketing actions: %s", e, exc_info=True)
        return error_response(f"Failed to list remarketing actions: {e}")


@mcp.tool()
def get_remarketing_action(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    remarketing_action_id: Annotated[str, "The remarketing action ID"],
) -> str:
    """Get detailed info about a remarketing action including its tag snippets."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_id = validate_numeric_id(remarketing_action_id, "remarketing_action_id")
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                remarketing_action.resource_name,
                remarketing_action.id,
                remarketing_action.name,
                remarketing_action.tag_snippets
            FROM remarketing_action
            WHERE remarketing_action.resource_name = 'customers/{cid}/remarketingActions/{safe_id}'
        """
        response = service.search(customer_id=cid, query=query)
        action_data = None
        for row in response:
            snippets = []
            for snippet in row.remarketing_action.tag_snippets:
                snippets.append({
                    "type": snippet.type_.name if hasattr(snippet.type_, "name") else str(snippet.type_),
                    "page_tag": snippet.global_site_tag if hasattr(snippet, "global_site_tag") else "",
                    "event_snippet": snippet.event_snippet if hasattr(snippet, "event_snippet") else "",
                })
            action_data = {
                "resource_name": row.remarketing_action.resource_name,
                "id": str(row.remarketing_action.id),
                "name": row.remarketing_action.name,
                "tag_snippets": snippets,
            }

        if not action_data:
            return error_response(f"Remarketing action {remarketing_action_id} not found")

        return success_response(action_data)
    except Exception as e:
        logger.error("Failed to get remarketing action: %s", e, exc_info=True)
        return error_response(f"Failed to get remarketing action: {e}")


@mcp.tool()
def create_remarketing_action(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Name for the remarketing action"],
) -> str:
    """Create a new remarketing action.

    This creates a remarketing tag that can be installed on your website
    to collect visitor data for remarketing audiences.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("RemarketingActionService")

        operation = client.get_type("RemarketingActionOperation")
        action = operation.create
        action.name = name

        response = service.mutate_remarketing_actions(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        action_id = resource_name.split("/")[-1]

        return success_response(
            {"remarketing_action_id": action_id, "resource_name": resource_name},
            message=f"Remarketing action '{name}' created",
        )
    except Exception as e:
        logger.error("Failed to create remarketing action: %s", e, exc_info=True)
        return error_response(f"Failed to create remarketing action: {e}")


@mcp.tool()
def remove_remarketing_action(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    remarketing_action_id: Annotated[str, "The remarketing action ID to remove"],
) -> str:
    """Remove a remarketing action.

    WARNING: This will stop collecting data for any remarketing lists using this action.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_id = validate_numeric_id(remarketing_action_id, "remarketing_action_id")
        client = get_client()
        service = get_service("RemarketingActionService")

        operation = client.get_type("RemarketingActionOperation")
        operation.remove = f"customers/{cid}/remarketingActions/{safe_id}"

        service.mutate_remarketing_actions(customer_id=cid, operations=[operation])

        return success_response(
            {"remarketing_action_id": remarketing_action_id, "action": "removed"},
            message=f"Remarketing action {remarketing_action_id} removed",
        )
    except Exception as e:
        logger.error("Failed to remove remarketing action: %s", e, exc_info=True)
        return error_response(f"Failed to remove remarketing action: {e}")


@mcp.tool()
def list_combined_audiences(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """List combined audiences (custom combinations of remarketing lists and other audiences).

    Combined audiences allow targeting users who belong to multiple audience segments.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                combined_audience.resource_name,
                combined_audience.id,
                combined_audience.name,
                combined_audience.description,
                combined_audience.status
            FROM combined_audience
            ORDER BY combined_audience.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        audiences = []
        for row in response:
            audiences.append({
                "resource_name": row.combined_audience.resource_name,
                "id": str(row.combined_audience.id),
                "name": row.combined_audience.name,
                "description": row.combined_audience.description,
                "status": row.combined_audience.status.name,
            })
        return success_response({"combined_audiences": audiences, "count": len(audiences)})
    except Exception as e:
        logger.error("Failed to list combined audiences: %s", e, exc_info=True)
        return error_response(f"Failed to list combined audiences: {e}")
