"""Recommendation management tools (5 tools)."""

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
    validate_enum_value,
    validate_limit,
    validate_numeric_id,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def list_recommendations(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    recommendation_type: Annotated[str | None, "Filter by type: KEYWORD, TEXT_AD, CAMPAIGN_BUDGET, ENHANCED_CPC, SEARCH_PARTNERS_OPT_IN, etc."] = None,
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """List optimization recommendations from Google Ads.

    Recommendations are suggestions to improve campaign performance, quality, and reach.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        type_filter = f"WHERE recommendation.type = '{validate_enum_value(recommendation_type, 'recommendation_type')}'" if recommendation_type else ""

        query = f"""
            SELECT
                recommendation.resource_name,
                recommendation.type,
                recommendation.impact.base_metrics.impressions,
                recommendation.impact.base_metrics.clicks,
                recommendation.impact.base_metrics.cost_micros,
                recommendation.impact.potential_metrics.impressions,
                recommendation.impact.potential_metrics.clicks,
                recommendation.impact.potential_metrics.cost_micros,
                recommendation.campaign,
                recommendation.dismissed
            FROM recommendation
            {type_filter}
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        recommendations = []
        for row in response:
            rec = {
                "resource_name": row.recommendation.resource_name,
                "type": row.recommendation.type_.name,
                "dismissed": row.recommendation.dismissed,
                "campaign": row.recommendation.campaign,
            }
            if row.recommendation.impact.base_metrics:
                rec["base_impressions"] = row.recommendation.impact.base_metrics.impressions
                rec["base_clicks"] = row.recommendation.impact.base_metrics.clicks
                rec["base_cost"] = format_micros(row.recommendation.impact.base_metrics.cost_micros)
            if row.recommendation.impact.potential_metrics:
                rec["potential_impressions"] = row.recommendation.impact.potential_metrics.impressions
                rec["potential_clicks"] = row.recommendation.impact.potential_metrics.clicks
                rec["potential_cost"] = format_micros(row.recommendation.impact.potential_metrics.cost_micros)
            recommendations.append(rec)

        return success_response({"recommendations": recommendations, "count": len(recommendations)})
    except Exception as e:
        logger.error("Failed to list recommendations: %s", e, exc_info=True)
        return error_response(f"Failed to list recommendations: {e}")


@mcp.tool()
def get_recommendation(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    recommendation_id: Annotated[str, "The recommendation ID"],
) -> str:
    """Get detailed information about a specific recommendation."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_rec_id = validate_numeric_id(recommendation_id, "recommendation_id")
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                recommendation.resource_name,
                recommendation.type,
                recommendation.impact.base_metrics.impressions,
                recommendation.impact.base_metrics.clicks,
                recommendation.impact.base_metrics.cost_micros,
                recommendation.impact.potential_metrics.impressions,
                recommendation.impact.potential_metrics.clicks,
                recommendation.impact.potential_metrics.cost_micros,
                recommendation.campaign,
                recommendation.ad_group,
                recommendation.dismissed
            FROM recommendation
            WHERE recommendation.resource_name = 'customers/{cid}/recommendations/{safe_rec_id}'
        """
        response = service.search(customer_id=cid, query=query)
        for row in response:
            data = {
                "resource_name": row.recommendation.resource_name,
                "type": row.recommendation.type_.name,
                "dismissed": row.recommendation.dismissed,
                "campaign": row.recommendation.campaign,
                "ad_group": row.recommendation.ad_group,
            }
            if row.recommendation.impact.base_metrics:
                data["base_impressions"] = row.recommendation.impact.base_metrics.impressions
                data["base_clicks"] = row.recommendation.impact.base_metrics.clicks
                data["base_cost"] = format_micros(row.recommendation.impact.base_metrics.cost_micros)
            if row.recommendation.impact.potential_metrics:
                data["potential_impressions"] = row.recommendation.impact.potential_metrics.impressions
                data["potential_clicks"] = row.recommendation.impact.potential_metrics.clicks
                data["potential_cost"] = format_micros(row.recommendation.impact.potential_metrics.cost_micros)
            return success_response(data)
        return error_response(f"Recommendation {recommendation_id} not found")
    except Exception as e:
        logger.error("Failed to get recommendation: %s", e, exc_info=True)
        return error_response(f"Failed to get recommendation: {e}")


@mcp.tool()
def apply_recommendation(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    recommendation_resource_name: Annotated[str, "Full resource name of the recommendation (e.g., customers/123/recommendations/456)"],
) -> str:
    """Apply a recommendation to implement Google's suggestion.

    WARNING: This will make changes to your campaigns (add keywords, adjust bids, etc.).
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("RecommendationService")

        operation = client.get_type("ApplyRecommendationOperation")
        operation.resource_name = recommendation_resource_name

        response = service.apply_recommendation(
            customer_id=cid, operations=[operation]
        )
        results = [r.resource_name for r in response.results]
        return success_response(
            {"applied": len(results), "resource_names": results},
            message="Recommendation applied successfully",
        )
    except Exception as e:
        logger.error("Failed to apply recommendation: %s", e, exc_info=True)
        return error_response(f"Failed to apply recommendation: {e}")


@mcp.tool()
def dismiss_recommendation(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    recommendation_resource_name: Annotated[str, "Full resource name of the recommendation"],
) -> str:
    """Dismiss a recommendation (mark as not useful)."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("RecommendationService")

        operation = client.get_type("DismissRecommendationRequest.DismissRecommendationOperation")
        operation.resource_name = recommendation_resource_name

        response = service.dismiss_recommendation(
            customer_id=cid, operations=[operation]
        )
        results = [r.resource_name for r in response.results]
        return success_response(
            {"dismissed": len(results), "resource_names": results},
            message="Recommendation dismissed",
        )
    except Exception as e:
        logger.error("Failed to dismiss recommendation: %s", e, exc_info=True)
        return error_response(f"Failed to dismiss recommendation: {e}")


@mcp.tool()
def get_optimization_score(
    customer_id: Annotated[str, "The Google Ads customer ID"],
) -> str:
    """Get the account's overall optimization score (0-100%).

    The optimization score indicates how well the account is set up to perform.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        query = """
            SELECT
                customer.optimization_score,
                customer.optimization_score_weight
            FROM customer
        """
        response = service.search(customer_id=cid, query=query)
        for row in response:
            score = row.customer.optimization_score
            weight = row.customer.optimization_score_weight
            return success_response({
                "optimization_score": round(score * 100, 1) if score else None,
                "optimization_score_weight": weight,
            })
        return error_response("Could not retrieve optimization score")
    except Exception as e:
        logger.error("Failed to get optimization score: %s", e, exc_info=True)
        return error_response(f"Failed to get optimization score: {e}")
