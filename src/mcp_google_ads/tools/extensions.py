"""Ad extension (asset) management tools (14 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import (
    error_response,
    process_partial_failure,
    resolve_customer_id,
    success_response,
    validate_batch,
    validate_enum_value,
    validate_limit,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def list_assets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    asset_type: Annotated[str | None, "Filter: SITELINK, CALLOUT, STRUCTURED_SNIPPET, CALL, IMAGE, etc."] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """List all assets (extensions) for an account."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        type_filter = f"WHERE asset.type = '{validate_enum_value(asset_type, 'asset_type')}'" if asset_type else ""

        query = f"""
            SELECT
                asset.id,
                asset.name,
                asset.type,
                asset.sitelink_asset.description1,
                asset.sitelink_asset.description2,
                asset.sitelink_asset.link_text,
                asset.callout_asset.callout_text,
                asset.structured_snippet_asset.header,
                asset.call_asset.phone_number,
                asset.final_urls
            FROM asset
            {type_filter}
            ORDER BY asset.type ASC, asset.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        assets = []
        for row in response:
            asset_data = {
                "asset_id": str(row.asset.id),
                "name": row.asset.name,
                "type": row.asset.type_.name,
                "final_urls": list(row.asset.final_urls),
            }
            # Add type-specific fields
            if row.asset.type_.name == "SITELINK":
                asset_data["link_text"] = row.asset.sitelink_asset.link_text
                asset_data["description1"] = row.asset.sitelink_asset.description1
                asset_data["description2"] = row.asset.sitelink_asset.description2
            elif row.asset.type_.name == "CALLOUT":
                asset_data["callout_text"] = row.asset.callout_asset.callout_text
            elif row.asset.type_.name == "STRUCTURED_SNIPPET":
                asset_data["header"] = row.asset.structured_snippet_asset.header
            elif row.asset.type_.name == "CALL":
                asset_data["phone_number"] = row.asset.call_asset.phone_number

            assets.append(asset_data)
        return success_response({"assets": assets, "count": len(assets)})
    except Exception as e:
        logger.error("Failed to list assets: %s", e, exc_info=True)
        return error_response(f"Failed to list assets: {e}")


@mcp.tool()
def create_sitelink_assets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    sitelinks: Annotated[list[dict], "List of {link_text, final_url, description1?, description2?}"],
) -> str:
    """Create sitelink extension assets.

    Example: [{"link_text": "Contact Us", "final_url": "https://example.com/contact", "description1": "Get in touch", "description2": "We respond fast"}]
    """
    try:
        cid = resolve_customer_id(customer_id)

        error = validate_batch(sitelinks, max_size=5000, required_fields=["link_text", "final_url"], item_name="sitelinks")
        if error:
            return error_response(error)

        client = get_client()
        service = get_service("AssetService")

        operations = []
        for sl in sitelinks:
            operation = client.get_type("AssetOperation")
            asset = operation.create
            asset.sitelink_asset.link_text = sl["link_text"]
            asset.final_urls.append(sl["final_url"])
            if sl.get("description1"):
                asset.sitelink_asset.description1 = sl["description1"]
            if sl.get("description2"):
                asset.sitelink_asset.description2 = sl["description2"]
            operations.append(operation)

        response = service.mutate_assets(customer_id=cid, operations=operations)
        results = [r.resource_name for r in response.results]
        result_data = {"created": len(results), "resource_names": results}
        return success_response(
            result_data,
            message=f"{len(results)} sitelink assets created",
        )
    except Exception as e:
        logger.error("Failed to create sitelinks: %s", e, exc_info=True)
        return error_response(f"Failed to create sitelinks: {e}")


@mcp.tool()
def create_callout_assets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    callouts: Annotated[list[str], "List of callout texts (each max 25 chars)"],
) -> str:
    """Create callout extension assets.

    Example: ["Free Shipping", "24/7 Support", "Price Match Guarantee"]
    """
    try:
        cid = resolve_customer_id(customer_id)

        error = validate_batch(callouts, max_size=5000, item_name="callouts")
        if error:
            return error_response(error)

        client = get_client()
        service = get_service("AssetService")

        operations = []
        for text in callouts:
            operation = client.get_type("AssetOperation")
            asset = operation.create
            asset.callout_asset.callout_text = text
            operations.append(operation)

        response = service.mutate_assets(customer_id=cid, operations=operations)
        results = [r.resource_name for r in response.results]
        result_data = {"created": len(results), "resource_names": results}
        return success_response(
            result_data,
            message=f"{len(results)} callout assets created",
        )
    except Exception as e:
        logger.error("Failed to create callouts: %s", e, exc_info=True)
        return error_response(f"Failed to create callouts: {e}")


@mcp.tool()
def create_structured_snippet_assets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    header: Annotated[str, "Snippet header (e.g., 'Brands', 'Services', 'Types', 'Models')"],
    values: Annotated[list[str], "List of snippet values"],
) -> str:
    """Create a structured snippet extension asset.

    Headers: Amenities, Brands, Courses, Degree programs, Destinations, Featured hotels,
    Insurance coverage, Models, Neighborhoods, Service catalog, Shows, Styles, Types.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        operation = client.get_type("AssetOperation")
        asset = operation.create
        asset.structured_snippet_asset.header = header
        for value in values:
            asset.structured_snippet_asset.values.append(value)

        response = service.mutate_assets(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Structured snippet '{header}' created with {len(values)} values",
        )
    except Exception as e:
        logger.error("Failed to create structured snippet: %s", e, exc_info=True)
        return error_response(f"Failed to create structured snippet: {e}")


@mcp.tool()
def create_call_asset(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    phone_number: Annotated[str, "Phone number (e.g., '+5511999999999')"],
    country_code: Annotated[str, "Country code (e.g., 'BR', 'US')"] = "BR",
    call_tracking: Annotated[bool, "Enable Google call tracking"] = True,
) -> str:
    """Create a call extension asset with a phone number."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        operation = client.get_type("AssetOperation")
        asset = operation.create
        asset.call_asset.phone_number = phone_number
        asset.call_asset.country_code = country_code
        asset.call_asset.call_tracking_enabled = call_tracking

        response = service.mutate_assets(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Call asset created: {phone_number}",
        )
    except Exception as e:
        logger.error("Failed to create call asset: %s", e, exc_info=True)
        return error_response(f"Failed to create call asset: {e}")


@mcp.tool()
def remove_asset(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    asset_id: Annotated[str, "The asset ID to remove"],
) -> str:
    """Remove an asset (extension) permanently."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        operation = client.get_type("AssetOperation")
        operation.remove = f"customers/{cid}/assets/{asset_id}"

        response = service.mutate_assets(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Asset {asset_id} removed",
        )
    except Exception as e:
        logger.error("Failed to remove asset: %s", e, exc_info=True)
        return error_response(f"Failed to remove asset: {e}")


@mcp.tool()
def create_image_asset(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    image_url: Annotated[str, "URL of the image to download and use"],
    asset_name: Annotated[str, "Name for the image asset"],
) -> str:
    """Create an image asset from a URL.

    The image will be downloaded and uploaded to Google Ads.
    Supported formats: JPEG, PNG, GIF. Recommended sizes: 1200x628, 1200x1200, 128x128.
    """
    try:
        import urllib.error
        import urllib.request

        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        try:
            image_data = urllib.request.urlopen(image_url, timeout=30).read()
        except urllib.error.HTTPError as e:
            logger.error("HTTP error downloading image from %s: %s", image_url, e, exc_info=True)
            return error_response(f"HTTP error {e.code} downloading image: {e.reason}")
        except urllib.error.URLError as e:
            logger.error("URL error downloading image from %s: %s", image_url, e, exc_info=True)
            return error_response(f"Failed to download image (network error): {e.reason}")

        operation = client.get_type("AssetOperation")
        asset = operation.create
        asset.name = asset_name
        asset.type_ = client.enums.AssetTypeEnum.IMAGE
        asset.image_asset.data = image_data

        response = service.mutate_assets(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        return success_response(
            {"resource_name": resource_name, "asset_id": resource_name.split("/")[-1]},
            message=f"Image asset '{asset_name}' created from URL",
        )
    except Exception as e:
        logger.error("Failed to create image asset: %s", e, exc_info=True)
        return error_response(f"Failed to create image asset: {e}")


@mcp.tool()
def create_video_asset(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    youtube_video_id: Annotated[str, "YouTube video ID (e.g., 'dQw4w9WgXcQ')"],
    asset_name: Annotated[str, "Name for the video asset"],
) -> str:
    """Create a video asset from a YouTube video ID.

    The video must be public or unlisted on YouTube.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        operation = client.get_type("AssetOperation")
        asset = operation.create
        asset.name = asset_name
        asset.type_ = client.enums.AssetTypeEnum.YOUTUBE_VIDEO
        asset.youtube_video_asset.youtube_video_id = youtube_video_id

        response = service.mutate_assets(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        return success_response(
            {"resource_name": resource_name, "asset_id": resource_name.split("/")[-1]},
            message=f"Video asset '{asset_name}' created",
        )
    except Exception as e:
        logger.error("Failed to create video asset: %s", e, exc_info=True)
        return error_response(f"Failed to create video asset: {e}")


@mcp.tool()
def create_lead_form_asset(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    headline: Annotated[str, "Lead form headline (max 30 chars)"],
    business_name: Annotated[str, "Business name"],
    description: Annotated[str, "Description text (max 200 chars)"],
    fields: Annotated[list[str], "Fields: FULL_NAME, EMAIL, PHONE_NUMBER, POSTAL_CODE, CITY, WORK_EMAIL, COMPANY_NAME, etc."],
    privacy_policy_url: Annotated[str, "Privacy policy URL"],
    call_to_action: Annotated[str, "CTA: LEARN_MORE, GET_QUOTE, APPLY_NOW, SIGN_UP, CONTACT_US, SUBSCRIBE, DOWNLOAD, BOOK_NOW, GET_OFFER"] = "LEARN_MORE",
) -> str:
    """Create a lead form extension asset for collecting leads directly from ads.

    Requires privacy policy URL. Fields determine what information is collected.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        operation = client.get_type("AssetOperation")
        asset = operation.create
        asset.name = f"Lead Form - {headline}"
        lead_form = asset.lead_form_asset
        lead_form.headline = headline
        lead_form.business_name = business_name
        lead_form.description = description
        lead_form.privacy_policy_url = privacy_policy_url
        validate_enum_value(call_to_action, "call_to_action")
        lead_form.call_to_action_type = getattr(
            client.enums.LeadFormCallToActionTypeEnum, call_to_action
        )

        for field_name in fields:
            field_input = client.get_type("LeadFormField")
            validate_enum_value(field_name, "field_name")
            field_input.input_type = getattr(client.enums.LeadFormFieldUserInputTypeEnum, field_name)
            lead_form.fields.append(field_input)

        response = service.mutate_assets(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        return success_response(
            {"resource_name": resource_name, "asset_id": resource_name.split("/")[-1]},
            message=f"Lead form asset '{headline}' created with {len(fields)} fields",
        )
    except Exception as e:
        logger.error("Failed to create lead form asset: %s", e, exc_info=True)
        return error_response(f"Failed to create lead form asset: {e}")


@mcp.tool()
def create_price_asset(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    price_type: Annotated[str, "Type: BRANDS, EVENTS, LOCATIONS, NEIGHBORHOODS, PRODUCT_CATEGORIES, PRODUCT_TIERS, SERVICES, SERVICE_CATEGORIES, SERVICE_TIERS"],
    price_items: Annotated[list[dict], "List of {header, description, final_url, price_micros, currency_code, unit}"],
    language_code: Annotated[str, "Language code (e.g., 'pt', 'en')"] = "pt",
) -> str:
    """Create a price extension asset showing products/services with prices.

    Each price item needs: header, description, final_url, price_micros, currency_code.
    Unit is optional: PER_HOUR, PER_DAY, PER_WEEK, PER_MONTH, PER_YEAR, PER_NIGHT.

    Example: [{"header": "Basic", "description": "Starter plan", "final_url": "https://example.com/basic", "price_micros": 29900000, "currency_code": "BRL"}]
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        error = validate_batch(price_items, max_size=5000, required_fields=["header", "description", "final_url", "price_micros"], item_name="price_items")
        if error:
            return error_response(error)

        operation = client.get_type("AssetOperation")
        asset = operation.create
        asset.name = f"Price Extension - {price_type}"
        price_asset = asset.price_asset
        validate_enum_value(price_type, "price_type")
        price_asset.type_ = getattr(client.enums.PriceExtensionTypeEnum, price_type)
        price_asset.language_code = language_code

        for item in price_items:
            price_offering = client.get_type("PriceOffering")
            price_offering.header = item["header"]
            price_offering.description = item["description"]
            price_offering.final_url = item["final_url"]
            price_offering.price.amount_micros = item["price_micros"]
            price_offering.price.currency_code = item.get("currency_code", "BRL")
            if "unit" in item:
                price_offering.unit = getattr(client.enums.PriceExtensionPriceUnitEnum, item["unit"])
            price_asset.price_offerings.append(price_offering)

        response = service.mutate_assets(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        return success_response(
            {"resource_name": resource_name, "asset_id": resource_name.split("/")[-1]},
            message=f"Price asset created with {len(price_items)} items",
        )
    except Exception as e:
        logger.error("Failed to create price asset: %s", e, exc_info=True)
        return error_response(f"Failed to create price asset: {e}")


@mcp.tool()
def create_promotion_asset(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    promotion_target: Annotated[str, "What is being promoted (max 20 chars)"],
    final_url: Annotated[str, "Landing page URL"],
    percent_off: Annotated[int | None, "Percentage discount (e.g., 20 for 20% off)"] = None,
    money_off_micros: Annotated[int | None, "Monetary discount in micros"] = None,
    currency_code: Annotated[str, "Currency code for money_off"] = "BRL",
    occasion: Annotated[str | None, "Occasion: NEW_YEARS, VALENTINES_DAY, EASTER, MOTHERS_DAY, FATHERS_DAY, BLACK_FRIDAY, CYBER_MONDAY, CHRISTMAS, etc."] = None,
    language_code: Annotated[str, "Language code"] = "pt",
) -> str:
    """Create a promotion extension asset for advertising sales and special offers."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        operation = client.get_type("AssetOperation")
        asset = operation.create
        asset.name = f"Promotion - {promotion_target}"
        promo = asset.promotion_asset
        promo.promotion_target = promotion_target
        promo.final_url = final_url
        promo.language_code = language_code

        if percent_off is not None:
            promo.percent_off = percent_off
            promo.discount_modifier = client.enums.PromotionExtensionDiscountModifierEnum.UP_TO
        elif money_off_micros is not None:
            promo.money_amount_off.amount_micros = money_off_micros
            promo.money_amount_off.currency_code = currency_code
            promo.discount_modifier = client.enums.PromotionExtensionDiscountModifierEnum.UP_TO

        if occasion:
            validate_enum_value(occasion, "occasion")
            promo.occasion = getattr(client.enums.PromotionExtensionOccasionEnum, occasion)

        response = service.mutate_assets(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        return success_response(
            {"resource_name": resource_name, "asset_id": resource_name.split("/")[-1]},
            message=f"Promotion asset '{promotion_target}' created",
        )
    except Exception as e:
        logger.error("Failed to create promotion asset: %s", e, exc_info=True)
        return error_response(f"Failed to create promotion asset: {e}")


@mcp.tool()
def link_asset_to_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    asset_id: Annotated[str, "The asset ID to link"],
    field_type: Annotated[str, "Asset field type: SITELINK, CALLOUT, STRUCTURED_SNIPPET, CALL, MOBILE_APP, HOTEL_CALLOUT, PRICE, PROMOTION, AD_IMAGE, LEAD_FORM, BUSINESS_LOGO"],
) -> str:
    """Link an asset (extension) to a campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignAssetService")

        operation = client.get_type("CampaignAssetOperation")
        campaign_asset = operation.create
        campaign_asset.campaign = f"customers/{cid}/campaigns/{campaign_id}"
        campaign_asset.asset = f"customers/{cid}/assets/{asset_id}"
        validate_enum_value(field_type, "field_type")
        campaign_asset.field_type = getattr(client.enums.AssetFieldTypeEnum, field_type)

        response = service.mutate_campaign_assets(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Asset {asset_id} linked to campaign {campaign_id} as {field_type}",
        )
    except Exception as e:
        logger.error("Failed to link asset to campaign: %s", e, exc_info=True)
        return error_response(f"Failed to link asset to campaign: {e}")


@mcp.tool()
def link_asset_to_ad_group(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    asset_id: Annotated[str, "The asset ID to link"],
    field_type: Annotated[str, "Asset field type: SITELINK, CALLOUT, STRUCTURED_SNIPPET, CALL, MOBILE_APP, PRICE, PROMOTION, AD_IMAGE, LEAD_FORM"],
) -> str:
    """Link an asset (extension) to an ad group."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupAssetService")

        operation = client.get_type("AdGroupAssetOperation")
        ad_group_asset = operation.create
        ad_group_asset.ad_group = f"customers/{cid}/adGroups/{ad_group_id}"
        ad_group_asset.asset = f"customers/{cid}/assets/{asset_id}"
        validate_enum_value(field_type, "field_type")
        ad_group_asset.field_type = getattr(client.enums.AssetFieldTypeEnum, field_type)

        response = service.mutate_ad_group_assets(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Asset {asset_id} linked to ad group {ad_group_id} as {field_type}",
        )
    except Exception as e:
        logger.error("Failed to link asset to ad group: %s", e, exc_info=True)
        return error_response(f"Failed to link asset to ad group: {e}")


@mcp.tool()
def unlink_asset(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    resource_name: Annotated[str, "Full resource name of the asset link (e.g., customers/123/campaignAssets/456~789~SITELINK or customers/123/customerAssets/456~SITELINK)"],
    resource_type: Annotated[str, "Type: campaign, ad_group, or customer"] = "campaign",
) -> str:
    """Unlink an asset from a campaign, ad group, or customer (account level).

    Use the resource_name from the link (not the asset itself).
    For customer-level: customers/{id}/customerAssets/{asset_id}~{FIELD_TYPE}
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()

        if resource_type == "campaign":
            service = get_service("CampaignAssetService")
            operation = client.get_type("CampaignAssetOperation")
            operation.remove = resource_name
            response = service.mutate_campaign_assets(customer_id=cid, operations=[operation])
        elif resource_type == "customer":
            service = get_service("CustomerAssetService")
            operation = client.get_type("CustomerAssetOperation")
            operation.remove = resource_name
            response = service.mutate_customer_assets(customer_id=cid, operations=[operation])
        else:
            service = get_service("AdGroupAssetService")
            operation = client.get_type("AdGroupAssetOperation")
            operation.remove = resource_name
            response = service.mutate_ad_group_assets(customer_id=cid, operations=[operation])

        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Asset unlinked from {resource_type}",
        )
    except Exception as e:
        logger.error("Failed to unlink asset: %s", e, exc_info=True)
        return error_response(f"Failed to unlink asset: {e}")


@mcp.tool()
def unlink_customer_assets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    asset_ids: Annotated[list[str], "List of asset IDs to unlink from account level"],
    field_type: Annotated[str, "Asset field type: SITELINK, CALLOUT, STRUCTURED_SNIPPET, CALL, etc."] = "SITELINK",
) -> str:
    """Unlink multiple assets from the account (customer) level in batch.

    This removes customer_asset links, stopping account-level assets from
    propagating to campaigns that don't have their own assets of this type.
    The assets themselves are NOT deleted, only the customer-level link is removed.

    Resource name format: customers/{customer_id}/customerAssets/{asset_id}~{FIELD_TYPE}
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()

        error = validate_batch(asset_ids, max_size=5000, item_name="asset_ids")
        if error:
            return error_response(error)

        validate_enum_value(field_type, "field_type")
        service = get_service("CustomerAssetService")

        operations = []
        for asset_id in asset_ids:
            operation = client.get_type("CustomerAssetOperation")
            operation.remove = f"customers/{cid}/customerAssets/{asset_id}~{field_type}"
            operations.append(operation)

        response = service.mutate_customer_assets(customer_id=cid, operations=operations)
        results = [r.resource_name for r in response.results]
        return success_response(
            {"unlinked": len(results), "resource_names": results},
            message=f"{len(results)} assets unlinked from account level",
        )
    except Exception as e:
        logger.error("Failed to unlink customer assets: %s", e, exc_info=True)
        return error_response(f"Failed to unlink customer assets: {e}")
