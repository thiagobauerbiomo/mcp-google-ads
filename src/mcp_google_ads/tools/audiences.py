"""Audience management tools (12 tools)."""

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
def list_audience_segments(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    segment_type: Annotated[str | None, "Filter by type: CUSTOM, COMBINED, REMARKETING, etc."] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """List available audience segments for targeting."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        type_filter = f"WHERE audience.type = '{validate_enum_value(segment_type, 'segment_type')}'" if segment_type else ""

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
        logger.error("Failed to list audience segments: %s", e, exc_info=True)
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
        logger.error("Failed to add audience targeting: %s", e, exc_info=True)
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
        logger.error("Failed to remove audience targeting: %s", e, exc_info=True)
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
        logger.error("Failed to suggest geo targets: %s", e, exc_info=True)
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
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        type_filter = f"AND campaign_criterion.type = '{validate_enum_value(criterion_type, 'criterion_type')}'" if criterion_type else ""

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
            WHERE campaign.id = {validate_numeric_id(campaign_id, "campaign_id")} {type_filter}
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
        logger.error("Failed to list campaign targeting: %s", e, exc_info=True)
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
        logger.error("Failed to add audience to ad group: %s", e, exc_info=True)
        return error_response(f"Failed to add audience to ad group: {e}")


@mcp.tool()
def create_custom_audience(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Unique audience name"],
    audience_type: Annotated[str, "Type: AUTO, SEARCH, INTEREST, PURCHASE_INTENT"],
    members: Annotated[list[dict], "List of {type: 'KEYWORD'|'URL', value: str}"],
) -> str:
    """Create a custom audience with keywords and/or URLs.

    Example members: [{"type": "KEYWORD", "value": "criação de sites"}, {"type": "URL", "value": "https://example.com"}]
    Types: AUTO (Google decides), SEARCH (search history), INTEREST (interests), PURCHASE_INTENT (buying intent).
    """
    try:
        cid = resolve_customer_id(customer_id)
        validate_enum_value(audience_type, "audience_type")
        client = get_client()
        service = get_service("CustomAudienceService")

        operation = client.get_type("CustomAudienceOperation")
        audience = operation.create
        audience.name = name
        audience.type_ = getattr(client.enums.CustomAudienceTypeEnum, audience_type)

        for member in members:
            member_type = member.get("type", "")
            value = member.get("value", "")
            validate_enum_value(member_type, "member_type")
            m = client.get_type("CustomAudienceMember")
            m.member_type = getattr(client.enums.CustomAudienceMemberTypeEnum, member_type)
            if member_type == "KEYWORD":
                m.keyword = value
            elif member_type == "URL":
                m.url = value
            audience.members.append(m)

        response = service.mutate_custom_audiences(customer_id=cid, operations=[operation])
        rn = response.results[0].resource_name
        audience_id = rn.split("/")[-1]
        return success_response(
            {"audience_id": audience_id, "resource_name": rn},
            message=f"Custom audience '{name}' created with {len(members)} members",
        )
    except Exception as e:
        logger.error("Failed to create custom audience: %s", e, exc_info=True)
        return error_response(f"Failed to create custom audience: {e}")


@mcp.tool()
def add_audience_signal(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    asset_group_id: Annotated[str, "The PMax asset group ID"],
    audience_id: Annotated[str, "The audience ID to use as signal"],
) -> str:
    """Add an audience signal to a Performance Max asset group.

    Audience signals help PMax find the right customers. Unlike targeting, signals are hints
    — PMax may show ads beyond the signaled audience if it predicts conversions.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag = validate_numeric_id(asset_group_id, "asset_group_id")
        safe_aud = validate_numeric_id(audience_id, "audience_id")
        client = get_client()
        service = get_service("AssetGroupSignalService")

        operation = client.get_type("AssetGroupSignalOperation")
        signal = operation.create
        signal.asset_group = f"customers/{cid}/assetGroups/{safe_ag}"
        signal.audience.audience = f"customers/{cid}/audiences/{safe_aud}"

        response = service.mutate_asset_group_signals(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Audience signal {audience_id} added to asset group {asset_group_id}",
        )
    except Exception as e:
        logger.error("Failed to add audience signal: %s", e, exc_info=True)
        return error_response(f"Failed to add audience signal: {e}")


@mcp.tool()
def add_search_theme_signal(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    asset_group_id: Annotated[str, "The PMax asset group ID"],
    search_themes: Annotated[list[str], "Search themes (keywords/topics, max 25)"],
) -> str:
    """Add search theme signals to a Performance Max asset group.

    Search themes tell PMax what topics/keywords are relevant. Each theme is a separate signal.
    Max 25 search themes per asset group.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag = validate_numeric_id(asset_group_id, "asset_group_id")
        client = get_client()
        service = get_service("AssetGroupSignalService")

        if len(search_themes) > 25:
            return error_response("Maximum 25 search themes per asset group")

        operations = []
        for theme in search_themes:
            operation = client.get_type("AssetGroupSignalOperation")
            signal = operation.create
            signal.asset_group = f"customers/{cid}/assetGroups/{safe_ag}"
            signal.search_theme.text = theme
            operations.append(operation)

        response = service.mutate_asset_group_signals(customer_id=cid, operations=operations)
        results = [r.resource_name for r in response.results]
        return success_response(
            {"resource_names": results, "count": len(results)},
            message=f"{len(results)} search theme signals added to asset group {asset_group_id}",
        )
    except Exception as e:
        logger.error("Failed to add search theme signals: %s", e, exc_info=True)
        return error_response(f"Failed to add search theme signals: {e}")


@mcp.tool()
def list_asset_group_signals(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    asset_group_id: Annotated[str, "The PMax asset group ID"],
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """List all audience and search theme signals for a PMax asset group."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag = validate_numeric_id(asset_group_id, "asset_group_id")
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                asset_group_signal.resource_name,
                asset_group_signal.asset_group,
                asset_group_signal.audience.audience,
                asset_group_signal.search_theme.text,
                asset_group_signal.approval_status
            FROM asset_group_signal
            WHERE asset_group.id = {safe_ag}
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        signals = []
        for row in response:
            signal_data = {
                "resource_name": row.asset_group_signal.resource_name,
                "approval_status": row.asset_group_signal.approval_status.name,
            }
            if row.asset_group_signal.audience.audience:
                signal_data["type"] = "audience"
                signal_data["audience"] = row.asset_group_signal.audience.audience
            elif row.asset_group_signal.search_theme.text:
                signal_data["type"] = "search_theme"
                signal_data["search_theme"] = row.asset_group_signal.search_theme.text
            signals.append(signal_data)
        return success_response({"signals": signals, "count": len(signals)})
    except Exception as e:
        logger.error("Failed to list asset group signals: %s", e, exc_info=True)
        return error_response(f"Failed to list asset group signals: {e}")


@mcp.tool()
def remove_asset_group_signal(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    signal_resource_name: Annotated[str, "The full resource name of the signal to remove (from list_asset_group_signals)"],
) -> str:
    """Remove an audience or search theme signal from a PMax asset group."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetGroupSignalService")

        operation = client.get_type("AssetGroupSignalOperation")
        operation.remove = signal_resource_name

        response = service.mutate_asset_group_signals(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Signal removed: {signal_resource_name}",
        )
    except Exception as e:
        logger.error("Failed to remove asset group signal: %s", e, exc_info=True)
        return error_response(f"Failed to remove asset group signal: {e}")


@mcp.tool()
def remove_audience_from_ad_group(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    criterion_id: Annotated[str, "The ad group criterion ID to remove"],
) -> str:
    """Remove an audience targeting criterion from an ad group."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag = validate_numeric_id(ad_group_id, "ad_group_id")
        safe_crit = validate_numeric_id(criterion_id, "criterion_id")
        client = get_client()
        service = get_service("AdGroupCriterionService")

        operation = client.get_type("AdGroupCriterionOperation")
        operation.remove = f"customers/{cid}/adGroupCriteria/{safe_ag}~{safe_crit}"

        response = service.mutate_ad_group_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Audience criterion {criterion_id} removed from ad group {ad_group_id}",
        )
    except Exception as e:
        logger.error("Failed to remove audience from ad group: %s", e, exc_info=True)
        return error_response(f"Failed to remove audience from ad group: {e}")
