"""Campaign-level criteria management tools (5 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import (
    error_response,
    resolve_customer_id,
    success_response,
    validate_batch,
    validate_enum_value,
    validate_limit,
    validate_numeric_id,
)

logger = logging.getLogger(__name__)

_VALID_CRITERION_TYPES = {
    "KEYWORD", "PLACEMENT", "LOCATION", "LANGUAGE", "DEVICE",
    "AGE_RANGE", "GENDER", "INCOME_RANGE", "IP_BLOCK", "CONTENT_LABEL",
    "PROXIMITY", "USER_LIST", "WEBPAGE", "TOPIC", "CUSTOM_AFFINITY", "CUSTOM_INTENT",
}

_VALID_ADD_CRITERION_TYPES = {"IP_BLOCK", "PLACEMENT", "TOPIC", "CONTENT_LABEL", "USER_LIST", "WEBPAGE"}


def _parse_criterion(row) -> dict:
    """Parse a campaign_criterion row into a dict based on its type."""
    cc = row.campaign_criterion
    ctype = cc.type_.name if hasattr(cc.type_, "name") else str(cc.type_)

    result = {
        "resource_name": cc.resource_name,
        "criterion_id": str(cc.criterion_id),
        "type": ctype,
        "negative": cc.negative,
        "bid_modifier": cc.bid_modifier,
        "status": cc.status.name if hasattr(cc.status, "name") else str(cc.status),
    }

    if ctype == "KEYWORD":
        result["keyword_text"] = cc.keyword.text
        result["match_type"] = cc.keyword.match_type.name if hasattr(cc.keyword.match_type, "name") else str(cc.keyword.match_type)
    elif ctype == "LOCATION":
        result["geo_target_constant"] = cc.location.geo_target_constant
    elif ctype == "LANGUAGE":
        result["language_constant"] = cc.language.language_constant
    elif ctype == "DEVICE":
        result["device_type"] = cc.device.type_.name if hasattr(cc.device.type_, "name") else str(cc.device.type_)
    elif ctype == "AGE_RANGE":
        result["age_range_type"] = cc.age_range.type_.name if hasattr(cc.age_range.type_, "name") else str(cc.age_range.type_)
    elif ctype == "GENDER":
        result["gender_type"] = cc.gender.type_.name if hasattr(cc.gender.type_, "name") else str(cc.gender.type_)
    elif ctype == "INCOME_RANGE":
        result["income_range_type"] = cc.income_range.type_.name if hasattr(cc.income_range.type_, "name") else str(cc.income_range.type_)
    elif ctype == "USER_LIST":
        result["user_list"] = cc.user_list.user_list
    elif ctype == "PROXIMITY":
        result["longitude_micro_degrees"] = cc.proximity.geo_point.longitude_in_micro_degrees
        result["latitude_micro_degrees"] = cc.proximity.geo_point.latitude_in_micro_degrees
        result["radius"] = cc.proximity.radius
        result["radius_units"] = cc.proximity.radius_units.name if hasattr(cc.proximity.radius_units, "name") else str(cc.proximity.radius_units)
    elif ctype == "IP_BLOCK":
        result["ip_address"] = cc.ip_block.ip_address
    elif ctype == "PLACEMENT":
        result["url"] = cc.placement.url
    elif ctype == "TOPIC":
        result["topic_constant"] = cc.topic.topic_constant
    elif ctype == "WEBPAGE":
        conditions = []
        for cond in cc.webpage.conditions:
            conditions.append({
                "operand": cond.operand.name if hasattr(cond.operand, "name") else str(cond.operand),
                "argument": cond.argument,
            })
        result["webpage_conditions"] = conditions

    return result


@mcp.tool()
def list_campaign_criteria(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    criterion_type: Annotated[str | None, "Filter by type: KEYWORD, PLACEMENT, LOCATION, LANGUAGE, DEVICE, AGE_RANGE, GENDER, INCOME_RANGE, IP_BLOCK, CONTENT_LABEL, PROXIMITY, USER_LIST, WEBPAGE, TOPIC, CUSTOM_AFFINITY, CUSTOM_INTENT"] = None,
    limit: Annotated[int, "Maximum number of results"] = 200,
) -> str:
    """List all targeting criteria for a campaign.

    Returns both positive (targeting) and negative (exclusion) criteria.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_campaign_id = validate_numeric_id(campaign_id, "campaign_id")
        safe_limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        type_filter = ""
        if criterion_type is not None:
            safe_type = validate_enum_value(criterion_type, "criterion_type")
            if safe_type not in _VALID_CRITERION_TYPES:
                return error_response(f"Invalid criterion_type: {criterion_type}. Use: {sorted(_VALID_CRITERION_TYPES)}")
            type_filter = f"\n                AND campaign_criterion.type = '{safe_type}'"

        query = f"""
            SELECT
                campaign_criterion.resource_name,
                campaign_criterion.criterion_id,
                campaign_criterion.type,
                campaign_criterion.negative,
                campaign_criterion.bid_modifier,
                campaign_criterion.status,
                campaign_criterion.keyword.text,
                campaign_criterion.keyword.match_type,
                campaign_criterion.location.geo_target_constant,
                campaign_criterion.language.language_constant,
                campaign_criterion.device.type,
                campaign_criterion.age_range.type,
                campaign_criterion.gender.type,
                campaign_criterion.income_range.type,
                campaign_criterion.user_list.user_list,
                campaign_criterion.proximity.geo_point.longitude_in_micro_degrees,
                campaign_criterion.proximity.geo_point.latitude_in_micro_degrees,
                campaign_criterion.proximity.radius,
                campaign_criterion.proximity.radius_units,
                campaign_criterion.ip_block.ip_address,
                campaign_criterion.placement.url,
                campaign_criterion.topic.topic_constant,
                campaign_criterion.webpage.conditions
            FROM campaign_criterion
            WHERE campaign_criterion.campaign = 'customers/{cid}/campaigns/{safe_campaign_id}'{type_filter}
            LIMIT {safe_limit}
        """

        response = service.search(customer_id=cid, query=query)

        criteria = []
        for row in response:
            criteria.append(_parse_criterion(row))

        return success_response({"criteria": criteria, "count": len(criteria)})
    except Exception as e:
        logger.error("Failed to list campaign criteria: %s", e, exc_info=True)
        return error_response(f"Failed to list campaign criteria: {e}")


@mcp.tool()
def add_campaign_criterion(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    criterion_type: Annotated[str, "Type: IP_BLOCK, PLACEMENT, TOPIC, CONTENT_LABEL, USER_LIST, WEBPAGE"],
    value: Annotated[str, "The criterion value (IP address, URL, topic ID, user list ID, etc.)"],
    negative: Annotated[bool, "Whether this is a negative/exclusion criterion"] = False,
    bid_modifier: Annotated[float | None, "Bid modifier (1.0 = no change, 1.2 = +20%, 0.8 = -20%)"] = None,
) -> str:
    """Add a targeting or exclusion criterion to a campaign.

    Supports IP blocks, placement exclusions, topic targeting, content label exclusions,
    user list targeting, and webpage criteria.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_campaign_id = validate_numeric_id(campaign_id, "campaign_id")
        safe_ctype = validate_enum_value(criterion_type, "criterion_type")

        if safe_ctype not in _VALID_ADD_CRITERION_TYPES:
            return error_response(
                f"Unsupported criterion_type: {criterion_type}. Use: {sorted(_VALID_ADD_CRITERION_TYPES)}"
            )

        client = get_client()
        service = get_service("CampaignCriterionService")

        operation = client.get_type("CampaignCriterionOperation")
        criterion = operation.create
        criterion.campaign = f"customers/{cid}/campaigns/{safe_campaign_id}"
        criterion.negative = negative

        if bid_modifier is not None:
            criterion.bid_modifier = bid_modifier

        if safe_ctype == "IP_BLOCK":
            criterion.ip_block.ip_address = value
        elif safe_ctype == "PLACEMENT":
            criterion.placement.url = value
        elif safe_ctype == "TOPIC":
            safe_val = validate_numeric_id(value, "topic_id")
            criterion.topic.topic_constant = f"topicConstants/{safe_val}"
        elif safe_ctype == "CONTENT_LABEL":
            safe_val = validate_enum_value(value, "content_label_type")
            criterion.content_label.type_ = getattr(client.enums.ContentLabelTypeEnum, safe_val)
        elif safe_ctype == "USER_LIST":
            safe_val = validate_numeric_id(value, "user_list_id")
            criterion.user_list.user_list = f"customers/{cid}/userLists/{safe_val}"
        elif safe_ctype == "WEBPAGE":
            condition = client.get_type("WebpageConditionInfo")
            condition.operand = client.enums.WebpageConditionOperandEnum.URL
            condition.argument = value
            criterion.webpage.conditions.append(condition)

        response = service.mutate_campaign_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Campaign criterion ({safe_ctype}) added to campaign {campaign_id} (negative={negative})",
        )
    except Exception as e:
        logger.error("Failed to add campaign criterion: %s", e, exc_info=True)
        return error_response(f"Failed to add campaign criterion: {e}")


@mcp.tool()
def remove_campaign_criterion(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    criterion_id: Annotated[str, "The criterion ID to remove"],
) -> str:
    """Remove a specific criterion from a campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_campaign_id = validate_numeric_id(campaign_id, "campaign_id")
        safe_criterion_id = validate_numeric_id(criterion_id, "criterion_id")

        client = get_client()
        service = get_service("CampaignCriterionService")

        operation = client.get_type("CampaignCriterionOperation")
        operation.remove = f"customers/{cid}/campaignCriteria/{safe_campaign_id}~{safe_criterion_id}"

        service.mutate_campaign_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"campaign_id": campaign_id, "criterion_id": criterion_id},
            message=f"Criterion {criterion_id} removed from campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to remove campaign criterion: %s", e, exc_info=True)
        return error_response(f"Failed to remove campaign criterion: {e}")


@mcp.tool()
def exclude_ip_addresses(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    ip_addresses: Annotated[list[str], "List of IP addresses to block (max 500)"],
) -> str:
    """Exclude multiple IP addresses from a campaign.

    Useful for blocking click fraud or internal traffic.
    Maximum 500 IPs per campaign (Google Ads limit).
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_campaign_id = validate_numeric_id(campaign_id, "campaign_id")

        batch_error = validate_batch(ip_addresses, max_size=500, item_name="IP addresses")
        if batch_error:
            return error_response(batch_error)

        if not ip_addresses:
            return error_response("ip_addresses list cannot be empty")

        client = get_client()
        service = get_service("CampaignCriterionService")

        operations = []
        for ip_addr in ip_addresses:
            operation = client.get_type("CampaignCriterionOperation")
            criterion = operation.create
            criterion.campaign = f"customers/{cid}/campaigns/{safe_campaign_id}"
            criterion.negative = True
            criterion.ip_block.ip_address = ip_addr
            operations.append(operation)

        response = service.mutate_campaign_criteria(customer_id=cid, operations=operations)
        created = [r.resource_name for r in response.results]
        return success_response(
            {"excluded_ips": len(created), "resource_names": created},
            message=f"{len(created)} IP address(es) excluded from campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to exclude IP addresses: %s", e, exc_info=True)
        return error_response(f"Failed to exclude IP addresses: {e}")


@mcp.tool()
def list_ip_exclusions(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
) -> str:
    """List all IP address exclusions for a campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_campaign_id = validate_numeric_id(campaign_id, "campaign_id")
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign_criterion.resource_name,
                campaign_criterion.criterion_id,
                campaign_criterion.ip_block.ip_address
            FROM campaign_criterion
            WHERE campaign_criterion.campaign = 'customers/{cid}/campaigns/{safe_campaign_id}'
                AND campaign_criterion.type = 'IP_BLOCK'
                AND campaign_criterion.negative = true
        """

        response = service.search(customer_id=cid, query=query)

        exclusions = []
        for row in response:
            exclusions.append({
                "criterion_id": str(row.campaign_criterion.criterion_id),
                "ip_address": row.campaign_criterion.ip_block.ip_address,
                "resource_name": row.campaign_criterion.resource_name,
            })

        return success_response({"ip_exclusions": exclusions, "count": len(exclusions)})
    except Exception as e:
        logger.error("Failed to list IP exclusions: %s", e, exc_info=True)
        return error_response(f"Failed to list IP exclusions: {e}")
