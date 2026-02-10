"""Audience management tools (6 tools)."""

from __future__ import annotations

from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response


@mcp.tool()
def list_audience_segments(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    segment_type: Annotated[str | None, "Filter by type: CUSTOM, COMBINED, REMARKETING, etc."] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """List available audience segments for targeting."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        type_filter = f"WHERE audience.type = '{segment_type}'" if segment_type else ""

        query = f"""
            SELECT
                audience.id,
                audience.name,
                audience.status,
                audience.description,
                audience.type
            FROM audience
            {type_filter}
            ORDER BY audience.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        segments = []
        for row in response:
            segments.append({
                "audience_id": str(row.audience.id),
                "name": row.audience.name,
                "status": row.audience.status.name,
                "description": row.audience.description,
                "type": row.audience.type_.name,
            })
        return success_response({"segments": segments, "count": len(segments)})
    except Exception as e:
        return error_response(f"Failed to list audience segments: {e}")


@mcp.tool()
def add_audience_targeting(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    audience_id: Annotated[str, "The audience segment ID to target"],
    bid_modifier: Annotated[float | None, "Bid modifier (e.g., 1.2 = +20%)"] = None,
) -> str:
    """Add an audience segment as targeting criterion to a campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignCriterionService")

        operation = client.get_type("CampaignCriterionOperation")
        criterion = operation.create
        criterion.campaign = f"customers/{cid}/campaigns/{campaign_id}"
        criterion.audience.audience = f"customers/{cid}/audiences/{audience_id}"

        if bid_modifier is not None:
            criterion.bid_modifier = bid_modifier

        response = service.mutate_campaign_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Audience {audience_id} added to campaign {campaign_id}",
        )
    except Exception as e:
        return error_response(f"Failed to add audience targeting: {e}")


@mcp.tool()
def remove_audience_targeting(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    criterion_id: Annotated[str, "The campaign criterion ID to remove"],
) -> str:
    """Remove an audience targeting criterion from a campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignCriterionService")

        operation = client.get_type("CampaignCriterionOperation")
        operation.remove = f"customers/{cid}/campaignCriteria/{campaign_id}~{criterion_id}"

        response = service.mutate_campaign_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Audience criterion {criterion_id} removed from campaign {campaign_id}",
        )
    except Exception as e:
        return error_response(f"Failed to remove audience targeting: {e}")


@mcp.tool()
def suggest_geo_targets(
    locale: Annotated[str, "Locale for suggestions (e.g., 'pt_BR', 'en_US')"] = "pt_BR",
    country_code: Annotated[str, "Country code (e.g., 'BR', 'US')"] = "BR",
    query: Annotated[str | None, "Search query for location name"] = None,
) -> str:
    """Suggest geographic targeting locations by name search.

    Use this to find geo target criterion IDs for specific cities, regions, or countries.
    """
    try:
        client = get_client()
        service = get_service("GeoTargetConstantService")

        request = client.get_type("SuggestGeoTargetConstantsRequest")
        request.locale = locale
        request.country_code = country_code

        if query:
            request.location_names.names.append(query)

        response = service.suggest_geo_target_constants(request=request)
        suggestions = []
        for suggestion in response.geo_target_constant_suggestions:
            geo = suggestion.geo_target_constant
            suggestions.append({
                "criterion_id": str(geo.id),
                "name": geo.name,
                "canonical_name": geo.canonical_name,
                "target_type": geo.target_type,
                "country_code": geo.country_code,
                "status": geo.status.name,
            })
        return success_response({"suggestions": suggestions, "count": len(suggestions)})
    except Exception as e:
        return error_response(f"Failed to suggest geo targets: {e}")


@mcp.tool()
def list_campaign_targeting(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    criterion_type: Annotated[str | None, "Filter: LOCATION, LANGUAGE, AUDIENCE, DEVICE, etc."] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """List all targeting criteria for a campaign (locations, languages, audiences, devices)."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        type_filter = f"AND campaign_criterion.type = '{criterion_type}'" if criterion_type else ""

        query = f"""
            SELECT
                campaign_criterion.criterion_id,
                campaign_criterion.type,
                campaign_criterion.negative,
                campaign_criterion.bid_modifier,
                campaign_criterion.status,
                campaign_criterion.location.geo_target_constant,
                campaign_criterion.language.language_constant,
                campaign.id
            FROM campaign_criterion
            WHERE campaign.id = {campaign_id} {type_filter}
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        criteria = []
        for row in response:
            criteria.append({
                "criterion_id": str(row.campaign_criterion.criterion_id),
                "type": row.campaign_criterion.type_.name,
                "negative": row.campaign_criterion.negative,
                "bid_modifier": row.campaign_criterion.bid_modifier,
                "status": row.campaign_criterion.status.name,
            })
        return success_response({"criteria": criteria, "count": len(criteria)})
    except Exception as e:
        return error_response(f"Failed to list campaign targeting: {e}")


@mcp.tool()
def add_audience_to_ad_group(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    audience_id: Annotated[str, "The audience segment ID"],
    bid_modifier: Annotated[float | None, "Bid modifier (e.g., 1.5 = +50%)"] = None,
) -> str:
    """Add an audience segment as targeting to an ad group."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupCriterionService")

        operation = client.get_type("AdGroupCriterionOperation")
        criterion = operation.create
        criterion.ad_group = f"customers/{cid}/adGroups/{ad_group_id}"
        criterion.audience.audience = f"customers/{cid}/audiences/{audience_id}"

        if bid_modifier is not None:
            criterion.bid_modifier = bid_modifier

        response = service.mutate_ad_group_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Audience {audience_id} added to ad group {ad_group_id}",
        )
    except Exception as e:
        return error_response(f"Failed to add audience to ad group: {e}")
