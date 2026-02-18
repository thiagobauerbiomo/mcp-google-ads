"""Campaign management tools (9 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from google.api_core import protobuf_helpers

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import (
    error_response,
    format_micros,
    resolve_customer_id,
    success_response,
    to_micros,
    validate_enum_value,
    validate_limit,
    validate_numeric_id,
    validate_status,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def list_campaigns(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    status_filter: Annotated[str | None, "Filter by status: ENABLED, PAUSED, REMOVED. None for all."] = None,
    limit: Annotated[int, "Maximum number of results"] = 100,
) -> str:
    """List campaigns for a customer account.

    Returns campaign ID, name, status, type, bidding strategy, and budget info.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        where = ""
        if status_filter:
            safe_status = validate_status(status_filter)
            where = f"WHERE campaign.status = '{safe_status}'"

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.bidding_strategy_type,
                campaign_budget.amount_micros
            FROM campaign
            {where}
            ORDER BY campaign.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        campaigns = []
        for row in response:
            campaigns.append({
                "campaign_id": str(row.campaign.id),
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "channel_type": row.campaign.advertising_channel_type.name,
                "bidding_strategy": row.campaign.bidding_strategy_type.name,
                "budget_micros": row.campaign_budget.amount_micros,
                "budget": format_micros(row.campaign_budget.amount_micros),
            })
        return success_response({"campaigns": campaigns, "count": len(campaigns)})
    except Exception as e:
        logger.error("Failed to list campaigns: %s", e, exc_info=True)
        return error_response(f"Failed to list campaigns: {e}")


@mcp.tool()
def get_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
) -> str:
    """Get detailed information about a specific campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_id = validate_numeric_id(campaign_id, "campaign_id")
        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.advertising_channel_sub_type,
                campaign.bidding_strategy_type,
                campaign.bidding_strategy,
                campaign_budget.amount_micros,
                campaign_budget.delivery_method,
                campaign.serving_status,
                campaign.network_settings.target_google_search,
                campaign.network_settings.target_search_network,
                campaign.network_settings.target_content_network,
                campaign.geo_target_type_setting.positive_geo_target_type,
                campaign.url_custom_parameters
            FROM campaign
            WHERE campaign.id = {safe_id}
        """
        response = service.search(customer_id=cid, query=query)
        for row in response:
            data = {
                "campaign_id": str(row.campaign.id),
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "channel_type": row.campaign.advertising_channel_type.name,
                "channel_sub_type": row.campaign.advertising_channel_sub_type.name,
                "bidding_strategy_type": row.campaign.bidding_strategy_type.name,
                "budget_micros": row.campaign_budget.amount_micros,
                "budget": format_micros(row.campaign_budget.amount_micros),
                "budget_delivery": row.campaign_budget.delivery_method.name,
                "serving_status": row.campaign.serving_status.name,
                "target_google_search": row.campaign.network_settings.target_google_search,
                "target_search_network": row.campaign.network_settings.target_search_network,
                "target_content_network": row.campaign.network_settings.target_content_network,
            }
            return success_response(data)
        return error_response(f"Campaign {campaign_id} not found")
    except Exception as e:
        logger.error("Failed to get campaign: %s", e, exc_info=True)
        return error_response(f"Failed to get campaign: {e}")


@mcp.tool()
def create_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Campaign name"],
    budget_amount: Annotated[float, "Daily budget in account currency"],
    channel_type: Annotated[str, "Channel type: SEARCH, DISPLAY, SHOPPING, VIDEO, PERFORMANCE_MAX"] = "SEARCH",
    bidding_strategy: Annotated[str, "Bidding strategy: MANUAL_CPC, MAXIMIZE_CLICKS, MAXIMIZE_CONVERSIONS, TARGET_CPA, TARGET_ROAS"] = "MANUAL_CPC",
    target_cpa_micros: Annotated[int | None, "Target CPA in micros (for TARGET_CPA strategy)"] = None,
    target_roas: Annotated[float | None, "Target ROAS (for TARGET_ROAS strategy, e.g., 3.0 for 300%)"] = None,
    cpc_bid_ceiling_micros: Annotated[int | None, "Max CPC ceiling in micros for MAXIMIZE_CLICKS (e.g., 4000000 for R$4.00)"] = None,
    network_search: Annotated[bool, "Target Google Search"] = True,
    network_search_partners: Annotated[bool, "Target Search Partners"] = False,
    network_display: Annotated[bool, "Target Display Network"] = False,
) -> str:
    """Create a new campaign. Campaign is created PAUSED by default for safety.

    Use set_campaign_status to enable it after reviewing settings.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        campaign_service = get_service("CampaignService")
        budget_service = get_service("CampaignBudgetService")

        # Create budget
        budget_op = client.get_type("CampaignBudgetOperation")
        budget = budget_op.create
        budget.name = f"Budget for {name}"
        budget.amount_micros = to_micros(budget_amount)
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget.explicitly_shared = False

        budget_response = budget_service.mutate_campaign_budgets(
            customer_id=cid, operations=[budget_op]
        )
        budget_rn = budget_response.results[0].resource_name

        # Create campaign
        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.create
        campaign.name = name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
        campaign.campaign_budget = budget_rn
        validate_enum_value(channel_type, "channel_type")
        campaign.advertising_channel_type = getattr(
            client.enums.AdvertisingChannelTypeEnum, channel_type
        )

        # EU political advertising (required field — DOES_NOT_CONTAIN = 3)
        campaign.contains_eu_political_advertising = 3

        # Bidding strategy
        validate_enum_value(bidding_strategy, "bidding_strategy")
        if bidding_strategy == "MANUAL_CPC":
            campaign.manual_cpc.enhanced_cpc_enabled = False
        elif bidding_strategy in ("MAXIMIZE_CLICKS", "TARGET_SPEND"):
            if cpc_bid_ceiling_micros:
                campaign.target_spend.cpc_bid_ceiling_micros = cpc_bid_ceiling_micros
            else:
                client.copy_from(
                    campaign.target_spend,
                    client.get_type("TargetSpend")(),
                )
        elif bidding_strategy == "MAXIMIZE_CONVERSIONS":
            if target_cpa_micros:
                campaign.maximize_conversions.target_cpa_micros = target_cpa_micros
            else:
                client.copy_from(
                    campaign.maximize_conversions,
                    client.get_type("MaximizeConversions")(),
                )
        elif bidding_strategy == "TARGET_CPA":
            campaign.target_cpa.target_cpa_micros = target_cpa_micros or 0
        elif bidding_strategy == "TARGET_ROAS":
            campaign.target_roas.target_roas = target_roas or 0.0

        # Network settings
        campaign.network_settings.target_google_search = network_search
        campaign.network_settings.target_search_network = network_search_partners
        campaign.network_settings.target_content_network = network_display

        response = campaign_service.mutate_campaigns(
            customer_id=cid, operations=[campaign_op]
        )
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"campaign_id": new_id, "resource_name": resource_name, "status": "PAUSED"},
            message=f"Campaign '{name}' created as PAUSED",
        )
    except Exception as e:
        logger.error("Failed to create campaign: %s", e, exc_info=True)
        return error_response(f"Failed to create campaign: {e}")


@mcp.tool()
def update_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID to update"],
    name: Annotated[str | None, "New campaign name"] = None,
    start_date: Annotated[str | None, "Start date (YYYY-MM-DD)"] = None,
    end_date: Annotated[str | None, "End date (YYYY-MM-DD)"] = None,
    network_search: Annotated[bool | None, "Target Google Search"] = None,
    network_search_partners: Annotated[bool | None, "Target Search Partners"] = None,
    network_display: Annotated[bool | None, "Target Display Network"] = None,
) -> str:
    """Update an existing campaign's settings (name, dates, networks)."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignService")

        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.update
        campaign.resource_name = f"customers/{cid}/campaigns/{campaign_id}"

        update_mask_fields = []

        if name is not None:
            campaign.name = name
            update_mask_fields.append("name")
        if start_date is not None:
            campaign.start_date = start_date
            update_mask_fields.append("start_date")
        if end_date is not None:
            campaign.end_date = end_date
            update_mask_fields.append("end_date")
        if network_search is not None:
            campaign.network_settings.target_google_search = network_search
            update_mask_fields.append("network_settings.target_google_search")
        if network_search_partners is not None:
            campaign.network_settings.target_search_network = network_search_partners
            update_mask_fields.append("network_settings.target_search_network")
        if network_display is not None:
            campaign.network_settings.target_content_network = network_display
            update_mask_fields.append("network_settings.target_content_network")

        if not update_mask_fields:
            return error_response("No fields to update")

        protobuf_helpers.field_mask_pb2.FieldMask(paths=update_mask_fields)
        client.copy_from(
            campaign_op.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=update_mask_fields),
        )

        response = service.mutate_campaigns(customer_id=cid, operations=[campaign_op])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Campaign {campaign_id} updated",
        )
    except Exception as e:
        logger.error("Failed to update campaign: %s", e, exc_info=True)
        return error_response(f"Failed to update campaign: {e}")


@mcp.tool()
def set_campaign_status(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    status: Annotated[str, "New status: ENABLED, PAUSED, or REMOVED"],
) -> str:
    """Enable, pause, or remove a campaign.

    WARNING: Setting to ENABLED will start spending budget. Setting to REMOVED is permanent.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_status = validate_status(status)
        client = get_client()
        service = get_service("CampaignService")

        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.update
        campaign.resource_name = f"customers/{cid}/campaigns/{campaign_id}"
        campaign.status = getattr(client.enums.CampaignStatusEnum, safe_status)

        client.copy_from(
            campaign_op.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=["status"]),
        )

        response = service.mutate_campaigns(customer_id=cid, operations=[campaign_op])
        return success_response(
            {"resource_name": response.results[0].resource_name, "new_status": safe_status},
            message=f"Campaign {campaign_id} set to {safe_status}",
        )
    except Exception as e:
        logger.error("Failed to set campaign status: %s", e, exc_info=True)
        return error_response(f"Failed to set campaign status: {e}")


@mcp.tool()
def remove_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID to remove"],
) -> str:
    """Remove (delete) a campaign permanently. This action cannot be undone."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignService")

        campaign_op = client.get_type("CampaignOperation")
        campaign_op.remove = f"customers/{cid}/campaigns/{campaign_id}"

        response = service.mutate_campaigns(customer_id=cid, operations=[campaign_op])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Campaign {campaign_id} removed permanently",
        )
    except Exception as e:
        logger.error("Failed to remove campaign: %s", e, exc_info=True)
        return error_response(f"Failed to remove campaign: {e}")


@mcp.tool()
def list_campaign_labels(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """List labels associated with campaigns."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        where = ""
        if campaign_id:
            safe_id = validate_numeric_id(campaign_id, "campaign_id")
            where = f"WHERE campaign.id = {safe_id}"

        query = f"""
            SELECT
                campaign_label.campaign,
                campaign_label.label,
                label.id,
                label.name,
                campaign.id,
                campaign.name
            FROM campaign_label
            {where}
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        labels = []
        for row in response:
            labels.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "label_id": str(row.label.id),
                "label_name": row.label.name,
            })
        return success_response({"labels": labels, "count": len(labels)})
    except Exception as e:
        logger.error("Failed to list campaign labels: %s", e, exc_info=True)
        return error_response(f"Failed to list campaign labels: {e}")


@mcp.tool()
def set_campaign_tracking_template(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    tracking_template: Annotated[str, "Tracking URL template with ValueTrack parameters. Example: {lpurl}?utm_source=google&utm_medium=cpc&utm_campaign={_campaign}"],
    custom_parameters: Annotated[list[dict] | None, "List of {key, value} custom parameters for {_key} placeholders"] = None,
) -> str:
    """Set a tracking URL template on a campaign for UTM/analytics tracking.

    The template applies to all ads in the campaign unless overridden at ad group or ad level.
    Use {lpurl} as the landing page placeholder. Example:
    {lpurl}?utm_source=google&utm_medium=cpc&utm_campaign={_campaign}&utm_content={_adgroup}
    Custom parameters: [{"key": "campaign", "value": "my_campaign_name"}]
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_id = validate_numeric_id(campaign_id, "campaign_id")
        client = get_client()
        service = get_service("CampaignService")

        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.update
        campaign.resource_name = f"customers/{cid}/campaigns/{safe_id}"
        campaign.tracking_url_template = tracking_template

        fields = ["tracking_url_template"]

        if custom_parameters:
            for param in custom_parameters:
                custom_param = client.get_type("CustomParameter")
                custom_param.key = param["key"]
                custom_param.value = param["value"]
                campaign.url_custom_parameters.append(custom_param)
            fields.append("url_custom_parameters")

        client.copy_from(
            campaign_op.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=fields),
        )

        response = service.mutate_campaigns(customer_id=cid, operations=[campaign_op])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Tracking template set on campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to set campaign tracking template: %s", e, exc_info=True)
        return error_response(f"Failed to set campaign tracking template: {e}")


@mcp.tool()
def clone_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    source_campaign_id: Annotated[str, "The campaign ID to clone"],
    new_name: Annotated[str | None, "Name for the cloned campaign. Defaults to original name + ' [Clone]'"] = None,
    budget_amount: Annotated[float | None, "Daily budget for clone (in account currency). Defaults to same as source."] = None,
    copy_ad_groups: Annotated[bool, "Whether to copy ad groups with keywords"] = True,
) -> str:
    """Clone an entire campaign with its ad groups, keywords, and settings.

    Creates a new PAUSED campaign with the same configuration. Ad groups are also created PAUSED.
    Does NOT copy ads (they need to be created fresh for proper A/B testing).
    Use clone_ad_group for more granular control over individual ad groups.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_source = validate_numeric_id(source_campaign_id, "source_campaign_id")
        client = get_client()
        search_service = get_service("GoogleAdsService")

        # 1. Get source campaign details
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.advertising_channel_type,
                campaign.bidding_strategy_type,
                campaign.network_settings.target_google_search,
                campaign.network_settings.target_search_network,
                campaign.network_settings.target_content_network,
                campaign_budget.amount_micros
            FROM campaign
            WHERE campaign.id = {safe_source}
        """
        response = search_service.search(customer_id=cid, query=query)
        source = None
        for row in response:
            source = row
        if source is None:
            return error_response(f"Source campaign {source_campaign_id} not found")

        clone_name = new_name or f"{source.campaign.name} [Clone]"
        budget_micros = to_micros(budget_amount) if budget_amount else source.campaign_budget.amount_micros

        # 2. Create budget
        budget_service = get_service("CampaignBudgetService")
        budget_op = client.get_type("CampaignBudgetOperation")
        budget = budget_op.create
        budget.name = f"Budget for {clone_name}"
        budget.amount_micros = budget_micros
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget.explicitly_shared = False
        budget_response = budget_service.mutate_campaign_budgets(customer_id=cid, operations=[budget_op])
        budget_rn = budget_response.results[0].resource_name

        # 3. Create campaign
        campaign_service = get_service("CampaignService")
        campaign_op = client.get_type("CampaignOperation")
        new_campaign = campaign_op.create
        new_campaign.name = clone_name
        new_campaign.status = client.enums.CampaignStatusEnum.PAUSED
        new_campaign.campaign_budget = budget_rn
        new_campaign.advertising_channel_type = source.campaign.advertising_channel_type
        new_campaign.network_settings.target_google_search = source.campaign.network_settings.target_google_search
        new_campaign.network_settings.target_search_network = source.campaign.network_settings.target_search_network
        new_campaign.network_settings.target_content_network = source.campaign.network_settings.target_content_network

        # Copy bidding strategy
        bst = source.campaign.bidding_strategy_type.name
        if bst == "MANUAL_CPC":
            new_campaign.manual_cpc.enhanced_cpc_enabled = False
        elif bst in ("MAXIMIZE_CLICKS", "TARGET_SPEND"):
            client.copy_from(new_campaign.target_spend, client.get_type("TargetSpend")())
        elif bst == "MAXIMIZE_CONVERSIONS":
            client.copy_from(new_campaign.maximize_conversions, client.get_type("MaximizeConversions")())

        campaign_response = campaign_service.mutate_campaigns(customer_id=cid, operations=[campaign_op])
        new_campaign_rn = campaign_response.results[0].resource_name
        new_campaign_id = new_campaign_rn.split("/")[-1]

        cloned_ad_groups = 0

        # 4. Clone ad groups if requested
        if copy_ad_groups:
            ag_query = f"""
                SELECT
                    ad_group.id,
                    ad_group.name,
                    ad_group.type,
                    ad_group.cpc_bid_micros
                FROM ad_group
                WHERE campaign.id = {safe_source}
                    AND ad_group.status != 'REMOVED'
            """
            ag_response = search_service.search(customer_id=cid, query=ag_query)
            ag_service = get_service("AdGroupService")

            for ag_row in ag_response:
                # Create ad group
                ag_op = client.get_type("AdGroupOperation")
                new_ag = ag_op.create
                new_ag.name = ag_row.ad_group.name
                new_ag.status = client.enums.AdGroupStatusEnum.PAUSED
                new_ag.campaign = f"customers/{cid}/campaigns/{new_campaign_id}"
                new_ag.type_ = ag_row.ad_group.type_
                if ag_row.ad_group.cpc_bid_micros:
                    new_ag.cpc_bid_micros = ag_row.ad_group.cpc_bid_micros

                ag_result = ag_service.mutate_ad_groups(customer_id=cid, operations=[ag_op])
                new_ag_id = ag_result.results[0].resource_name.split("/")[-1]

                # Copy keywords
                kw_query = f"""
                    SELECT
                        ad_group_criterion.keyword.text,
                        ad_group_criterion.keyword.match_type,
                        ad_group_criterion.cpc_bid_micros,
                        ad_group_criterion.negative
                    FROM ad_group_criterion
                    WHERE ad_group.id = {ag_row.ad_group.id}
                        AND ad_group_criterion.type = 'KEYWORD'
                        AND ad_group_criterion.status != 'REMOVED'
                    LIMIT 5000
                """
                kw_response = search_service.search(customer_id=cid, query=kw_query)
                kw_service = get_service("AdGroupCriterionService")
                kw_ops = []
                for kw_row in kw_response:
                    op = client.get_type("AdGroupCriterionOperation")
                    criterion = op.create
                    criterion.ad_group = f"customers/{cid}/adGroups/{new_ag_id}"
                    criterion.keyword.text = kw_row.ad_group_criterion.keyword.text
                    criterion.keyword.match_type = kw_row.ad_group_criterion.keyword.match_type
                    criterion.negative = kw_row.ad_group_criterion.negative
                    if not kw_row.ad_group_criterion.negative:
                        criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
                    if kw_row.ad_group_criterion.cpc_bid_micros:
                        criterion.cpc_bid_micros = kw_row.ad_group_criterion.cpc_bid_micros
                    kw_ops.append(op)

                if kw_ops:
                    kw_service.mutate_ad_group_criteria(customer_id=cid, operations=kw_ops)

                cloned_ad_groups += 1

        return success_response(
            {
                "new_campaign_id": new_campaign_id,
                "resource_name": new_campaign_rn,
                "status": "PAUSED",
                "budget": format_micros(budget_micros),
                "cloned_ad_groups": cloned_ad_groups,
            },
            message=f"Campaign cloned as '{clone_name}' (PAUSED) with {cloned_ad_groups} ad groups",
        )
    except Exception as e:
        logger.error("Failed to clone campaign: %s", e, exc_info=True)
        return error_response(f"Failed to clone campaign: {e}")
