"""Advanced targeting management tools (7 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response, validate_enum_value, validate_numeric_id

logger = logging.getLogger(__name__)


@mcp.tool()
def set_device_bid_adjustment(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    device_type: Annotated[str, "Device: MOBILE, DESKTOP, TABLET, CONNECTED_TV"],
    bid_modifier: Annotated[float, "Bid modifier (1.0 = no change, 1.2 = +20%, 0.8 = -20%, 0 = exclude)"],
) -> str:
    """Set a device bid adjustment for a campaign.

    Use bid_modifier=0 to exclude a device. Use 1.0 for no adjustment.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignCriterionService")

        operation = client.get_type("CampaignCriterionOperation")
        criterion = operation.create
        criterion.campaign = f"customers/{cid}/campaigns/{campaign_id}"
        validate_enum_value(device_type, "device_type")
        criterion.device.type_ = getattr(client.enums.DeviceEnum, device_type)
        criterion.bid_modifier = bid_modifier

        response = service.mutate_campaign_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Device {device_type} bid modifier set to {bid_modifier} on campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to set device bid adjustment: %s", e, exc_info=True)
        return error_response(f"Failed to set device bid adjustment: {e}")


@mcp.tool()
def create_ad_schedule(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    day_of_week: Annotated[str, "Day: MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY"],
    start_hour: Annotated[int, "Start hour (0-23)"],
    end_hour: Annotated[int, "End hour (0-24, use 24 for midnight)"],
    start_minute: Annotated[str, "Start minute: ZERO, FIFTEEN, THIRTY, FORTY_FIVE"] = "ZERO",
    end_minute: Annotated[str, "End minute: ZERO, FIFTEEN, THIRTY, FORTY_FIVE"] = "ZERO",
    bid_modifier: Annotated[float | None, "Bid modifier for this schedule (1.0 = no change)"] = None,
) -> str:
    """Create an ad schedule (dayparting) for a campaign.

    Controls which hours/days ads are shown. Use bid_modifier to adjust bids during specific times.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignCriterionService")

        operation = client.get_type("CampaignCriterionOperation")
        criterion = operation.create
        criterion.campaign = f"customers/{cid}/campaigns/{campaign_id}"
        validate_enum_value(day_of_week, "day_of_week")
        criterion.ad_schedule.day_of_week = getattr(client.enums.DayOfWeekEnum, day_of_week)
        criterion.ad_schedule.start_hour = start_hour
        criterion.ad_schedule.end_hour = end_hour
        validate_enum_value(start_minute, "start_minute")
        criterion.ad_schedule.start_minute = getattr(client.enums.MinuteOfHourEnum, start_minute)
        validate_enum_value(end_minute, "end_minute")
        criterion.ad_schedule.end_minute = getattr(client.enums.MinuteOfHourEnum, end_minute)

        if bid_modifier is not None:
            criterion.bid_modifier = bid_modifier

        response = service.mutate_campaign_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Ad schedule created: {day_of_week} {start_hour}:00-{end_hour}:00",
        )
    except Exception as e:
        logger.error("Failed to create ad schedule: %s", e, exc_info=True)
        return error_response(f"Failed to create ad schedule: {e}")


@mcp.tool()
def list_ad_schedules(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
) -> str:
    """List all ad schedules (dayparting) for a campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign_criterion.criterion_id,
                campaign_criterion.ad_schedule.day_of_week,
                campaign_criterion.ad_schedule.start_hour,
                campaign_criterion.ad_schedule.end_hour,
                campaign_criterion.ad_schedule.start_minute,
                campaign_criterion.ad_schedule.end_minute,
                campaign_criterion.bid_modifier
            FROM campaign_criterion
            WHERE campaign.id = {validate_numeric_id(campaign_id, "campaign_id")}
                AND campaign_criterion.type = 'AD_SCHEDULE'
        """
        response = service.search(customer_id=cid, query=query)
        schedules = []
        for row in response:
            schedules.append({
                "criterion_id": str(row.campaign_criterion.criterion_id),
                "day_of_week": row.campaign_criterion.ad_schedule.day_of_week.name,
                "start_hour": row.campaign_criterion.ad_schedule.start_hour,
                "end_hour": row.campaign_criterion.ad_schedule.end_hour,
                "start_minute": row.campaign_criterion.ad_schedule.start_minute.name,
                "end_minute": row.campaign_criterion.ad_schedule.end_minute.name,
                "bid_modifier": row.campaign_criterion.bid_modifier,
            })
        return success_response({"schedules": schedules, "count": len(schedules)})
    except Exception as e:
        logger.error("Failed to list ad schedules: %s", e, exc_info=True)
        return error_response(f"Failed to list ad schedules: {e}")


@mcp.tool()
def remove_ad_schedule(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    criterion_id: Annotated[str, "The ad schedule criterion ID"],
) -> str:
    """Remove an ad schedule from a campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignCriterionService")

        operation = client.get_type("CampaignCriterionOperation")
        operation.remove = f"customers/{cid}/campaignCriteria/{campaign_id}~{criterion_id}"

        response = service.mutate_campaign_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Ad schedule {criterion_id} removed from campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to remove ad schedule: %s", e, exc_info=True)
        return error_response(f"Failed to remove ad schedule: {e}")


@mcp.tool()
def exclude_geo_location(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    geo_target_id: Annotated[str, "Geo target criterion ID (use suggest_geo_targets to find IDs)"],
) -> str:
    """Exclude a geographic location from a campaign.

    Use suggest_geo_targets to find geo_target_id for specific locations.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignCriterionService")

        operation = client.get_type("CampaignCriterionOperation")
        criterion = operation.create
        criterion.campaign = f"customers/{cid}/campaigns/{campaign_id}"
        criterion.negative = True
        criterion.location.geo_target_constant = f"geoTargetConstants/{geo_target_id}"

        response = service.mutate_campaign_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Geo location {geo_target_id} excluded from campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to exclude geo location: %s", e, exc_info=True)
        return error_response(f"Failed to exclude geo location: {e}")


@mcp.tool()
def add_geo_location(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    geo_target_ids: Annotated[list[str], "List of geo target criterion IDs to add (use suggest_geo_targets to find IDs)"],
) -> str:
    """Add geographic location targeting to a campaign (positive — include locations).

    Use suggest_geo_targets to find geo_target_id for specific locations.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignCriterionService")

        operations = []
        for geo_id in geo_target_ids:
            operation = client.get_type("CampaignCriterionOperation")
            criterion = operation.create
            criterion.campaign = f"customers/{cid}/campaigns/{campaign_id}"
            criterion.location.geo_target_constant = f"geoTargetConstants/{geo_id}"
            operations.append(operation)

        response = service.mutate_campaign_criteria(customer_id=cid, operations=operations)
        results = [r.resource_name for r in response.results]
        return success_response(
            {"resource_names": results, "count": len(results)},
            message=f"{len(results)} geo locations added to campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to add geo location: %s", e, exc_info=True)
        return error_response(f"Failed to add geo location: {e}")


@mcp.tool()
def add_language_targeting(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    language_id: Annotated[str, "Language criterion ID (1000=English, 1014=Portuguese, 1003=Spanish)"],
) -> str:
    """Add a language targeting criterion to a campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignCriterionService")

        operation = client.get_type("CampaignCriterionOperation")
        criterion = operation.create
        criterion.campaign = f"customers/{cid}/campaigns/{campaign_id}"
        criterion.language.language_constant = f"languageConstants/{language_id}"

        response = service.mutate_campaign_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Language {language_id} targeting added to campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to add language targeting: %s", e, exc_info=True)
        return error_response(f"Failed to add language targeting: {e}")


@mcp.tool()
def remove_language_targeting(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    criterion_id: Annotated[str, "The language criterion ID to remove"],
) -> str:
    """Remove a language targeting criterion from a campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignCriterionService")

        operation = client.get_type("CampaignCriterionOperation")
        operation.remove = f"customers/{cid}/campaignCriteria/{campaign_id}~{criterion_id}"

        response = service.mutate_campaign_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Language targeting {criterion_id} removed from campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to remove language targeting: %s", e, exc_info=True)
        return error_response(f"Failed to remove language targeting: {e}")
