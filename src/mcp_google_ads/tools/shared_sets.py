"""Shared set management tools (6 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import (
    error_response,
    resolve_customer_id,
    success_response,
    validate_enum_value,
    validate_limit,
    validate_numeric_id,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def list_shared_sets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    set_type: Annotated[str | None, "Filter by type: NEGATIVE_KEYWORDS, NEGATIVE_PLACEMENTS"] = None,
    limit: Annotated[int, "Maximum number of results"] = 100,
) -> str:
    """List all shared sets (negative keyword lists, placement exclusion lists).

    Shared sets allow you to create reusable lists that can be applied across campaigns.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        type_filter = f"WHERE shared_set.type = '{validate_enum_value(set_type, 'set_type')}'" if set_type else ""

        query = f"""
            SELECT
                shared_set.id,
                shared_set.name,
                shared_set.type,
                shared_set.status,
                shared_set.member_count
            FROM shared_set
            {type_filter}
            ORDER BY shared_set.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        shared_sets = []
        for row in response:
            shared_sets.append({
                "shared_set_id": str(row.shared_set.id),
                "name": row.shared_set.name,
                "type": row.shared_set.type_.name,
                "status": row.shared_set.status.name,
                "member_count": row.shared_set.member_count,
            })
        return success_response({"shared_sets": shared_sets, "count": len(shared_sets)})
    except Exception as e:
        logger.error("Failed to list shared sets: %s", e, exc_info=True)
        return error_response(f"Failed to list shared sets: {e}")


@mcp.tool()
def create_shared_set(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Name for the shared set"],
    set_type: Annotated[str, "Type: NEGATIVE_KEYWORDS or NEGATIVE_PLACEMENTS"] = "NEGATIVE_KEYWORDS",
) -> str:
    """Create a new shared set (negative keyword list or placement exclusion list)."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("GoogleAdsService")

        mutate_op = client.get_type("MutateOperation")
        shared_set = mutate_op.shared_set_operation.create
        shared_set.name = name
        validate_enum_value(set_type, "set_type")
        shared_set.type_ = getattr(client.enums.SharedSetTypeEnum, set_type)

        response = service.mutate(customer_id=cid, mutate_operations=[mutate_op])
        result = response.mutate_operation_responses[0].shared_set_result
        resource_name = result.resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"shared_set_id": new_id, "resource_name": resource_name},
            message=f"Shared set '{name}' created",
        )
    except Exception as e:
        logger.error("Failed to create shared set: %s", e, exc_info=True)
        return error_response(f"Failed to create shared set: {e}")


@mcp.tool()
def remove_shared_set(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    shared_set_id: Annotated[str, "The shared set ID to remove"],
) -> str:
    """Remove a shared set permanently. This also removes all associations with campaigns."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("GoogleAdsService")

        mutate_op = client.get_type("MutateOperation")
        mutate_op.shared_set_operation.remove = f"customers/{cid}/sharedSets/{shared_set_id}"

        response = service.mutate(customer_id=cid, mutate_operations=[mutate_op])
        result = response.mutate_operation_responses[0].shared_set_result
        return success_response(
            {"resource_name": result.resource_name},
            message=f"Shared set {shared_set_id} removed",
        )
    except Exception as e:
        logger.error("Failed to remove shared set: %s", e, exc_info=True)
        return error_response(f"Failed to remove shared set: {e}")


@mcp.tool()
def list_shared_set_members(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    shared_set_id: Annotated[str, "The shared set ID"],
    limit: Annotated[int, "Maximum number of results"] = 200,
) -> str:
    """List all members (keywords/placements) in a shared set."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                shared_criterion.shared_set,
                shared_criterion.type,
                shared_criterion.keyword.text,
                shared_criterion.keyword.match_type,
                shared_criterion.criterion_id
            FROM shared_criterion
            WHERE shared_set.id = {validate_numeric_id(shared_set_id, "shared_set_id")}
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        members = []
        for row in response:
            member = {
                "criterion_id": str(row.shared_criterion.criterion_id),
                "type": row.shared_criterion.type_.name,
            }
            if row.shared_criterion.type_.name == "KEYWORD":
                member["keyword"] = row.shared_criterion.keyword.text
                member["match_type"] = row.shared_criterion.keyword.match_type.name
            members.append(member)

        return success_response({"members": members, "count": len(members)})
    except Exception as e:
        logger.error("Failed to list shared set members: %s", e, exc_info=True)
        return error_response(f"Failed to list shared set members: {e}")


@mcp.tool()
def link_shared_set_to_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    shared_set_id: Annotated[str, "The shared set ID to link"],
) -> str:
    """Link a shared set to a campaign. The shared set's criteria will apply to the campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("GoogleAdsService")

        mutate_op = client.get_type("MutateOperation")
        css = mutate_op.campaign_shared_set_operation.create
        css.campaign = f"customers/{cid}/campaigns/{campaign_id}"
        css.shared_set = f"customers/{cid}/sharedSets/{shared_set_id}"

        response = service.mutate(customer_id=cid, mutate_operations=[mutate_op])
        result = response.mutate_operation_responses[0].campaign_shared_set_result
        return success_response(
            {"resource_name": result.resource_name},
            message=f"Shared set {shared_set_id} linked to campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to link shared set to campaign: %s", e, exc_info=True)
        return error_response(f"Failed to link shared set to campaign: {e}")


@mcp.tool()
def unlink_shared_set_from_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    shared_set_id: Annotated[str, "The shared set ID to unlink"],
) -> str:
    """Unlink a shared set from a campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("GoogleAdsService")

        mutate_op = client.get_type("MutateOperation")
        mutate_op.campaign_shared_set_operation.remove = (
            f"customers/{cid}/campaignSharedSets/{campaign_id}~{shared_set_id}"
        )

        response = service.mutate(customer_id=cid, mutate_operations=[mutate_op])
        result = response.mutate_operation_responses[0].campaign_shared_set_result
        return success_response(
            {"resource_name": result.resource_name},
            message=f"Shared set {shared_set_id} unlinked from campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to unlink shared set from campaign: %s", e, exc_info=True)
        return error_response(f"Failed to unlink shared set from campaign: {e}")
