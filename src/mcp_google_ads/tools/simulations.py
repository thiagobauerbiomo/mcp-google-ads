"""Bid and budget simulation tools (6 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_service
from ..coordinator import mcp
from ..utils import (
    error_response,
    format_micros,
    resolve_customer_id,
    success_response,
    validate_enum_value,
    validate_limit,
    validate_numeric_id,
)

logger = logging.getLogger(__name__)


def _parse_point_list(point_list, list_type: str) -> list[dict]:
    """Parse a simulation point list into user-friendly dicts."""
    if not point_list or not hasattr(point_list, "points"):
        return []
    points = []
    for p in point_list.points:
        point: dict = {}
        if list_type == "cpc_bid":
            point["cpc_bid"] = format_micros(p.cpc_bid_micros)
            point["cpc_bid_micros"] = p.cpc_bid_micros
        elif list_type == "budget":
            point["budget"] = format_micros(p.budget_amount_micros)
            point["budget_micros"] = p.budget_amount_micros
        elif list_type == "target_cpa":
            point["target_cpa"] = format_micros(p.target_cpa_micros)
            point["target_cpa_micros"] = p.target_cpa_micros
        elif list_type == "target_roas":
            point["target_roas"] = p.target_roas if hasattr(p, "target_roas") else None

        # Common fields
        if hasattr(p, "clicks"):
            point["clicks"] = p.clicks
        if hasattr(p, "impressions"):
            point["impressions"] = p.impressions
        if hasattr(p, "cost_micros"):
            point["cost"] = format_micros(p.cost_micros)
            point["cost_micros"] = p.cost_micros
        if hasattr(p, "biddable_conversions"):
            point["conversions"] = round(p.biddable_conversions, 2) if p.biddable_conversions else 0
        if hasattr(p, "biddable_conversions_value"):
            point["conversions_value"] = round(p.biddable_conversions_value, 2) if p.biddable_conversions_value else 0
        if hasattr(p, "top_slot_impressions"):
            point["top_impressions"] = p.top_slot_impressions
        points.append(point)
    return points


_SIMULATION_TYPE_MAP = {
    "CPC_BID": "cpc_bid",
    "TARGET_CPA": "target_cpa",
    "TARGET_ROAS": "target_roas",
    "BUDGET": "budget",
}

_POINT_LIST_ATTR_MAP = {
    "CPC_BID": "cpc_bid_point_list",
    "TARGET_CPA": "target_cpa_point_list",
    "TARGET_ROAS": "target_roas_point_list",
    "BUDGET": "budget_point_list",
}


@mcp.tool()
def list_campaign_simulations(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """List available bid and budget simulations for a campaign.

    Simulations show predicted impact of bid/budget changes.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_campaign_id = validate_numeric_id(campaign_id, "campaign_id")
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign_simulation.campaign_id,
                campaign_simulation.type,
                campaign_simulation.modification_method,
                campaign_simulation.start_date,
                campaign_simulation.end_date,
                campaign_simulation.cpc_bid_point_list,
                campaign_simulation.target_cpa_point_list,
                campaign_simulation.target_roas_point_list,
                campaign_simulation.budget_point_list
            FROM campaign_simulation
            WHERE campaign_simulation.campaign_id = '{safe_campaign_id}'
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        simulations = []
        for row in response:
            sim = row.campaign_simulation
            sim_type = sim.type_.name if hasattr(sim.type_, "name") else str(sim.type_)
            list_key = _SIMULATION_TYPE_MAP.get(sim_type, "cpc_bid")

            point_list = None
            if sim_type == "CPC_BID" and sim.cpc_bid_point_list:
                point_list = sim.cpc_bid_point_list
            elif sim_type == "TARGET_CPA" and sim.target_cpa_point_list:
                point_list = sim.target_cpa_point_list
            elif sim_type == "TARGET_ROAS" and sim.target_roas_point_list:
                point_list = sim.target_roas_point_list
            elif sim_type == "BUDGET" and sim.budget_point_list:
                point_list = sim.budget_point_list

            simulations.append({
                "campaign_id": sim.campaign_id,
                "type": sim_type,
                "modification_method": sim.modification_method.name if hasattr(sim.modification_method, "name") else str(sim.modification_method),
                "start_date": sim.start_date,
                "end_date": sim.end_date,
                "points": _parse_point_list(point_list, list_key),
            })

        return success_response({"simulations": simulations, "count": len(simulations)})
    except Exception as e:
        logger.error("Failed to list campaign simulations: %s", e, exc_info=True)
        return error_response(f"Failed to list campaign simulations: {e}")


@mcp.tool()
def list_ad_group_simulations(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """List available bid simulations for an ad group."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag_id = validate_numeric_id(ad_group_id, "ad_group_id")
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                ad_group_simulation.ad_group_id,
                ad_group_simulation.type,
                ad_group_simulation.modification_method,
                ad_group_simulation.start_date,
                ad_group_simulation.end_date,
                ad_group_simulation.cpc_bid_point_list,
                ad_group_simulation.target_cpa_point_list,
                ad_group_simulation.target_roas_point_list
            FROM ad_group_simulation
            WHERE ad_group_simulation.ad_group_id = '{safe_ag_id}'
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        simulations = []
        for row in response:
            sim = row.ad_group_simulation
            sim_type = sim.type_.name if hasattr(sim.type_, "name") else str(sim.type_)
            list_key = _SIMULATION_TYPE_MAP.get(sim_type, "cpc_bid")

            point_list = None
            if sim_type == "CPC_BID" and sim.cpc_bid_point_list:
                point_list = sim.cpc_bid_point_list
            elif sim_type == "TARGET_CPA" and sim.target_cpa_point_list:
                point_list = sim.target_cpa_point_list
            elif sim_type == "TARGET_ROAS" and sim.target_roas_point_list:
                point_list = sim.target_roas_point_list

            simulations.append({
                "ad_group_id": sim.ad_group_id,
                "type": sim_type,
                "modification_method": sim.modification_method.name if hasattr(sim.modification_method, "name") else str(sim.modification_method),
                "start_date": sim.start_date,
                "end_date": sim.end_date,
                "points": _parse_point_list(point_list, list_key),
            })

        return success_response({"simulations": simulations, "count": len(simulations)})
    except Exception as e:
        logger.error("Failed to list ad group simulations: %s", e, exc_info=True)
        return error_response(f"Failed to list ad group simulations: {e}")


@mcp.tool()
def list_keyword_simulations(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    criterion_id: Annotated[str, "The keyword criterion ID"],
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """List CPC bid simulations for a specific keyword."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_ag_id = validate_numeric_id(ad_group_id, "ad_group_id")
        safe_criterion_id = validate_numeric_id(criterion_id, "criterion_id")
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                ad_group_criterion_simulation.ad_group_id,
                ad_group_criterion_simulation.criterion_id,
                ad_group_criterion_simulation.type,
                ad_group_criterion_simulation.modification_method,
                ad_group_criterion_simulation.start_date,
                ad_group_criterion_simulation.end_date,
                ad_group_criterion_simulation.cpc_bid_point_list
            FROM ad_group_criterion_simulation
            WHERE ad_group_criterion_simulation.ad_group_id = '{safe_ag_id}'
                AND ad_group_criterion_simulation.criterion_id = {safe_criterion_id}
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        simulations = []
        for row in response:
            sim = row.ad_group_criterion_simulation
            simulations.append({
                "ad_group_id": sim.ad_group_id,
                "criterion_id": sim.criterion_id,
                "type": sim.type_.name if hasattr(sim.type_, "name") else str(sim.type_),
                "modification_method": sim.modification_method.name if hasattr(sim.modification_method, "name") else str(sim.modification_method),
                "start_date": sim.start_date,
                "end_date": sim.end_date,
                "points": _parse_point_list(sim.cpc_bid_point_list, "cpc_bid"),
            })

        return success_response({"simulations": simulations, "count": len(simulations)})
    except Exception as e:
        logger.error("Failed to list keyword simulations: %s", e, exc_info=True)
        return error_response(f"Failed to list keyword simulations: {e}")


@mcp.tool()
def get_bid_simulation_points(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    simulation_type: Annotated[str, "Type: CPC_BID, TARGET_CPA, TARGET_ROAS, BUDGET"] = "CPC_BID",
) -> str:
    """Get detailed bid simulation points for a campaign showing predicted metrics at each bid level.

    Returns predicted clicks, impressions, cost, and conversions for each simulated bid/budget value.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_campaign_id = validate_numeric_id(campaign_id, "campaign_id")
        safe_type = validate_enum_value(simulation_type, "simulation_type")

        if safe_type not in _SIMULATION_TYPE_MAP:
            return error_response(
                f"Invalid simulation_type: '{simulation_type}'. "
                f"Use: {', '.join(_SIMULATION_TYPE_MAP.keys())}"
            )

        point_list_attr = _POINT_LIST_ATTR_MAP[safe_type]
        list_key = _SIMULATION_TYPE_MAP[safe_type]

        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign_simulation.campaign_id,
                campaign_simulation.type,
                campaign_simulation.start_date,
                campaign_simulation.end_date,
                campaign_simulation.{point_list_attr}
            FROM campaign_simulation
            WHERE campaign_simulation.campaign_id = '{safe_campaign_id}'
                AND campaign_simulation.type = {safe_type}
        """
        response = service.search(customer_id=cid, query=query)
        all_points = []
        sim_info = None
        for row in response:
            sim = row.campaign_simulation
            if sim_info is None:
                sim_info = {
                    "campaign_id": sim.campaign_id,
                    "type": safe_type,
                    "start_date": sim.start_date,
                    "end_date": sim.end_date,
                }
            point_list = getattr(sim, point_list_attr, None)
            parsed = _parse_point_list(point_list, list_key)
            all_points.extend(parsed)

        if not sim_info:
            return error_response(
                f"No {safe_type} simulation found for campaign {campaign_id}"
            )

        sim_info["points"] = all_points
        sim_info["points_count"] = len(all_points)
        return success_response(sim_info)
    except Exception as e:
        logger.error("Failed to get bid simulation points: %s", e, exc_info=True)
        return error_response(f"Failed to get bid simulation points: {e}")


@mcp.tool()
def list_campaign_budget_simulations(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
) -> str:
    """List budget simulations for a campaign showing impact of budget changes on performance.

    Shows how increasing or decreasing budget would affect clicks, impressions, and conversions.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_campaign_id = validate_numeric_id(campaign_id, "campaign_id")
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign_simulation.campaign_id,
                campaign_simulation.start_date,
                campaign_simulation.end_date,
                campaign_simulation.budget_point_list
            FROM campaign_simulation
            WHERE campaign_simulation.campaign_id = '{safe_campaign_id}'
                AND campaign_simulation.type = BUDGET
        """
        response = service.search(customer_id=cid, query=query)
        simulations = []
        for row in response:
            sim = row.campaign_simulation
            simulations.append({
                "campaign_id": sim.campaign_id,
                "start_date": sim.start_date,
                "end_date": sim.end_date,
                "points": _parse_point_list(sim.budget_point_list, "budget"),
            })

        return success_response({"simulations": simulations, "count": len(simulations)})
    except Exception as e:
        logger.error("Failed to list campaign budget simulations: %s", e, exc_info=True)
        return error_response(f"Failed to list campaign budget simulations: {e}")


@mcp.tool()
def get_keyword_plan_simulation(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    keyword_plan_id: Annotated[str, "The keyword plan ID"],
) -> str:
    """Get forecast simulation for a keyword plan.

    Returns predicted metrics for the keyword plan at different bid levels.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_kp_id = validate_numeric_id(keyword_plan_id, "keyword_plan_id")
        service = get_service("KeywordPlanService")

        keyword_plan_resource = f"customers/{cid}/keywordPlans/{safe_kp_id}"
        response = service.generate_forecast_metrics(keyword_plan=keyword_plan_resource)

        forecasts = []
        if hasattr(response, "campaign_forecast_metrics"):
            cfm = response.campaign_forecast_metrics
            forecasts.append({
                "level": "campaign",
                "clicks": cfm.clicks if hasattr(cfm, "clicks") else None,
                "impressions": cfm.impressions if hasattr(cfm, "impressions") else None,
                "cost": format_micros(cfm.cost_micros) if hasattr(cfm, "cost_micros") else None,
                "conversions": round(cfm.conversions, 2) if hasattr(cfm, "conversions") and cfm.conversions else None,
                "conversion_rate": round(cfm.conversion_rate, 4) if hasattr(cfm, "conversion_rate") and cfm.conversion_rate else None,
                "avg_cpc": format_micros(cfm.average_cpc_micros) if hasattr(cfm, "average_cpc_micros") else None,
            })

        keyword_forecasts = []
        if hasattr(response, "keyword_forecasts"):
            for kf in response.keyword_forecasts:
                kw_data = {
                    "keyword_plan_ad_group_keyword": kf.keyword_plan_ad_group_keyword if hasattr(kf, "keyword_plan_ad_group_keyword") else None,
                }
                if hasattr(kf, "keyword_forecast"):
                    f = kf.keyword_forecast
                    kw_data["clicks"] = f.clicks if hasattr(f, "clicks") else None
                    kw_data["impressions"] = f.impressions if hasattr(f, "impressions") else None
                    kw_data["cost"] = format_micros(f.cost_micros) if hasattr(f, "cost_micros") else None
                    kw_data["conversions"] = round(f.conversions, 2) if hasattr(f, "conversions") and f.conversions else None
                    kw_data["avg_cpc"] = format_micros(f.average_cpc_micros) if hasattr(f, "average_cpc_micros") else None
                keyword_forecasts.append(kw_data)

        return success_response({
            "keyword_plan_id": safe_kp_id,
            "campaign_forecast": forecasts[0] if forecasts else None,
            "keyword_forecasts": keyword_forecasts,
            "keyword_count": len(keyword_forecasts),
        })
    except Exception as e:
        logger.error("Failed to get keyword plan simulation: %s", e, exc_info=True)
        return error_response(f"Failed to get keyword plan simulation: {e}")
