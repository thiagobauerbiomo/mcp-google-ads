"""Ad Group management tools (7 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from google.api_core import protobuf_helpers

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import (
    error_response,
    format_micros,
    resolve_customer_id,
    success_response,
    to_micros,
    validate_enum_value,
    validate_limit,
    validate_numeric_id,
    validate_status,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def list_ad_groups(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    status_filter: Annotated[str | None, "Filter: ENABLED, PAUSED, REMOVED"] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """List ad groups, optionally filtered by campaign and/or status."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        conditions = []
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")
        if status_filter:
            conditions.append(f"ad_group.status = '{validate_status(status_filter)}'")
        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group.type,
                ad_group.cpc_bid_micros,
                campaign.id,
                campaign.name
            FROM ad_group
            {where}
            ORDER BY ad_group.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        groups = []
        for row in response:
            groups.append({
                "ad_group_id": str(row.ad_group.id),
                "name": row.ad_group.name,
                "status": row.ad_group.status.name,
                "type": row.ad_group.type_.name,
                "cpc_bid_micros": row.ad_group.cpc_bid_micros,
                "cpc_bid": format_micros(row.ad_group.cpc_bid_micros),
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
            })
        return success_response({"ad_groups": groups, "count": len(groups)})
    except Exception as e:
        logger.error("Failed to list ad groups: %s", e, exc_info=True)
        return error_response(f"Failed to list ad groups: {e}")


@mcp.tool()
def get_ad_group(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
) -> str:
    """Get detailed information about a specific ad group."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_ad_group_id = validate_numeric_id(ad_group_id, "ad_group_id")
        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group.type,
                ad_group.cpc_bid_micros,
                ad_group.cpm_bid_micros,
                ad_group.target_cpa_micros,
                ad_group.target_roas,
                ad_group.effective_target_cpa_micros,
                campaign.id,
                campaign.name
            FROM ad_group
            WHERE ad_group.id = {safe_ad_group_id}
        """
        response = service.search(customer_id=cid, query=query)
        for row in response:
            data = {
                "ad_group_id": str(row.ad_group.id),
                "name": row.ad_group.name,
                "status": row.ad_group.status.name,
                "type": row.ad_group.type_.name,
                "cpc_bid_micros": row.ad_group.cpc_bid_micros,
                "cpc_bid": format_micros(row.ad_group.cpc_bid_micros),
                "target_cpa_micros": row.ad_group.target_cpa_micros,
                "target_roas": row.ad_group.target_roas,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
            }
            return success_response(data)
        return error_response(f"Ad group {ad_group_id} not found")
    except Exception as e:
        logger.error("Failed to get ad group: %s", e, exc_info=True)
        return error_response(f"Failed to get ad group: {e}")


@mcp.tool()
def create_ad_group(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID to create the ad group in"],
    name: Annotated[str, "Ad group name"],
    cpc_bid: Annotated[float | None, "CPC bid in account currency (e.g., 10.0 for R$10.00). NOT in micros."] = None,
    ad_group_type: Annotated[str, "Type: SEARCH_STANDARD, DISPLAY_STANDARD, SHOPPING_PRODUCT_ADS"] = "SEARCH_STANDARD",
) -> str:
    """Create a new ad group within a campaign. Created PAUSED by default."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupService")

        operation = client.get_type("AdGroupOperation")
        ad_group = operation.create
        ad_group.name = name
        ad_group.status = client.enums.AdGroupStatusEnum.PAUSED
        ad_group.campaign = f"customers/{cid}/campaigns/{campaign_id}"
        validate_enum_value(ad_group_type, "ad_group_type")
        ad_group.type_ = getattr(client.enums.AdGroupTypeEnum, ad_group_type)

        if cpc_bid is not None:
            if cpc_bid < 0.10:
                return error_response(
                    f"CPC bid R${cpc_bid:.2f} is suspiciously low (< R$0.10). "
                    f"Pass the value in currency, not micros (e.g., 10.0 for R$10.00)."
                )
            ad_group.cpc_bid_micros = to_micros(cpc_bid)

        response = service.mutate_ad_groups(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"ad_group_id": new_id, "resource_name": resource_name, "status": "PAUSED"},
            message=f"Ad group '{name}' created as PAUSED",
        )
    except Exception as e:
        logger.error("Failed to create ad group: %s", e, exc_info=True)
        return error_response(f"Failed to create ad group: {e}")


@mcp.tool()
def update_ad_group(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    name: Annotated[str | None, "New name"] = None,
    cpc_bid: Annotated[float | None, "New CPC bid in account currency"] = None,
    target_cpa_micros: Annotated[int | None, "Target CPA in micros"] = None,
) -> str:
    """Update an ad group's name, bid, or target CPA."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupService")

        operation = client.get_type("AdGroupOperation")
        ad_group = operation.update
        ad_group.resource_name = f"customers/{cid}/adGroups/{ad_group_id}"

        fields = []
        if name is not None:
            ad_group.name = name
            fields.append("name")
        if cpc_bid is not None:
            ad_group.cpc_bid_micros = to_micros(cpc_bid)
            fields.append("cpc_bid_micros")
        if target_cpa_micros is not None:
            ad_group.target_cpa_micros = target_cpa_micros
            fields.append("target_cpa_micros")

        if not fields:
            return error_response("No fields to update")

        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=fields),
        )

        response = service.mutate_ad_groups(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Ad group {ad_group_id} updated",
        )
    except Exception as e:
        logger.error("Failed to update ad group: %s", e, exc_info=True)
        return error_response(f"Failed to update ad group: {e}")


@mcp.tool()
def set_ad_group_status(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    status: Annotated[str, "New status: ENABLED, PAUSED, or REMOVED"],
) -> str:
    """Enable, pause, or remove an ad group."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupService")

        operation = client.get_type("AdGroupOperation")
        ad_group = operation.update
        ad_group.resource_name = f"customers/{cid}/adGroups/{ad_group_id}"
        validate_enum_value(status, "status")
        ad_group.status = getattr(client.enums.AdGroupStatusEnum, status)

        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=["status"]),
        )

        response = service.mutate_ad_groups(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name, "new_status": status},
            message=f"Ad group {ad_group_id} set to {status}",
        )
    except Exception as e:
        logger.error("Failed to set ad group status: %s", e, exc_info=True)
        return error_response(f"Failed to set ad group status: {e}")


@mcp.tool()
def remove_ad_group(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID to remove"],
) -> str:
    """Remove (delete) an ad group permanently."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupService")

        operation = client.get_type("AdGroupOperation")
        operation.remove = f"customers/{cid}/adGroups/{ad_group_id}"

        response = service.mutate_ad_groups(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Ad group {ad_group_id} removed",
        )
    except Exception as e:
        logger.error("Failed to remove ad group: %s", e, exc_info=True)
        return error_response(f"Failed to remove ad group: {e}")


@mcp.tool()
def clone_ad_group(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    source_ad_group_id: Annotated[str, "The ad group ID to clone from"],
    new_name: Annotated[str | None, "Name for the cloned ad group. Defaults to original name + ' [Clone]'"] = None,
    target_campaign_id: Annotated[str | None, "Campaign ID for the clone. Defaults to same campaign as source."] = None,
    copy_keywords: Annotated[bool, "Whether to copy keywords from the source ad group"] = True,
    copy_negative_keywords: Annotated[bool, "Whether to copy negative keywords"] = True,
) -> str:
    """Clone an ad group with its keywords and settings.

    Creates a new PAUSED ad group with the same configuration, keywords, and negative keywords.
    Useful for A/B testing or restructuring campaigns.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_source = validate_numeric_id(source_ad_group_id, "source_ad_group_id")
        client = get_client()
        search_service = get_service("GoogleAdsService")

        # 1. Get source ad group details
        query = f"""
            SELECT
                ad_group.name,
                ad_group.type,
                ad_group.cpc_bid_micros,
                ad_group.target_cpa_micros,
                campaign.id
            FROM ad_group
            WHERE ad_group.id = {safe_source}
        """
        response = search_service.search(customer_id=cid, query=query)
        source = None
        for row in response:
            source = row
        if source is None:
            return error_response(f"Source ad group {source_ad_group_id} not found")

        campaign_id = target_campaign_id or str(source.campaign.id)
        clone_name = new_name or f"{source.ad_group.name} [Clone]"

        # 2. Create the new ad group
        ag_service = get_service("AdGroupService")
        ag_op = client.get_type("AdGroupOperation")
        new_ag = ag_op.create
        new_ag.name = clone_name
        new_ag.status = client.enums.AdGroupStatusEnum.PAUSED
        new_ag.campaign = f"customers/{cid}/campaigns/{campaign_id}"
        new_ag.type_ = source.ad_group.type_
        if source.ad_group.cpc_bid_micros:
            new_ag.cpc_bid_micros = source.ad_group.cpc_bid_micros

        ag_response = ag_service.mutate_ad_groups(customer_id=cid, operations=[ag_op])
        new_ag_resource = ag_response.results[0].resource_name
        new_ag_id = new_ag_resource.split("/")[-1]

        copied_keywords = 0
        copied_negatives = 0

        # 3. Copy keywords
        if copy_keywords:
            kw_query = f"""
                SELECT
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.cpc_bid_micros,
                    ad_group_criterion.negative
                FROM ad_group_criterion
                WHERE ad_group.id = {safe_source}
                    AND ad_group_criterion.type = 'KEYWORD'
                    AND ad_group_criterion.negative = false
                    AND ad_group_criterion.status != 'REMOVED'
                LIMIT 5000
            """
            kw_response = search_service.search(customer_id=cid, query=kw_query)
            kw_service = get_service("AdGroupCriterionService")
            kw_ops = []
            for row in kw_response:
                op = client.get_type("AdGroupCriterionOperation")
                criterion = op.create
                criterion.ad_group = f"customers/{cid}/adGroups/{new_ag_id}"
                criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
                criterion.keyword.text = row.ad_group_criterion.keyword.text
                criterion.keyword.match_type = row.ad_group_criterion.keyword.match_type
                if row.ad_group_criterion.cpc_bid_micros:
                    criterion.cpc_bid_micros = row.ad_group_criterion.cpc_bid_micros
                kw_ops.append(op)

            if kw_ops:
                kw_result = kw_service.mutate_ad_group_criteria(customer_id=cid, operations=kw_ops)
                copied_keywords = len(kw_result.results)

        # 4. Copy negative keywords
        if copy_negative_keywords:
            neg_query = f"""
                SELECT
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type
                FROM ad_group_criterion
                WHERE ad_group.id = {safe_source}
                    AND ad_group_criterion.type = 'KEYWORD'
                    AND ad_group_criterion.negative = true
                    AND ad_group_criterion.status != 'REMOVED'
                LIMIT 5000
            """
            neg_response = search_service.search(customer_id=cid, query=neg_query)
            neg_service = get_service("AdGroupCriterionService")
            neg_ops = []
            for row in neg_response:
                op = client.get_type("AdGroupCriterionOperation")
                criterion = op.create
                criterion.ad_group = f"customers/{cid}/adGroups/{new_ag_id}"
                criterion.negative = True
                criterion.keyword.text = row.ad_group_criterion.keyword.text
                criterion.keyword.match_type = row.ad_group_criterion.keyword.match_type
                neg_ops.append(op)

            if neg_ops:
                neg_result = neg_service.mutate_ad_group_criteria(customer_id=cid, operations=neg_ops)
                copied_negatives = len(neg_result.results)

        return success_response(
            {
                "new_ad_group_id": new_ag_id,
                "resource_name": new_ag_resource,
                "status": "PAUSED",
                "copied_keywords": copied_keywords,
                "copied_negatives": copied_negatives,
            },
            message=f"Ad group cloned as '{clone_name}' (PAUSED) with {copied_keywords} keywords and {copied_negatives} negatives",
        )
    except Exception as e:
        logger.error("Failed to clone ad group: %s", e, exc_info=True)
        return error_response(f"Failed to clone ad group: {e}")
