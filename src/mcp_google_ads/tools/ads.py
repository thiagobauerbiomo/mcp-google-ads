"""Ad management tools (6 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from google.api_core import protobuf_helpers

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import (
    error_response,
    resolve_customer_id,
    success_response,
    validate_enum_value,
    validate_limit,
    validate_numeric_id,
    validate_status,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def list_ads(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str | None, "Filter by ad group ID"] = None,
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    status_filter: Annotated[str | None, "Filter: ENABLED, PAUSED, REMOVED"] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """List ads with their RSA headlines, descriptions, and status."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        conditions = []
        if ad_group_id:
            conditions.append(f"ad_group.id = {validate_numeric_id(ad_group_id, 'ad_group_id')}")
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")
        if status_filter:
            conditions.append(f"ad_group_ad.status = '{validate_status(status_filter)}'")
        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.name,
                ad_group_ad.ad.type,
                ad_group_ad.status,
                ad_group_ad.ad.final_urls,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad_strength,
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name
            FROM ad_group_ad
            {where}
            ORDER BY ad_group_ad.ad.id ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        ads_list = []
        for row in response:
            headlines = [h.text for h in row.ad_group_ad.ad.responsive_search_ad.headlines]
            descriptions = [d.text for d in row.ad_group_ad.ad.responsive_search_ad.descriptions]
            ads_list.append({
                "ad_id": str(row.ad_group_ad.ad.id),
                "name": row.ad_group_ad.ad.name,
                "type": row.ad_group_ad.ad.type_.name,
                "status": row.ad_group_ad.status.name,
                "final_urls": list(row.ad_group_ad.ad.final_urls),
                "headlines": headlines,
                "descriptions": descriptions,
                "ad_strength": row.ad_group_ad.ad_strength.name,
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
            })
        return success_response({"ads": ads_list, "count": len(ads_list)})
    except Exception as e:
        logger.error("Failed to list ads: %s", e, exc_info=True)
        return error_response(f"Failed to list ads: {e}")


@mcp.tool()
def get_ad(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID containing the ad"],
    ad_id: Annotated[str, "The ad ID"],
) -> str:
    """Get detailed information about a specific ad."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag = validate_numeric_id(ad_group_id, "ad_group_id")
        safe_ad = validate_numeric_id(ad_id, "ad_id")
        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.name,
                ad_group_ad.ad.type,
                ad_group_ad.status,
                ad_group_ad.ad.final_urls,
                ad_group_ad.ad.final_mobile_urls,
                ad_group_ad.ad.tracking_url_template,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.responsive_search_ad.path1,
                ad_group_ad.ad.responsive_search_ad.path2,
                ad_group_ad.ad_strength,
                ad_group_ad.policy_summary.approval_status
            FROM ad_group_ad
            WHERE ad_group.id = {safe_ag} AND ad_group_ad.ad.id = {safe_ad}
        """
        response = service.search(customer_id=cid, query=query)
        for row in response:
            rsa = row.ad_group_ad.ad.responsive_search_ad
            headlines = [{"text": h.text, "pinned_field": h.pinned_field.name} for h in rsa.headlines]
            descriptions = [{"text": d.text, "pinned_field": d.pinned_field.name} for d in rsa.descriptions]
            data = {
                "ad_id": str(row.ad_group_ad.ad.id),
                "name": row.ad_group_ad.ad.name,
                "type": row.ad_group_ad.ad.type_.name,
                "status": row.ad_group_ad.status.name,
                "final_urls": list(row.ad_group_ad.ad.final_urls),
                "final_mobile_urls": list(row.ad_group_ad.ad.final_mobile_urls),
                "tracking_url_template": row.ad_group_ad.ad.tracking_url_template,
                "headlines": headlines,
                "descriptions": descriptions,
                "path1": rsa.path1,
                "path2": rsa.path2,
                "ad_strength": row.ad_group_ad.ad_strength.name,
                "approval_status": row.ad_group_ad.policy_summary.approval_status.name,
            }
            return success_response(data)
        return error_response(f"Ad {ad_id} not found in ad group {ad_group_id}")
    except Exception as e:
        logger.error("Failed to get ad: %s", e, exc_info=True)
        return error_response(f"Failed to get ad: {e}")


_PIN_FIELD_MAP = {
    "HEADLINE_1": "HEADLINE_1",
    "HEADLINE_2": "HEADLINE_2",
    "HEADLINE_3": "HEADLINE_3",
    "DESCRIPTION_1": "DESCRIPTION_1",
    "DESCRIPTION_2": "DESCRIPTION_2",
}


@mcp.tool()
def create_responsive_search_ad(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    headlines: Annotated[list[str], "List of headlines (3-15, each max 30 chars)"],
    descriptions: Annotated[list[str], "List of descriptions (2-4, each max 90 chars)"],
    final_url: Annotated[str, "Landing page URL"],
    path1: Annotated[str | None, "Display URL path 1 (max 15 chars)"] = None,
    path2: Annotated[str | None, "Display URL path 2 (max 15 chars)"] = None,
    pinned_headlines: Annotated[
        dict[int, str] | None,
        "Pin headlines to positions. Key=0-based index, value=HEADLINE_1/HEADLINE_2/HEADLINE_3. Example: {0: 'HEADLINE_1', 2: 'HEADLINE_2'}",
    ] = None,
    pinned_descriptions: Annotated[
        dict[int, str] | None,
        "Pin descriptions to positions. Key=0-based index, value=DESCRIPTION_1/DESCRIPTION_2. Example: {0: 'DESCRIPTION_1'}",
    ] = None,
) -> str:
    """Create a Responsive Search Ad (RSA). Created PAUSED by default.

    Requires 3-15 headlines and 2-4 descriptions. More assets = better optimization.
    Use pinned_headlines/pinned_descriptions to pin specific assets to positions.
    """
    try:
        if len(headlines) < 3 or len(headlines) > 15:
            return error_response("Headlines must be between 3 and 15")
        if len(descriptions) < 2 or len(descriptions) > 4:
            return error_response("Descriptions must be between 2 and 4")

        # Validar pins antes de chamar a API
        if pinned_headlines:
            for idx, pin_value in pinned_headlines.items():
                if pin_value not in ("HEADLINE_1", "HEADLINE_2", "HEADLINE_3"):
                    return error_response(f"Invalid pin position '{pin_value}' for headline {idx}. Use HEADLINE_1, HEADLINE_2, or HEADLINE_3")
        if pinned_descriptions:
            for idx, pin_value in pinned_descriptions.items():
                if pin_value not in ("DESCRIPTION_1", "DESCRIPTION_2"):
                    return error_response(f"Invalid pin position '{pin_value}' for description {idx}. Use DESCRIPTION_1 or DESCRIPTION_2")

        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupAdService")

        operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = operation.create
        ad_group_ad.ad_group = f"customers/{cid}/adGroups/{ad_group_id}"
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED

        ad = ad_group_ad.ad
        ad.final_urls.append(final_url)

        for i, headline_text in enumerate(headlines):
            headline = client.get_type("AdTextAsset")
            headline.text = headline_text
            if pinned_headlines and i in pinned_headlines:
                headline.pinned_field = getattr(client.enums.ServedAssetFieldTypeEnum, pinned_headlines[i])
            ad.responsive_search_ad.headlines.append(headline)

        for i, desc_text in enumerate(descriptions):
            description = client.get_type("AdTextAsset")
            description.text = desc_text
            if pinned_descriptions and i in pinned_descriptions:
                description.pinned_field = getattr(client.enums.ServedAssetFieldTypeEnum, pinned_descriptions[i])
            ad.responsive_search_ad.descriptions.append(description)

        if path1:
            ad.responsive_search_ad.path1 = path1
        if path2:
            ad.responsive_search_ad.path2 = path2

        response = service.mutate_ad_group_ads(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name

        pin_count = len(pinned_headlines or {}) + len(pinned_descriptions or {})
        pin_msg = f" with {pin_count} pins" if pin_count else ""
        return success_response(
            {"resource_name": resource_name, "status": "PAUSED", "pins": pin_count},
            message=f"RSA created as PAUSED{pin_msg}",
        )
    except Exception as e:
        logger.error("Failed to create RSA: %s", e, exc_info=True)
        return error_response(f"Failed to create RSA: {e}")


@mcp.tool()
def update_ad(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    ad_id: Annotated[str, "The ad ID"],
    final_url: Annotated[str | None, "New landing page URL"] = None,
    path1: Annotated[str | None, "New display path 1"] = None,
    path2: Annotated[str | None, "New display path 2"] = None,
) -> str:
    """Update an existing ad's URLs and display paths.

    Note: Headlines and descriptions cannot be updated - create a new ad instead.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupAdService")

        operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = operation.update
        ad_group_ad.ad_group = f"customers/{cid}/adGroups/{ad_group_id}"
        ad_group_ad.ad.resource_name = f"customers/{cid}/ads/{ad_id}"

        fields = []
        if final_url is not None:
            ad_group_ad.ad.final_urls.append(final_url)
            fields.append("ad.final_urls")
        if path1 is not None:
            ad_group_ad.ad.responsive_search_ad.path1 = path1
            fields.append("ad.responsive_search_ad.path1")
        if path2 is not None:
            ad_group_ad.ad.responsive_search_ad.path2 = path2
            fields.append("ad.responsive_search_ad.path2")

        if not fields:
            return error_response("No fields to update")

        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=fields),
        )

        response = service.mutate_ad_group_ads(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Ad {ad_id} updated",
        )
    except Exception as e:
        logger.error("Failed to update ad: %s", e, exc_info=True)
        return error_response(f"Failed to update ad: {e}")


@mcp.tool()
def set_ad_status(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    ad_id: Annotated[str, "The ad ID"],
    status: Annotated[str, "New status: ENABLED, PAUSED, or REMOVED"],
) -> str:
    """Enable, pause, or remove an ad."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag = validate_numeric_id(ad_group_id, "ad_group_id")
        safe_ad = validate_numeric_id(ad_id, "ad_id")
        validate_enum_value(status, "status")
        client = get_client()
        service = get_service("AdGroupAdService")

        operation = client.get_type("AdGroupAdOperation")
        resource_name = f"customers/{cid}/adGroupAds/{safe_ag}~{safe_ad}"

        if status == "REMOVED":
            operation.remove = resource_name
        else:
            ad_group_ad = operation.update
            ad_group_ad.resource_name = resource_name
            ad_group_ad.status = getattr(client.enums.AdGroupAdStatusEnum, status)
            client.copy_from(
                operation.update_mask,
                protobuf_helpers.field_mask_pb2.FieldMask(paths=["status"]),
            )

        response = service.mutate_ad_group_ads(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name, "new_status": status},
            message=f"Ad {ad_id} set to {status}",
        )
    except Exception as e:
        logger.error("Failed to set ad status: %s", e, exc_info=True)
        return error_response(f"Failed to set ad status: {e}")


@mcp.tool()
def get_ad_strength(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str | None, "Filter by ad group ID"] = None,
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get ad strength ratings for RSA ads to identify optimization opportunities."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        conditions = ["ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'"]
        if ad_group_id:
            conditions.append(f"ad_group.id = {validate_numeric_id(ad_group_id, 'ad_group_id')}")
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")
        where = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad_strength,
                ad_group_ad.status,
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name
            FROM ad_group_ad
            {where}
            ORDER BY ad_group_ad.ad_strength ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        results = []
        for row in response:
            results.append({
                "ad_id": str(row.ad_group_ad.ad.id),
                "ad_strength": row.ad_group_ad.ad_strength.name,
                "status": row.ad_group_ad.status.name,
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
            })
        return success_response({"ads": results, "count": len(results)})
    except Exception as e:
        logger.error("Failed to get ad strength: %s", e, exc_info=True)
        return error_response(f"Failed to get ad strength: {e}")
