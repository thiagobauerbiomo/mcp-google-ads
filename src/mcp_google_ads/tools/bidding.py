"""Bidding strategy management tools (12 tools)."""

from __future__ import annotations

import logging
import re
from typing import Annotated

from google.api_core import protobuf_helpers

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response, validate_limit, validate_numeric_id

logger = logging.getLogger(__name__)


@mcp.tool()
def list_bidding_strategies(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """List all portfolio bidding strategies for an account."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                bidding_strategy.id,
                bidding_strategy.name,
                bidding_strategy.type,
                bidding_strategy.status,
                bidding_strategy.campaign_count,
                bidding_strategy.effective_currency_code
            FROM bidding_strategy
            ORDER BY bidding_strategy.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        strategies = []
        for row in response:
            strategies.append({
                "strategy_id": str(row.bidding_strategy.id),
                "name": row.bidding_strategy.name,
                "type": row.bidding_strategy.type_.name,
                "status": row.bidding_strategy.status.name,
                "campaign_count": row.bidding_strategy.campaign_count,
                "currency": row.bidding_strategy.effective_currency_code,
            })
        return success_response({"strategies": strategies, "count": len(strategies)})
    except Exception as e:
        logger.error("Failed to list bidding strategies: %s", e, exc_info=True)
        return error_response(f"Failed to list bidding strategies: {e}")


@mcp.tool()
def get_bidding_strategy(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    strategy_id: Annotated[str, "The bidding strategy ID"],
) -> str:
    """Get detailed information about a specific bidding strategy."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                bidding_strategy.id,
                bidding_strategy.name,
                bidding_strategy.type,
                bidding_strategy.status,
                bidding_strategy.campaign_count,
                bidding_strategy.effective_currency_code,
                bidding_strategy.maximize_clicks.cpc_bid_ceiling_micros,
                bidding_strategy.maximize_conversions.target_cpa_micros,
                bidding_strategy.target_cpa.target_cpa_micros,
                bidding_strategy.target_roas.target_roas,
                bidding_strategy.target_roas.target_roas_tolerance_percent_millis,
                bidding_strategy.maximize_conversion_value.target_roas_tolerance_percent_millis,
                bidding_strategy.target_spend.cpc_bid_ceiling_micros,
                bidding_strategy.target_impression_share.location,
                bidding_strategy.target_impression_share.location_fraction_micros,
                bidding_strategy.target_impression_share.cpc_bid_ceiling_micros
            FROM bidding_strategy
            WHERE bidding_strategy.id = {validate_numeric_id(strategy_id, "strategy_id")}
        """
        response = service.search(customer_id=cid, query=query)
        for row in response:
            bs = row.bidding_strategy
            data = {
                "strategy_id": str(bs.id),
                "name": bs.name,
                "type": bs.type_.name,
                "status": bs.status.name,
                "campaign_count": bs.campaign_count,
                "currency": bs.effective_currency_code,
            }
            # Add type-specific fields
            if bs.type_.name == "TARGET_CPA":
                data["target_cpa_micros"] = bs.target_cpa.target_cpa_micros
            elif bs.type_.name == "TARGET_ROAS":
                data["target_roas"] = bs.target_roas.target_roas
                if bs.target_roas.target_roas_tolerance_percent_millis:
                    data["target_roas_tolerance_percent_millis"] = bs.target_roas.target_roas_tolerance_percent_millis
            elif bs.type_.name == "MAXIMIZE_CONVERSION_VALUE":
                if bs.maximize_conversion_value.target_roas_tolerance_percent_millis:
                    data["target_roas_tolerance_percent_millis"] = bs.maximize_conversion_value.target_roas_tolerance_percent_millis
            elif bs.type_.name == "MAXIMIZE_CLICKS":
                data["cpc_bid_ceiling_micros"] = bs.target_spend.cpc_bid_ceiling_micros
            elif bs.type_.name == "TARGET_IMPRESSION_SHARE":
                data["location"] = bs.target_impression_share.location.name
                data["location_fraction_micros"] = bs.target_impression_share.location_fraction_micros
                data["cpc_bid_ceiling_micros"] = bs.target_impression_share.cpc_bid_ceiling_micros

            return success_response(data)
        return error_response(f"Bidding strategy {strategy_id} not found")
    except Exception as e:
        logger.error("Failed to get bidding strategy: %s", e, exc_info=True)
        return error_response(f"Failed to get bidding strategy: {e}")


@mcp.tool()
def create_bidding_strategy(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Strategy name"],
    strategy_type: Annotated[str, "Type: MAXIMIZE_CLICKS, MAXIMIZE_CONVERSIONS, TARGET_CPA, TARGET_ROAS, TARGET_IMPRESSION_SHARE"],
    target_cpa_micros: Annotated[int | None, "Target CPA in micros (for TARGET_CPA)"] = None,
    target_roas: Annotated[float | None, "Target ROAS (for TARGET_ROAS, e.g. 3.0)"] = None,
    cpc_bid_ceiling_micros: Annotated[int | None, "Max CPC bid in micros"] = None,
    target_roas_tolerance_percent_millis: Annotated[int | None, "Smart Bidding Exploration tolerance in percent millis (e.g. 5000 = 5%). For TARGET_ROAS only."] = None,
) -> str:
    """Create a portfolio bidding strategy that can be shared across campaigns."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("BiddingStrategyService")

        operation = client.get_type("BiddingStrategyOperation")
        strategy = operation.create
        strategy.name = name

        if strategy_type == "MAXIMIZE_CLICKS":
            if cpc_bid_ceiling_micros:
                strategy.target_spend.cpc_bid_ceiling_micros = cpc_bid_ceiling_micros
            else:
                strategy.target_spend.cpc_bid_ceiling_micros = 0
        elif strategy_type == "MAXIMIZE_CONVERSIONS":
            strategy.maximize_conversions.target_cpa_micros = target_cpa_micros or 0
        elif strategy_type == "TARGET_CPA":
            strategy.target_cpa.target_cpa_micros = target_cpa_micros or 0
        elif strategy_type == "TARGET_ROAS":
            strategy.target_roas.target_roas = target_roas or 0.0
            if target_roas_tolerance_percent_millis is not None:
                strategy.target_roas.target_roas_tolerance_percent_millis = target_roas_tolerance_percent_millis
        elif strategy_type == "TARGET_IMPRESSION_SHARE":
            strategy.target_impression_share.location = (
                client.enums.TargetImpressionShareLocationEnum.ANYWHERE_ON_PAGE
            )
            if cpc_bid_ceiling_micros:
                strategy.target_impression_share.cpc_bid_ceiling_micros = cpc_bid_ceiling_micros
        else:
            return error_response(f"Unsupported strategy type: {strategy_type}")

        response = service.mutate_bidding_strategies(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"strategy_id": new_id, "resource_name": resource_name},
            message=f"Bidding strategy '{name}' ({strategy_type}) created",
        )
    except Exception as e:
        logger.error("Failed to create bidding strategy: %s", e, exc_info=True)
        return error_response(f"Failed to create bidding strategy: {e}")


@mcp.tool()
def update_bidding_strategy(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    strategy_id: Annotated[str, "The bidding strategy ID"],
    name: Annotated[str | None, "New name"] = None,
    target_cpa_micros: Annotated[int | None, "New target CPA in micros"] = None,
    target_roas: Annotated[float | None, "New target ROAS"] = None,
    cpc_bid_ceiling_micros: Annotated[int | None, "New max CPC bid in micros"] = None,
    target_roas_tolerance_percent_millis: Annotated[int | None, "Smart Bidding Exploration tolerance in percent millis (e.g. 5000 = 5%)"] = None,
) -> str:
    """Update a portfolio bidding strategy's settings."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("BiddingStrategyService")

        operation = client.get_type("BiddingStrategyOperation")
        strategy = operation.update
        strategy.resource_name = f"customers/{cid}/biddingStrategies/{strategy_id}"

        fields = []
        if name is not None:
            strategy.name = name
            fields.append("name")
        if target_cpa_micros is not None:
            strategy.target_cpa.target_cpa_micros = target_cpa_micros
            fields.append("target_cpa.target_cpa_micros")
        if target_roas is not None:
            strategy.target_roas.target_roas = target_roas
            fields.append("target_roas.target_roas")
        if cpc_bid_ceiling_micros is not None:
            strategy.target_spend.cpc_bid_ceiling_micros = cpc_bid_ceiling_micros
            fields.append("target_spend.cpc_bid_ceiling_micros")
        if target_roas_tolerance_percent_millis is not None:
            strategy.target_roas.target_roas_tolerance_percent_millis = target_roas_tolerance_percent_millis
            fields.append("target_roas.target_roas_tolerance_percent_millis")

        if not fields:
            return error_response("No fields to update")

        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=fields),
        )

        response = service.mutate_bidding_strategies(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Bidding strategy {strategy_id} updated",
        )
    except Exception as e:
        logger.error("Failed to update bidding strategy: %s", e, exc_info=True)
        return error_response(f"Failed to update bidding strategy: {e}")


@mcp.tool()
def set_campaign_bidding_strategy(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    strategy_id: Annotated[str, "The portfolio bidding strategy ID to assign"],
) -> str:
    """Assign a portfolio bidding strategy to a campaign."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignService")

        operation = client.get_type("CampaignOperation")
        campaign = operation.update
        campaign.resource_name = f"customers/{cid}/campaigns/{campaign_id}"
        campaign.bidding_strategy = f"customers/{cid}/biddingStrategies/{strategy_id}"

        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=["bidding_strategy"]),
        )

        response = service.mutate_campaigns(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Campaign {campaign_id} assigned to bidding strategy {strategy_id}",
        )
    except Exception as e:
        logger.error("Failed to set campaign bidding strategy: %s", e, exc_info=True)
        return error_response(f"Failed to set campaign bidding strategy: {e}")


_DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

_VALID_SCOPES = {"CAMPAIGN", "CHANNEL"}

_VALID_CHANNEL_TYPES = {
    "SEARCH", "DISPLAY", "SHOPPING", "VIDEO", "MULTI_CHANNEL",
    "LOCAL", "SMART", "PERFORMANCE_MAX", "LOCAL_SERVICES",
    "DISCOVERY", "TRAVEL", "DEMAND_GEN",
}


def _validate_datetime(value: str, field_name: str = "datetime") -> str:
    """Validate YYYY-MM-DD HH:MM:SS format."""
    if not _DATETIME_PATTERN.match(value):
        raise ValueError(f"{field_name} inválido: '{value}'. Formato esperado: YYYY-MM-DD HH:MM:SS")
    return value


def _validate_scope(scope: str) -> str:
    """Validate scope value."""
    upper = scope.upper()
    if upper not in _VALID_SCOPES:
        raise ValueError(f"Scope inválido: '{scope}'. Use: {_VALID_SCOPES}")
    return upper


def _validate_channel_types(channel_types: list[str]) -> list[str]:
    """Validate advertising channel types."""
    result = []
    for ct in channel_types:
        upper = ct.upper()
        if upper not in _VALID_CHANNEL_TYPES:
            raise ValueError(f"Channel type inválido: '{ct}'. Use: {_VALID_CHANNEL_TYPES}")
        result.append(upper)
    return result


@mcp.tool()
def list_bidding_data_exclusions(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """List bidding data exclusions for a customer account."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                bidding_data_exclusion.data_exclusion_id,
                bidding_data_exclusion.name,
                bidding_data_exclusion.status,
                bidding_data_exclusion.description,
                bidding_data_exclusion.start_date_time,
                bidding_data_exclusion.end_date_time,
                bidding_data_exclusion.scope,
                bidding_data_exclusion.advertising_channel_types,
                bidding_data_exclusion.campaigns
            FROM bidding_data_exclusion
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        exclusions = []
        for row in response:
            de = row.bidding_data_exclusion
            exclusions.append({
                "data_exclusion_id": str(de.data_exclusion_id),
                "name": de.name,
                "status": de.status.name,
                "description": de.description,
                "start_date_time": de.start_date_time,
                "end_date_time": de.end_date_time,
                "scope": de.scope.name,
                "advertising_channel_types": [ct.name for ct in de.advertising_channel_types],
                "campaigns": list(de.campaigns),
            })
        return success_response({"exclusions": exclusions, "count": len(exclusions)})
    except Exception as e:
        logger.error("Failed to list bidding data exclusions: %s", e, exc_info=True)
        return error_response(f"Failed to list bidding data exclusions: {e}")


@mcp.tool()
def create_bidding_data_exclusion(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Name of the data exclusion"],
    start_date_time: Annotated[str, "Start datetime in YYYY-MM-DD HH:MM:SS format"],
    end_date_time: Annotated[str, "End datetime in YYYY-MM-DD HH:MM:SS format"],
    scope: Annotated[str, "Scope: CAMPAIGN or CHANNEL"],
    campaign_ids: Annotated[list[str] | None, "List of campaign IDs (required when scope=CAMPAIGN)"] = None,
    advertising_channel_types: Annotated[list[str] | None, "Channel types like SEARCH, PERFORMANCE_MAX (required when scope=CHANNEL)"] = None,
    description: Annotated[str | None, "Optional description"] = None,
) -> str:
    """Create a bidding data exclusion to exclude a time period from Smart Bidding learning."""
    try:
        cid = resolve_customer_id(customer_id)
        _validate_datetime(start_date_time, "start_date_time")
        _validate_datetime(end_date_time, "end_date_time")
        validated_scope = _validate_scope(scope)

        client = get_client()
        service = get_service("BiddingDataExclusionService")

        operation = client.get_type("BiddingDataExclusionOperation")
        exclusion = operation.create
        exclusion.name = name
        exclusion.start_date_time = start_date_time
        exclusion.end_date_time = end_date_time

        scope_enum = client.enums.SeasonalityEventScopeEnum
        exclusion.scope = getattr(scope_enum, validated_scope)

        if description:
            exclusion.description = description

        if validated_scope == "CAMPAIGN":
            if not campaign_ids:
                return error_response("campaign_ids is required when scope=CAMPAIGN")
            for cmp_id in campaign_ids:
                validated_id = validate_numeric_id(cmp_id, "campaign_id")
                exclusion.campaigns.append(f"customers/{cid}/campaigns/{validated_id}")
        elif validated_scope == "CHANNEL":
            if not advertising_channel_types:
                return error_response("advertising_channel_types is required when scope=CHANNEL")
            validated_types = _validate_channel_types(advertising_channel_types)
            channel_enum = client.enums.AdvertisingChannelTypeEnum
            for ct in validated_types:
                exclusion.advertising_channel_types.append(getattr(channel_enum, ct))

        response = service.mutate_bidding_data_exclusions(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"data_exclusion_id": new_id, "resource_name": resource_name},
            message=f"Bidding data exclusion '{name}' created",
        )
    except Exception as e:
        logger.error("Failed to create bidding data exclusion: %s", e, exc_info=True)
        return error_response(f"Failed to create bidding data exclusion: {e}")


@mcp.tool()
def remove_bidding_data_exclusion(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    data_exclusion_id: Annotated[str, "The data exclusion ID"],
) -> str:
    """Remove a bidding data exclusion."""
    try:
        cid = resolve_customer_id(customer_id)
        validated_id = validate_numeric_id(data_exclusion_id, "data_exclusion_id")
        client = get_client()
        service = get_service("BiddingDataExclusionService")

        operation = client.get_type("BiddingDataExclusionOperation")
        operation.remove = f"customers/{cid}/biddingDataExclusions/{validated_id}"

        response = service.mutate_bidding_data_exclusions(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Bidding data exclusion {validated_id} removed",
        )
    except Exception as e:
        logger.error("Failed to remove bidding data exclusion: %s", e, exc_info=True)
        return error_response(f"Failed to remove bidding data exclusion: {e}")


@mcp.tool()
def list_seasonality_adjustments(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """List bidding seasonality adjustments for a customer account."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                bidding_seasonality_adjustment.seasonality_adjustment_id,
                bidding_seasonality_adjustment.name,
                bidding_seasonality_adjustment.status,
                bidding_seasonality_adjustment.description,
                bidding_seasonality_adjustment.start_date_time,
                bidding_seasonality_adjustment.end_date_time,
                bidding_seasonality_adjustment.scope,
                bidding_seasonality_adjustment.conversion_rate_modifier,
                bidding_seasonality_adjustment.advertising_channel_types,
                bidding_seasonality_adjustment.campaigns
            FROM bidding_seasonality_adjustment
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        adjustments = []
        for row in response:
            sa = row.bidding_seasonality_adjustment
            adjustments.append({
                "seasonality_adjustment_id": str(sa.seasonality_adjustment_id),
                "name": sa.name,
                "status": sa.status.name,
                "description": sa.description,
                "start_date_time": sa.start_date_time,
                "end_date_time": sa.end_date_time,
                "scope": sa.scope.name,
                "conversion_rate_modifier": sa.conversion_rate_modifier,
                "advertising_channel_types": [ct.name for ct in sa.advertising_channel_types],
                "campaigns": list(sa.campaigns),
            })
        return success_response({"adjustments": adjustments, "count": len(adjustments)})
    except Exception as e:
        logger.error("Failed to list seasonality adjustments: %s", e, exc_info=True)
        return error_response(f"Failed to list seasonality adjustments: {e}")


@mcp.tool()
def create_seasonality_adjustment(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Name of the seasonality adjustment"],
    start_date_time: Annotated[str, "Start datetime in YYYY-MM-DD HH:MM:SS format"],
    end_date_time: Annotated[str, "End datetime in YYYY-MM-DD HH:MM:SS format"],
    conversion_rate_modifier: Annotated[float, "Expected conversion rate change (e.g. 1.5 for +50%, 0.7 for -30%)"],
    scope: Annotated[str, "Scope: CAMPAIGN or CHANNEL"],
    campaign_ids: Annotated[list[str] | None, "List of campaign IDs (required when scope=CAMPAIGN)"] = None,
    advertising_channel_types: Annotated[list[str] | None, "Channel types like SEARCH, PERFORMANCE_MAX (required when scope=CHANNEL)"] = None,
    description: Annotated[str | None, "Optional description"] = None,
) -> str:
    """Create a seasonality adjustment to tell Smart Bidding about expected temporary changes in conversion rates."""
    try:
        cid = resolve_customer_id(customer_id)
        _validate_datetime(start_date_time, "start_date_time")
        _validate_datetime(end_date_time, "end_date_time")
        validated_scope = _validate_scope(scope)

        if conversion_rate_modifier <= 0:
            return error_response("conversion_rate_modifier must be greater than 0")

        client = get_client()
        service = get_service("BiddingSeasonalityAdjustmentService")

        operation = client.get_type("BiddingSeasonalityAdjustmentOperation")
        adjustment = operation.create
        adjustment.name = name
        adjustment.start_date_time = start_date_time
        adjustment.end_date_time = end_date_time
        adjustment.conversion_rate_modifier = conversion_rate_modifier

        scope_enum = client.enums.SeasonalityEventScopeEnum
        adjustment.scope = getattr(scope_enum, validated_scope)

        if description:
            adjustment.description = description

        if validated_scope == "CAMPAIGN":
            if not campaign_ids:
                return error_response("campaign_ids is required when scope=CAMPAIGN")
            for cmp_id in campaign_ids:
                validated_id = validate_numeric_id(cmp_id, "campaign_id")
                adjustment.campaigns.append(f"customers/{cid}/campaigns/{validated_id}")
        elif validated_scope == "CHANNEL":
            if not advertising_channel_types:
                return error_response("advertising_channel_types is required when scope=CHANNEL")
            validated_types = _validate_channel_types(advertising_channel_types)
            channel_enum = client.enums.AdvertisingChannelTypeEnum
            for ct in validated_types:
                adjustment.advertising_channel_types.append(getattr(channel_enum, ct))

        response = service.mutate_bidding_seasonality_adjustments(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"seasonality_adjustment_id": new_id, "resource_name": resource_name},
            message=f"Seasonality adjustment '{name}' created",
        )
    except Exception as e:
        logger.error("Failed to create seasonality adjustment: %s", e, exc_info=True)
        return error_response(f"Failed to create seasonality adjustment: {e}")


@mcp.tool()
def remove_seasonality_adjustment(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    seasonality_adjustment_id: Annotated[str, "The seasonality adjustment ID"],
) -> str:
    """Remove a seasonality adjustment."""
    try:
        cid = resolve_customer_id(customer_id)
        validated_id = validate_numeric_id(seasonality_adjustment_id, "seasonality_adjustment_id")
        client = get_client()
        service = get_service("BiddingSeasonalityAdjustmentService")

        operation = client.get_type("BiddingSeasonalityAdjustmentOperation")
        operation.remove = f"customers/{cid}/biddingSeasonalityAdjustments/{validated_id}"

        response = service.mutate_bidding_seasonality_adjustments(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Seasonality adjustment {validated_id} removed",
        )
    except Exception as e:
        logger.error("Failed to remove seasonality adjustment: %s", e, exc_info=True)
        return error_response(f"Failed to remove seasonality adjustment: {e}")


@mcp.tool()
def list_accessible_bidding_strategies(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """List portfolio bidding strategies accessible from an MCC (manager account)."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                accessible_bidding_strategy.id,
                accessible_bidding_strategy.name,
                accessible_bidding_strategy.type,
                accessible_bidding_strategy.owner_customer_id,
                accessible_bidding_strategy.owner_descriptive_name
            FROM accessible_bidding_strategy
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        strategies = []
        for row in response:
            abs_ = row.accessible_bidding_strategy
            strategies.append({
                "strategy_id": str(abs_.id),
                "name": abs_.name,
                "type": abs_.type_.name,
                "owner_customer_id": str(abs_.owner_customer_id),
                "owner_descriptive_name": abs_.owner_descriptive_name,
            })
        return success_response({"strategies": strategies, "count": len(strategies)})
    except Exception as e:
        logger.error("Failed to list accessible bidding strategies: %s", e, exc_info=True)
        return error_response(f"Failed to list accessible bidding strategies: {e}")
