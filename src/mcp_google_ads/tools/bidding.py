"""Bidding strategy management tools (5 tools)."""

from __future__ import annotations

import logging
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
            elif bs.type_.name == "MAXIMIZE_CLICKS":
                data["cpc_bid_ceiling_micros"] = bs.maximize_clicks.cpc_bid_ceiling_micros
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
                strategy.maximize_clicks.cpc_bid_ceiling_micros = cpc_bid_ceiling_micros
            else:
                strategy.maximize_clicks.cpc_bid_ceiling_micros = 0
        elif strategy_type == "MAXIMIZE_CONVERSIONS":
            if target_cpa_micros:
                strategy.maximize_conversions.target_cpa_micros = target_cpa_micros
        elif strategy_type == "TARGET_CPA":
            strategy.target_cpa.target_cpa_micros = target_cpa_micros or 0
        elif strategy_type == "TARGET_ROAS":
            strategy.target_roas.target_roas = target_roas or 0.0
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
            strategy.maximize_clicks.cpc_bid_ceiling_micros = cpc_bid_ceiling_micros
            fields.append("maximize_clicks.cpc_bid_ceiling_micros")

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
