"""Smart Campaign suggestions and management tools (4 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import (
    error_response,
    format_micros,
    resolve_customer_id,
    success_response,
    validate_limit,
    validate_numeric_id,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def suggest_smart_campaign_budget(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    business_name: Annotated[str, "The business name"],
    landing_page_url: Annotated[str, "The landing page URL"],
    location_ids: Annotated[list[str] | None, "Geo target constant IDs for targeting"] = None,
    language_code: Annotated[str, "Language code (e.g. 'pt' for Portuguese)"] = "pt",
) -> str:
    """Get budget suggestions for a Smart Campaign.

    Returns recommended daily budget amounts (low, recommended, high)
    based on business type and targeting.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("SmartCampaignSuggestService")

        suggestion_info = client.get_type("SmartCampaignSuggestionInfo")
        suggestion_info.final_url = landing_page_url
        suggestion_info.language_code = language_code
        suggestion_info.business_context.business_name = business_name

        if location_ids:
            for loc_id in location_ids:
                safe_id = validate_numeric_id(loc_id, "location_id")
                location = client.get_type("LocationInfo")
                location.geo_target_constant = f"geoTargetConstants/{safe_id}"
                suggestion_info.location_list.locations.append(location)

        response = service.suggest_smart_campaign_budget_options(
            customer_id=cid,
            suggestion_info=suggestion_info,
        )

        data = {}
        if hasattr(response, "low") and response.low:
            data["low"] = {
                "daily_amount": format_micros(response.low.daily_amount_micros),
                "daily_amount_micros": response.low.daily_amount_micros,
            }
        if hasattr(response, "recommended") and response.recommended:
            data["recommended"] = {
                "daily_amount": format_micros(response.recommended.daily_amount_micros),
                "daily_amount_micros": response.recommended.daily_amount_micros,
            }
        if hasattr(response, "high") and response.high:
            data["high"] = {
                "daily_amount": format_micros(response.high.daily_amount_micros),
                "daily_amount_micros": response.high.daily_amount_micros,
            }

        return success_response(data)
    except Exception as e:
        logger.error("Failed to suggest smart campaign budget: %s", e, exc_info=True)
        return error_response(f"Failed to suggest smart campaign budget: {e}")


@mcp.tool()
def suggest_smart_campaign_ad(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    business_name: Annotated[str, "The business name"],
    landing_page_url: Annotated[str, "The landing page URL"],
    language_code: Annotated[str, "Language code"] = "pt",
) -> str:
    """Get ad creative suggestions for a Smart Campaign.

    Returns suggested headlines and descriptions based on the landing page content.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("SmartCampaignSuggestService")

        suggestion_info = client.get_type("SmartCampaignSuggestionInfo")
        suggestion_info.final_url = landing_page_url
        suggestion_info.language_code = language_code
        suggestion_info.business_context.business_name = business_name

        response = service.suggest_smart_campaign_ad(
            customer_id=cid,
            suggestion_info=suggestion_info,
        )

        ad_info = response.ad_info if hasattr(response, "ad_info") else response

        headlines = []
        if hasattr(ad_info, "headlines"):
            for headline in ad_info.headlines:
                text = headline.text if hasattr(headline, "text") else str(headline)
                headlines.append(text)

        descriptions = []
        if hasattr(ad_info, "descriptions"):
            for description in ad_info.descriptions:
                text = description.text if hasattr(description, "text") else str(description)
                descriptions.append(text)

        data = {
            "headlines": headlines,
            "descriptions": descriptions,
            "headline_count": len(headlines),
            "description_count": len(descriptions),
        }

        return success_response(data)
    except Exception as e:
        logger.error("Failed to suggest smart campaign ad: %s", e, exc_info=True)
        return error_response(f"Failed to suggest smart campaign ad: {e}")


@mcp.tool()
def suggest_keyword_themes(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    business_name: Annotated[str, "The business name"],
    landing_page_url: Annotated[str, "The landing page URL"],
    language_code: Annotated[str, "Language code"] = "pt",
    country_code: Annotated[str, "Country code"] = "BR",
) -> str:
    """Get keyword theme suggestions for a Smart Campaign.

    Keyword themes are broader than regular keywords -- they represent
    topics/themes that trigger the ad.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("SmartCampaignSuggestService")

        suggestion_info = client.get_type("SmartCampaignSuggestionInfo")
        suggestion_info.final_url = landing_page_url
        suggestion_info.language_code = language_code
        suggestion_info.business_context.business_name = business_name

        response = service.suggest_keyword_theme_constants(
            customer_id=cid,
            suggestion_info=suggestion_info,
        )

        keyword_themes = []
        if hasattr(response, "keyword_theme_constants"):
            for theme in response.keyword_theme_constants:
                theme_data = {
                    "resource_name": theme.resource_name if hasattr(theme, "resource_name") else "",
                    "display_name": theme.display_name if hasattr(theme, "display_name") else "",
                }
                keyword_themes.append(theme_data)

        data = {
            "keyword_themes": keyword_themes,
            "count": len(keyword_themes),
        }

        return success_response(data)
    except Exception as e:
        logger.error("Failed to suggest keyword themes: %s", e, exc_info=True)
        return error_response(f"Failed to suggest keyword themes: {e}")


@mcp.tool()
def list_smart_campaign_settings(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """List Smart Campaign-specific settings for all Smart Campaigns in the account.

    Shows phone number, final URL, and keyword themes configured for each Smart Campaign.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                smart_campaign_setting.resource_name,
                smart_campaign_setting.campaign,
                smart_campaign_setting.final_url,
                smart_campaign_setting.phone_number.country_code,
                smart_campaign_setting.phone_number.phone_number,
                smart_campaign_setting.advertising_language_code,
                smart_campaign_setting.business_name
            FROM smart_campaign_setting
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)

        settings = []
        for row in response:
            setting = row.smart_campaign_setting
            settings.append({
                "resource_name": setting.resource_name,
                "campaign": setting.campaign,
                "final_url": setting.final_url,
                "phone_country_code": setting.phone_number.country_code,
                "phone_number": setting.phone_number.phone_number,
                "advertising_language_code": setting.advertising_language_code,
                "business_name": setting.business_name,
            })

        return success_response({"settings": settings, "count": len(settings)})
    except Exception as e:
        logger.error("Failed to list smart campaign settings: %s", e, exc_info=True)
        return error_response(f"Failed to list smart campaign settings: {e}")
