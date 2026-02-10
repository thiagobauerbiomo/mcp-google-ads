"""Campaign type creation tools — Performance Max, Display, Video, Shopping, Demand Gen, App (8 tools)."""

from __future__ import annotations

from typing import Annotated

from google.api_core import protobuf_helpers

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response, to_micros, validate_numeric_id


@mcp.tool()
def create_performance_max_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Campaign name"],
    budget_amount: Annotated[float, "Daily budget in account currency"],
    final_url: Annotated[str, "Final URL for the asset group"],
    asset_group_name: Annotated[str, "Name for the asset group"],
    headlines: Annotated[list[str], "3-15 headline texts (max 30 chars each)"],
    descriptions: Annotated[list[str], "2-5 description texts (max 90 chars each)"],
    long_headlines: Annotated[list[str], "1-5 long headline texts (max 90 chars each)"],
    business_name: Annotated[str, "Business name"],
    bidding_strategy: Annotated[str, "MAXIMIZE_CONVERSIONS or MAXIMIZE_CONVERSION_VALUE"] = "MAXIMIZE_CONVERSIONS",
    target_cpa_micros: Annotated[int | None, "Target CPA in micros (for MAXIMIZE_CONVERSIONS)"] = None,
    target_roas: Annotated[float | None, "Target ROAS (for MAXIMIZE_CONVERSION_VALUE, e.g., 3.0 for 300%)"] = None,
) -> str:
    """Create a Performance Max campaign with an asset group and text assets.

    Created PAUSED by default. PMax campaigns use all Google channels (Search, Display, YouTube, Gmail, Maps, Discover).
    Requires at least 3 headlines, 2 descriptions, and 1 long headline.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()

        operations = []

        # 1. Create budget
        budget_op = client.get_type("MutateOperation")
        budget = budget_op.campaign_budget_operation.create
        budget.name = f"Budget for PMax - {name}"
        budget.amount_micros = to_micros(budget_amount)
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget.explicitly_shared = False
        temp_budget_rn = f"customers/{cid}/campaignBudgets/-1"
        budget.resource_name = temp_budget_rn
        operations.append(budget_op)

        # 2. Create campaign
        campaign_op = client.get_type("MutateOperation")
        campaign = campaign_op.campaign_operation.create
        campaign.name = name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
        campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
        campaign.campaign_budget = temp_budget_rn

        if bidding_strategy == "MAXIMIZE_CONVERSIONS":
            campaign.maximize_conversions.target_cpa_micros = target_cpa_micros or 0
        elif bidding_strategy == "MAXIMIZE_CONVERSION_VALUE":
            campaign.maximize_conversion_value.target_roas = target_roas or 0.0

        temp_campaign_rn = f"customers/{cid}/campaigns/-2"
        campaign.resource_name = temp_campaign_rn
        operations.append(campaign_op)

        # 3. Create asset group
        asset_group_op = client.get_type("MutateOperation")
        asset_group = asset_group_op.asset_group_operation.create
        asset_group.name = asset_group_name
        asset_group.campaign = temp_campaign_rn
        asset_group.status = client.enums.AssetGroupStatusEnum.PAUSED
        asset_group.final_urls.append(final_url)
        temp_ag_rn = f"customers/{cid}/assetGroups/-3"
        asset_group.resource_name = temp_ag_rn
        operations.append(asset_group_op)

        # 4. Create text assets and link them
        asset_counter = -4

        for headline in headlines:
            asset_op = client.get_type("MutateOperation")
            asset = asset_op.asset_operation.create
            asset.text_asset.text = headline
            temp_asset_rn = f"customers/{cid}/assets/{asset_counter}"
            asset.resource_name = temp_asset_rn
            operations.append(asset_op)

            link_op = client.get_type("MutateOperation")
            link = link_op.asset_group_asset_operation.create
            link.asset_group = temp_ag_rn
            link.asset = temp_asset_rn
            link.field_type = client.enums.AssetFieldTypeEnum.HEADLINE
            operations.append(link_op)
            asset_counter -= 1

        for desc in descriptions:
            asset_op = client.get_type("MutateOperation")
            asset = asset_op.asset_operation.create
            asset.text_asset.text = desc
            temp_asset_rn = f"customers/{cid}/assets/{asset_counter}"
            asset.resource_name = temp_asset_rn
            operations.append(asset_op)

            link_op = client.get_type("MutateOperation")
            link = link_op.asset_group_asset_operation.create
            link.asset_group = temp_ag_rn
            link.asset = temp_asset_rn
            link.field_type = client.enums.AssetFieldTypeEnum.DESCRIPTION
            operations.append(link_op)
            asset_counter -= 1

        for long_headline in long_headlines:
            asset_op = client.get_type("MutateOperation")
            asset = asset_op.asset_operation.create
            asset.text_asset.text = long_headline
            temp_asset_rn = f"customers/{cid}/assets/{asset_counter}"
            asset.resource_name = temp_asset_rn
            operations.append(asset_op)

            link_op = client.get_type("MutateOperation")
            link = link_op.asset_group_asset_operation.create
            link.asset_group = temp_ag_rn
            link.asset = temp_asset_rn
            link.field_type = client.enums.AssetFieldTypeEnum.LONG_HEADLINE
            operations.append(link_op)
            asset_counter -= 1

        # Business name asset
        bn_op = client.get_type("MutateOperation")
        bn_asset = bn_op.asset_operation.create
        bn_asset.text_asset.text = business_name
        temp_bn_rn = f"customers/{cid}/assets/{asset_counter}"
        bn_asset.resource_name = temp_bn_rn
        operations.append(bn_op)

        bn_link_op = client.get_type("MutateOperation")
        bn_link = bn_link_op.asset_group_asset_operation.create
        bn_link.asset_group = temp_ag_rn
        bn_link.asset = temp_bn_rn
        bn_link.field_type = client.enums.AssetFieldTypeEnum.BUSINESS_NAME
        operations.append(bn_link_op)

        # 5. Create listing group filter (required for PMax)
        lg_op = client.get_type("MutateOperation")
        listing_group = lg_op.asset_group_listing_group_filter_operation.create
        listing_group.asset_group = temp_ag_rn
        listing_group.type_ = client.enums.ListingGroupFilterTypeEnum.UNIT_INCLUDED
        operations.append(lg_op)

        # Execute batch
        gads_service = get_service("GoogleAdsService")
        response = gads_service.mutate(customer_id=cid, mutate_operations=operations)

        campaign_rn = response.mutate_operation_responses[1].campaign_result.resource_name
        campaign_id = campaign_rn.split("/")[-1]

        return success_response(
            {
                "campaign_id": campaign_id,
                "campaign_resource_name": campaign_rn,
                "status": "PAUSED",
                "operations_count": len(operations),
            },
            message=f"Performance Max campaign '{name}' created as PAUSED with asset group",
        )
    except Exception as e:
        return error_response(f"Failed to create Performance Max campaign: {e}")


@mcp.tool()
def list_asset_groups(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    limit: Annotated[int, "Maximum number of results"] = 100,
) -> str:
    """List asset groups, optionally filtered by campaign.

    Asset groups are used in Performance Max campaigns to organize assets.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        campaign_filter = f"WHERE campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}" if campaign_id else ""

        query = f"""
            SELECT
                asset_group.id,
                asset_group.name,
                asset_group.status,
                asset_group.final_urls,
                asset_group.final_mobile_urls,
                campaign.id,
                campaign.name
            FROM asset_group
            {campaign_filter}
            ORDER BY asset_group.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        groups = []
        for row in response:
            groups.append({
                "asset_group_id": str(row.asset_group.id),
                "name": row.asset_group.name,
                "status": row.asset_group.status.name,
                "final_urls": list(row.asset_group.final_urls),
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
            })
        return success_response({"asset_groups": groups, "count": len(groups)})
    except Exception as e:
        return error_response(f"Failed to list asset groups: {e}")


@mcp.tool()
def update_asset_group(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    asset_group_id: Annotated[str, "The asset group ID"],
    name: Annotated[str | None, "New name"] = None,
    status: Annotated[str | None, "New status: ENABLED, PAUSED"] = None,
    final_url: Annotated[str | None, "New final URL (replaces existing)"] = None,
) -> str:
    """Update an asset group's name, status, or final URL."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetGroupService")

        operation = client.get_type("AssetGroupOperation")
        asset_group = operation.update
        asset_group.resource_name = f"customers/{cid}/assetGroups/{asset_group_id}"

        fields = []
        if name is not None:
            asset_group.name = name
            fields.append("name")
        if status is not None:
            asset_group.status = getattr(client.enums.AssetGroupStatusEnum, status)
            fields.append("status")
        if final_url is not None:
            asset_group.final_urls.append(final_url)
            fields.append("final_urls")

        if not fields:
            return error_response("No fields to update")

        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=fields),
        )

        response = service.mutate_asset_groups(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Asset group {asset_group_id} updated",
        )
    except Exception as e:
        return error_response(f"Failed to update asset group: {e}")


@mcp.tool()
def create_display_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Campaign name"],
    budget_amount: Annotated[float, "Daily budget in account currency"],
    bidding_strategy: Annotated[str, "MANUAL_CPC, MAXIMIZE_CLICKS, MAXIMIZE_CONVERSIONS, TARGET_CPA"] = "MAXIMIZE_CLICKS",
    target_cpa_micros: Annotated[int | None, "Target CPA in micros (for TARGET_CPA)"] = None,
) -> str:
    """Create a Display Network campaign. Created PAUSED by default.

    Display campaigns show image/responsive ads across the Google Display Network.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        budget_service = get_service("CampaignBudgetService")
        campaign_service = get_service("CampaignService")

        budget_op = client.get_type("CampaignBudgetOperation")
        budget = budget_op.create
        budget.name = f"Budget for Display - {name}"
        budget.amount_micros = to_micros(budget_amount)
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget_response = budget_service.mutate_campaign_budgets(customer_id=cid, operations=[budget_op])
        budget_rn = budget_response.results[0].resource_name

        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.create
        campaign.name = name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
        campaign.campaign_budget = budget_rn
        campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.DISPLAY

        if bidding_strategy == "MANUAL_CPC":
            campaign.manual_cpc.enhanced_cpc_enabled = False
        elif bidding_strategy == "MAXIMIZE_CLICKS":
            campaign.maximize_clicks.cpc_bid_ceiling_micros = 0
        elif bidding_strategy == "MAXIMIZE_CONVERSIONS":
            campaign.maximize_conversions.target_cpa_micros = target_cpa_micros or 0
        elif bidding_strategy == "TARGET_CPA":
            campaign.target_cpa.target_cpa_micros = target_cpa_micros or 0

        response = campaign_service.mutate_campaigns(customer_id=cid, operations=[campaign_op])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"campaign_id": new_id, "resource_name": resource_name, "status": "PAUSED"},
            message=f"Display campaign '{name}' created as PAUSED",
        )
    except Exception as e:
        return error_response(f"Failed to create Display campaign: {e}")


@mcp.tool()
def create_video_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Campaign name"],
    budget_amount: Annotated[float, "Daily budget in account currency"],
    bidding_strategy: Annotated[str, "MAXIMIZE_CONVERSIONS, TARGET_CPA, MAXIMIZE_CLICKS, MANUAL_CPV"] = "MAXIMIZE_CONVERSIONS",
    target_cpa_micros: Annotated[int | None, "Target CPA in micros"] = None,
) -> str:
    """Create a Video (YouTube) campaign. Created PAUSED by default."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        budget_service = get_service("CampaignBudgetService")
        campaign_service = get_service("CampaignService")

        budget_op = client.get_type("CampaignBudgetOperation")
        budget = budget_op.create
        budget.name = f"Budget for Video - {name}"
        budget.amount_micros = to_micros(budget_amount)
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget_response = budget_service.mutate_campaign_budgets(customer_id=cid, operations=[budget_op])
        budget_rn = budget_response.results[0].resource_name

        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.create
        campaign.name = name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
        campaign.campaign_budget = budget_rn
        campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.VIDEO

        if bidding_strategy == "MAXIMIZE_CONVERSIONS":
            campaign.maximize_conversions.target_cpa_micros = target_cpa_micros or 0
        elif bidding_strategy == "TARGET_CPA":
            campaign.target_cpa.target_cpa_micros = target_cpa_micros or 0
        elif bidding_strategy == "MAXIMIZE_CLICKS":
            campaign.maximize_clicks.cpc_bid_ceiling_micros = 0
        elif bidding_strategy == "MANUAL_CPV":
            pass  # manual_cpv has no fields to set

        response = campaign_service.mutate_campaigns(customer_id=cid, operations=[campaign_op])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"campaign_id": new_id, "resource_name": resource_name, "status": "PAUSED"},
            message=f"Video campaign '{name}' created as PAUSED",
        )
    except Exception as e:
        return error_response(f"Failed to create Video campaign: {e}")


@mcp.tool()
def create_shopping_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Campaign name"],
    budget_amount: Annotated[float, "Daily budget in account currency"],
    merchant_id: Annotated[str, "Google Merchant Center account ID"],
    country_code: Annotated[str, "Country of sale (e.g., 'BR', 'US')"] = "BR",
    priority: Annotated[int, "Campaign priority (0=low, 1=medium, 2=high)"] = 0,
    bidding_strategy: Annotated[str, "MANUAL_CPC, MAXIMIZE_CLICKS, TARGET_ROAS"] = "MANUAL_CPC",
    target_roas: Annotated[float | None, "Target ROAS (for TARGET_ROAS strategy)"] = None,
) -> str:
    """Create a Standard Shopping campaign. Created PAUSED by default.

    Requires a linked Google Merchant Center account with approved products.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        budget_service = get_service("CampaignBudgetService")
        campaign_service = get_service("CampaignService")

        budget_op = client.get_type("CampaignBudgetOperation")
        budget = budget_op.create
        budget.name = f"Budget for Shopping - {name}"
        budget.amount_micros = to_micros(budget_amount)
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget_response = budget_service.mutate_campaign_budgets(customer_id=cid, operations=[budget_op])
        budget_rn = budget_response.results[0].resource_name

        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.create
        campaign.name = name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
        campaign.campaign_budget = budget_rn
        campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SHOPPING

        campaign.shopping_setting.merchant_id = int(merchant_id)
        campaign.shopping_setting.sales_country = country_code
        campaign.shopping_setting.campaign_priority = priority

        if bidding_strategy == "MANUAL_CPC":
            campaign.manual_cpc.enhanced_cpc_enabled = False
        elif bidding_strategy == "MAXIMIZE_CLICKS":
            campaign.maximize_clicks.cpc_bid_ceiling_micros = 0
        elif bidding_strategy == "TARGET_ROAS":
            campaign.target_roas.target_roas = target_roas or 0.0

        response = campaign_service.mutate_campaigns(customer_id=cid, operations=[campaign_op])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"campaign_id": new_id, "resource_name": resource_name, "status": "PAUSED"},
            message=f"Shopping campaign '{name}' created as PAUSED",
        )
    except Exception as e:
        return error_response(f"Failed to create Shopping campaign: {e}")


@mcp.tool()
def create_demand_gen_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Campaign name"],
    budget_amount: Annotated[float, "Daily budget in account currency"],
    bidding_strategy: Annotated[str, "MAXIMIZE_CONVERSIONS, MAXIMIZE_CONVERSION_VALUE, TARGET_CPA"] = "MAXIMIZE_CONVERSIONS",
    target_cpa_micros: Annotated[int | None, "Target CPA in micros"] = None,
    target_roas: Annotated[float | None, "Target ROAS (for MAXIMIZE_CONVERSION_VALUE)"] = None,
) -> str:
    """Create a Demand Gen campaign. Created PAUSED by default.

    Demand Gen campaigns reach users across YouTube, Discover feed, and Gmail.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        budget_service = get_service("CampaignBudgetService")
        campaign_service = get_service("CampaignService")

        budget_op = client.get_type("CampaignBudgetOperation")
        budget = budget_op.create
        budget.name = f"Budget for Demand Gen - {name}"
        budget.amount_micros = to_micros(budget_amount)
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget_response = budget_service.mutate_campaign_budgets(customer_id=cid, operations=[budget_op])
        budget_rn = budget_response.results[0].resource_name

        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.create
        campaign.name = name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
        campaign.campaign_budget = budget_rn
        campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.DEMAND_GEN

        if bidding_strategy == "MAXIMIZE_CONVERSIONS":
            campaign.maximize_conversions.target_cpa_micros = target_cpa_micros or 0
        elif bidding_strategy == "TARGET_CPA":
            campaign.target_cpa.target_cpa_micros = target_cpa_micros or 0
        elif bidding_strategy == "MAXIMIZE_CONVERSION_VALUE":
            campaign.maximize_conversion_value.target_roas = target_roas or 0.0

        response = campaign_service.mutate_campaigns(customer_id=cid, operations=[campaign_op])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"campaign_id": new_id, "resource_name": resource_name, "status": "PAUSED"},
            message=f"Demand Gen campaign '{name}' created as PAUSED",
        )
    except Exception as e:
        return error_response(f"Failed to create Demand Gen campaign: {e}")


@mcp.tool()
def create_app_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Campaign name"],
    budget_amount: Annotated[float, "Daily budget in account currency"],
    app_id: Annotated[str, "App ID (package name for Android, numerical ID for iOS)"],
    app_store: Annotated[str, "App store: GOOGLE_APP_STORE or APPLE_APP_STORE"],
    bidding_strategy: Annotated[str, "TARGET_CPA or MAXIMIZE_CONVERSIONS"] = "TARGET_CPA",
    target_cpa_micros: Annotated[int | None, "Target CPA in micros"] = None,
) -> str:
    """Create an App campaign (Universal App Campaign). Created PAUSED by default.

    App campaigns promote your app across Search, Play, YouTube, and Display.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        budget_service = get_service("CampaignBudgetService")
        campaign_service = get_service("CampaignService")

        budget_op = client.get_type("CampaignBudgetOperation")
        budget = budget_op.create
        budget.name = f"Budget for App - {name}"
        budget.amount_micros = to_micros(budget_amount)
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget_response = budget_service.mutate_campaign_budgets(customer_id=cid, operations=[budget_op])
        budget_rn = budget_response.results[0].resource_name

        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.create
        campaign.name = name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
        campaign.campaign_budget = budget_rn
        campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.MULTI_CHANNEL
        campaign.advertising_channel_sub_type = client.enums.AdvertisingChannelSubTypeEnum.APP_CAMPAIGN

        campaign.app_campaign_setting.app_id = app_id
        campaign.app_campaign_setting.app_store = getattr(
            client.enums.AppCampaignAppStoreEnum, app_store
        )

        if bidding_strategy == "TARGET_CPA":
            campaign.target_cpa.target_cpa_micros = target_cpa_micros or 0
        elif bidding_strategy == "MAXIMIZE_CONVERSIONS":
            campaign.maximize_conversions.target_cpa_micros = target_cpa_micros or 0

        response = campaign_service.mutate_campaigns(customer_id=cid, operations=[campaign_op])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"campaign_id": new_id, "resource_name": resource_name, "status": "PAUSED"},
            message=f"App campaign '{name}' created as PAUSED",
        )
    except Exception as e:
        return error_response(f"Failed to create App campaign: {e}")
