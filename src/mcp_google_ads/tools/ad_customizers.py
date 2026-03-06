"""Customizer attribute management tools for dynamic ad personalization (5 tools)."""

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
def list_customizer_attributes(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum number of results"] = 100,
) -> str:
    """List all customizer attributes for dynamic ad personalization.

    Customizer attributes allow inserting dynamic values (prices, locations, etc.)
    into ad text using {CUSTOMIZER.attribute_name:default} syntax.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                customizer_attribute.resource_name,
                customizer_attribute.id,
                customizer_attribute.name,
                customizer_attribute.type,
                customizer_attribute.status
            FROM customizer_attribute
            WHERE customizer_attribute.status != 'REMOVED'
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        attributes = []
        for row in response:
            attributes.append({
                "resource_name": row.customizer_attribute.resource_name,
                "id": row.customizer_attribute.id,
                "name": row.customizer_attribute.name,
                "type": row.customizer_attribute.type_.name,
                "status": row.customizer_attribute.status.name,
            })
        return success_response({"customizer_attributes": attributes, "count": len(attributes)})
    except Exception as e:
        logger.error("Failed to list customizer attributes: %s", e, exc_info=True)
        return error_response(f"Failed to list customizer attributes: {e}")


@mcp.tool()
def create_customizer_attribute(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Attribute name (used in ad text as {CUSTOMIZER.name:default})"],
    type: Annotated[str, "Type: TEXT, NUMBER, PRICE, PERCENT"] = "TEXT",
) -> str:
    """Create a customizer attribute for dynamic ad text.

    After creating, assign values at campaign/ad_group level using set_campaign_customizer_value
    or set_ad_group_customizer_value.
    Use in ads: {CUSTOMIZER.attribute_name:default_value}
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_type = validate_enum_value(type, "type")
        client = get_client()
        service = get_service("CustomizerAttributeService")

        operation = client.get_type("CustomizerAttributeOperation")
        attr = operation.create
        attr.name = name
        attr.type_ = getattr(client.enums.CustomizerAttributeTypeEnum, safe_type)

        response = service.mutate_customizer_attributes(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        attr_id = resource_name.split("/")[-1]

        return success_response(
            {
                "customizer_attribute_id": attr_id,
                "resource_name": resource_name,
                "name": name,
                "type": safe_type,
            },
            message=f"Customizer attribute '{name}' created (type={safe_type})",
        )
    except Exception as e:
        logger.error("Failed to create customizer attribute: %s", e, exc_info=True)
        return error_response(f"Failed to create customizer attribute: {e}")


@mcp.tool()
def remove_customizer_attribute(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    customizer_attribute_id: Annotated[str, "The customizer attribute ID"],
) -> str:
    """Remove a customizer attribute. This will affect all ads using this attribute."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_id = validate_numeric_id(customizer_attribute_id, "customizer_attribute_id")
        client = get_client()
        service = get_service("CustomizerAttributeService")

        operation = client.get_type("CustomizerAttributeOperation")
        operation.remove = f"customers/{cid}/customizerAttributes/{safe_id}"

        service.mutate_customizer_attributes(customer_id=cid, operations=[operation])

        return success_response(
            {"customizer_attribute_id": customizer_attribute_id, "action": "removed"},
            message=f"Customizer attribute {customizer_attribute_id} removed",
        )
    except Exception as e:
        logger.error("Failed to remove customizer attribute: %s", e, exc_info=True)
        return error_response(f"Failed to remove customizer attribute: {e}")


@mcp.tool()
def set_campaign_customizer_value(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    customizer_attribute_id: Annotated[str, "The customizer attribute ID"],
    value: Annotated[str, "The value to set (text, number, or price like '19.99 BRL')"],
) -> str:
    """Set a customizer attribute value at the campaign level.

    All ads in this campaign using {CUSTOMIZER.attribute_name} will show this value.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_campaign_id = validate_numeric_id(campaign_id, "campaign_id")
        safe_attr_id = validate_numeric_id(customizer_attribute_id, "customizer_attribute_id")
        client = get_client()
        service = get_service("CampaignCustomizerService")

        operation = client.get_type("CampaignCustomizerOperation")
        customizer = operation.create
        customizer.campaign = f"customers/{cid}/campaigns/{safe_campaign_id}"
        customizer.customizer_attribute = f"customers/{cid}/customizerAttributes/{safe_attr_id}"
        customizer.value.type_ = client.enums.CustomizerAttributeTypeEnum.TEXT
        customizer.value.string_value = value

        response = service.mutate_campaign_customizers(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name

        return success_response(
            {
                "resource_name": resource_name,
                "campaign_id": campaign_id,
                "customizer_attribute_id": customizer_attribute_id,
                "value": value,
            },
            message=f"Customizer value set for campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to set campaign customizer value: %s", e, exc_info=True)
        return error_response(f"Failed to set campaign customizer value: {e}")


@mcp.tool()
def set_ad_group_customizer_value(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    customizer_attribute_id: Annotated[str, "The customizer attribute ID"],
    value: Annotated[str, "The value to set"],
) -> str:
    """Set a customizer attribute value at the ad group level.

    Ad group values override campaign-level values for the same attribute.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag_id = validate_numeric_id(ad_group_id, "ad_group_id")
        safe_attr_id = validate_numeric_id(customizer_attribute_id, "customizer_attribute_id")
        client = get_client()
        service = get_service("AdGroupCustomizerService")

        operation = client.get_type("AdGroupCustomizerOperation")
        customizer = operation.create
        customizer.ad_group = f"customers/{cid}/adGroups/{safe_ag_id}"
        customizer.customizer_attribute = f"customers/{cid}/customizerAttributes/{safe_attr_id}"
        customizer.value.type_ = client.enums.CustomizerAttributeTypeEnum.TEXT
        customizer.value.string_value = value

        response = service.mutate_ad_group_customizers(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name

        return success_response(
            {
                "resource_name": resource_name,
                "ad_group_id": ad_group_id,
                "customizer_attribute_id": customizer_attribute_id,
                "value": value,
            },
            message=f"Customizer value set for ad group {ad_group_id}",
        )
    except Exception as e:
        logger.error("Failed to set ad group customizer value: %s", e, exc_info=True)
        return error_response(f"Failed to set ad group customizer value: {e}")
