"""Advanced targeting management tools (11 tools)."""

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


@mcp.tool()
def set_age_bid_adjustment(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    age_range: Annotated[str, "Age range: AGE_RANGE_18_24, AGE_RANGE_25_34, AGE_RANGE_35_44, AGE_RANGE_45_54, AGE_RANGE_55_64, AGE_RANGE_65_UP"],
    bid_modifier: Annotated[float, "Bid modifier (1.0 = no change, 1.2 = +20%, 0.7 = -30%)"],
) -> str:
    """Set an age range bid adjustment for an ad group.

    Adjusts bids for specific age groups. Example: bid_modifier=1.2 bids 20% more for that age range.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag = validate_numeric_id(ad_group_id, "ad_group_id")
        validate_enum_value(age_range, "age_range")
        client = get_client()
        service = get_service("AdGroupCriterionService")

        operation = client.get_type("AdGroupCriterionOperation")
        criterion = operation.create
        criterion.ad_group = f"customers/{cid}/adGroups/{safe_ag}"
        criterion.age_range.type_ = getattr(client.enums.AgeRangeTypeEnum, age_range)
        criterion.bid_modifier = bid_modifier

        response = service.mutate_ad_group_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Age {age_range} bid modifier set to {bid_modifier} on ad group {ad_group_id}",
        )
    except Exception as e:
        logger.error("Failed to set age bid adjustment: %s", e, exc_info=True)
        return error_response(f"Failed to set age bid adjustment: {e}")


@mcp.tool()
def set_gender_bid_adjustment(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    gender: Annotated[str, "Gender: MALE, FEMALE, UNDETERMINED"],
    bid_modifier: Annotated[float, "Bid modifier (1.0 = no change, 1.2 = +20%, 0.7 = -30%)"],
) -> str:
    """Set a gender bid adjustment for an ad group.

    Adjusts bids for specific genders. Example: bid_modifier=1.2 bids 20% more for that gender.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag = validate_numeric_id(ad_group_id, "ad_group_id")
        validate_enum_value(gender, "gender")
        client = get_client()
        service = get_service("AdGroupCriterionService")

        operation = client.get_type("AdGroupCriterionOperation")
        criterion = operation.create
        criterion.ad_group = f"customers/{cid}/adGroups/{safe_ag}"
        criterion.gender.type_ = getattr(client.enums.GenderTypeEnum, gender)
        criterion.bid_modifier = bid_modifier

        response = service.mutate_ad_group_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Gender {gender} bid modifier set to {bid_modifier} on ad group {ad_group_id}",
        )
    except Exception as e:
        logger.error("Failed to set gender bid adjustment: %s", e, exc_info=True)
        return error_response(f"Failed to set gender bid adjustment: {e}")


@mcp.tool()
def set_income_bid_adjustment(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    income_range: Annotated[str, "Income range: INCOME_RANGE_0_50 (lower 50%), INCOME_RANGE_50_60, INCOME_RANGE_60_70, INCOME_RANGE_70_80, INCOME_RANGE_80_90, INCOME_RANGE_90_UP (top 10%)"],
    bid_modifier: Annotated[float, "Bid modifier (1.0 = no change, 1.3 = +30%, 0.8 = -20%)"],
) -> str:
    """Set a household income bid adjustment for an ad group.

    Income ranges are percentile-based: INCOME_RANGE_90_UP = top 10%, INCOME_RANGE_0_50 = lower 50%.
    Note: Income data is estimated based on area demographics, not individual users.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag = validate_numeric_id(ad_group_id, "ad_group_id")
        validate_enum_value(income_range, "income_range")
        client = get_client()
        service = get_service("AdGroupCriterionService")

        operation = client.get_type("AdGroupCriterionOperation")
        criterion = operation.create
        criterion.ad_group = f"customers/{cid}/adGroups/{safe_ag}"
        criterion.income_range.type_ = getattr(client.enums.IncomeRangeTypeEnum, income_range)
        criterion.bid_modifier = bid_modifier

        response = service.mutate_ad_group_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Income {income_range} bid modifier set to {bid_modifier} on ad group {ad_group_id}",
        )
    except Exception as e:
        logger.error("Failed to set income bid adjustment: %s", e, exc_info=True)
        return error_response(f"Failed to set income bid adjustment: {e}")


@mcp.tool()
def set_demographic_bid_adjustments(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    adjustments: Annotated[list[dict], "List of {type, value, bid_modifier}. type: 'age'|'gender'|'income'. value: enum name. bid_modifier: float."],
) -> str:
    """Set multiple demographic bid adjustments for an ad group in a single call.

    Example: [{"type": "age", "value": "AGE_RANGE_25_34", "bid_modifier": 1.2},
              {"type": "income", "value": "INCOME_RANGE_90_UP", "bid_modifier": 1.3}]
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag = validate_numeric_id(ad_group_id, "ad_group_id")
        client = get_client()
        service = get_service("AdGroupCriterionService")

        enum_map = {
            "age": ("age_range", "type_", "AgeRangeTypeEnum"),
            "gender": ("gender", "type_", "GenderTypeEnum"),
            "income": ("income_range", "type_", "IncomeRangeTypeEnum"),
        }

        operations = []
        for adj in adjustments:
            demo_type = adj.get("type", "")
            if demo_type not in enum_map:
                return error_response(f"Invalid type '{demo_type}'. Use: age, gender, income")

            field_name, attr_name, enum_name = enum_map[demo_type]
            value = adj.get("value", "")
            validate_enum_value(value, f"{demo_type}_value")

            operation = client.get_type("AdGroupCriterionOperation")
            criterion = operation.create
            criterion.ad_group = f"customers/{cid}/adGroups/{safe_ag}"
            criterion_field = getattr(criterion, field_name)
            setattr(criterion_field, attr_name, getattr(getattr(client.enums, enum_name), value))
            criterion.bid_modifier = adj.get("bid_modifier", 1.0)
            operations.append(operation)

        response = service.mutate_ad_group_criteria(customer_id=cid, operations=operations)
        return success_response(
            {"applied": len(response.results)},
            message=f"{len(response.results)} demographic bid adjustments set on ad group {ad_group_id}",
        )
    except Exception as e:
        logger.error("Failed to set demographic bid adjustments: %s", e, exc_info=True)
        return error_response(f"Failed to set demographic bid adjustments: {e}")
