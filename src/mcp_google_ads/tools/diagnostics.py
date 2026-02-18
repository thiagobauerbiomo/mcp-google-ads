"""Diagnostic tools (3 tools)."""

from __future__ import annotations

import logging
import time
import urllib.error
import urllib.request
from typing import Annotated

from ..auth import get_service
from ..coordinator import mcp
from ..utils import (
    error_response,
    format_micros,
    resolve_customer_id,
    success_response,
    validate_numeric_id,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def campaign_health_check(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID. None = all ENABLED campaigns"] = None,
) -> str:
    """Run a comprehensive health check on campaigns. Returns list of issues found.

    Checks: keywords below first page bid, ads with POOR/AVERAGE strength, budget-limited campaigns,
    missing geo targeting, ad groups without active ads, low impression campaigns.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        campaign_filter = ""
        if campaign_id:
            safe_id = validate_numeric_id(campaign_id, "campaign_id")
            campaign_filter = f" AND campaign.id = {safe_id}"

        issues: list[dict] = []

        # 1. Campaign status + budget info
        campaign_query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign_budget.amount_micros,
                campaign.advertising_channel_type
            FROM campaign
            WHERE campaign.status = 'ENABLED'{campaign_filter}
        """
        response = service.search(customer_id=cid, query=campaign_query)
        campaigns = []
        for row in response:
            campaigns.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "budget": format_micros(row.campaign_budget.amount_micros),
                "channel_type": row.campaign.advertising_channel_type.name,
            })

        # 2. Ad strength check
        ad_strength_query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad_strength,
                campaign.id
            FROM ad_group_ad
            WHERE ad_group_ad.status = 'ENABLED'
                AND ad_group_ad.ad_strength IN ('POOR', 'AVERAGE'){campaign_filter}
        """
        response = service.search(customer_id=cid, query=ad_strength_query)
        for row in response:
            strength = row.ad_group_ad.ad_strength.name
            severity = "critical" if strength == "POOR" else "warning"
            issues.append({
                "type": "weak_ad_strength",
                "severity": severity,
                "campaign_id": str(row.campaign.id),
                "ad_id": str(row.ad_group_ad.ad.id),
                "detail": f"Ad {row.ad_group_ad.ad.id} has {strength} ad strength",
            })

        # 3. Keywords with quality score issues
        keyword_query = f"""
            SELECT
                ad_group_criterion.keyword.text,
                ad_group_criterion.quality_info.quality_score,
                campaign.id
            FROM ad_group_criterion
            WHERE ad_group_criterion.type = 'KEYWORD'
                AND ad_group_criterion.status = 'ENABLED'
                AND ad_group_criterion.quality_info.quality_score < 5{campaign_filter}
        """
        response = service.search(customer_id=cid, query=keyword_query)
        for row in response:
            qs = row.ad_group_criterion.quality_info.quality_score
            severity = "critical" if qs <= 2 else "warning"
            issues.append({
                "type": "low_quality_score",
                "severity": severity,
                "campaign_id": str(row.campaign.id),
                "keyword": row.ad_group_criterion.keyword.text,
                "quality_score": qs,
                "detail": f"Keyword '{row.ad_group_criterion.keyword.text}' has quality score {qs}/10",
            })

        # 4. Campaigns with zero impressions last 7 days
        zero_impressions_query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions
            FROM campaign
            WHERE campaign.status = 'ENABLED'
                AND segments.date DURING LAST_7_DAYS
                AND metrics.impressions = 0{campaign_filter}
        """
        response = service.search(customer_id=cid, query=zero_impressions_query)
        for row in response:
            issues.append({
                "type": "zero_impressions",
                "severity": "critical",
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "detail": f"Campaign '{row.campaign.name}' has 0 impressions in the last 7 days",
            })

        # Build summary counts
        summary = {"critical": 0, "warning": 0, "info": 0}
        for issue in issues:
            summary[issue["severity"]] += 1

        return success_response({
            "issues": issues,
            "summary": summary,
            "total_issues": len(issues),
            "campaigns_checked": len(campaigns),
        })
    except Exception as e:
        logger.error("Failed to run campaign health check: %s", e, exc_info=True)
        return error_response(f"Failed to run campaign health check: {e}")


@mcp.tool()
def validate_landing_page(
    url: Annotated[str, "The URL to validate"],
) -> str:
    """Validate a landing page URL. Checks HTTP status, redirects, SSL, and response time.

    Use before creating ads to ensure the landing page is working correctly.
    """
    try:
        start_time = time.time()
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "Mozilla/5.0 (compatible; GoogleAdsMCP/1.0)")

        response = urllib.request.urlopen(req, timeout=15)
        response_time_ms = round((time.time() - start_time) * 1000)

        final_url = response.url
        status_code = response.status
        has_ssl = final_url.startswith("https://")

        return success_response({
            "url": url,
            "status_code": status_code,
            "final_url": final_url,
            "has_ssl": has_ssl,
            "response_time_ms": response_time_ms,
            "redirected": final_url != url,
        })
    except urllib.error.HTTPError as e:
        logger.error("HTTP error validating landing page %s: %s", url, e, exc_info=True)
        return error_response(f"HTTP error {e.code}: {e.reason}", details={"url": url, "status_code": e.code})
    except urllib.error.URLError as e:
        logger.error("URL error validating landing page %s: %s", url, e, exc_info=True)
        reason = str(e.reason)
        if "timed out" in reason:
            return error_response("Request timed out after 15 seconds", details={"url": url})
        return error_response(f"Failed to reach URL: {reason}", details={"url": url})
    except TimeoutError:
        logger.error("Timeout validating landing page %s", url, exc_info=True)
        return error_response("Request timed out after 15 seconds", details={"url": url})
    except Exception as e:
        logger.error("Failed to validate landing page %s: %s", url, e, exc_info=True)
        return error_response(f"Failed to validate landing page: {e}", details={"url": url})


@mcp.tool()
def budget_forecast(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_ids: Annotated[list[str] | None, "Campaign IDs to include. None = all ENABLED campaigns"] = None,
    forecast_days: Annotated[int, "Days to forecast (default: 30)"] = 30,
) -> str:
    """Forecast monthly spending based on last 7 days of actual spend.

    Returns daily average, projected monthly cost, budget utilization, and per-campaign breakdown.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        campaign_filter = ""
        if campaign_ids:
            safe_ids = [validate_numeric_id(cid_val, "campaign_id") for cid_val in campaign_ids]
            ids_str = ", ".join(safe_ids)
            campaign_filter = f" AND campaign.id IN ({ids_str})"

        # Query 1: Get configured budget per campaign
        budget_query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign_budget.amount_micros
            FROM campaign
            WHERE campaign.status = 'ENABLED'{campaign_filter}
        """
        response = service.search(customer_id=cid, query=budget_query)
        budgets: dict[str, dict] = {}
        for row in response:
            cmp_id = str(row.campaign.id)
            budgets[cmp_id] = {
                "campaign_id": cmp_id,
                "campaign_name": row.campaign.name,
                "budget_daily": format_micros(row.campaign_budget.amount_micros),
                "budget_daily_micros": row.campaign_budget.amount_micros,
            }

        # Query 2: Get actual spend last 7 days per campaign
        spend_query = f"""
            SELECT
                campaign.id,
                metrics.cost_micros
            FROM campaign
            WHERE campaign.status = 'ENABLED'
                AND segments.date DURING LAST_7_DAYS{campaign_filter}
        """
        response = service.search(customer_id=cid, query=spend_query)
        spend_by_campaign: dict[str, int] = {}
        for row in response:
            cmp_id = str(row.campaign.id)
            spend_by_campaign[cmp_id] = spend_by_campaign.get(cmp_id, 0) + row.metrics.cost_micros

        # Calculate per-campaign breakdown
        breakdown = []
        total_daily_avg_micros = 0
        total_budget_daily_micros = 0

        for cmp_id, budget_info in budgets.items():
            cost_7d_micros = spend_by_campaign.get(cmp_id, 0)
            daily_avg_micros = cost_7d_micros // 7
            projected_micros = daily_avg_micros * forecast_days

            budget_daily_micros = budget_info["budget_daily_micros"]
            utilization_pct = round((daily_avg_micros / budget_daily_micros * 100), 2) if budget_daily_micros > 0 else 0

            total_daily_avg_micros += daily_avg_micros
            total_budget_daily_micros += budget_daily_micros

            breakdown.append({
                "campaign_id": cmp_id,
                "campaign_name": budget_info["campaign_name"],
                "budget_daily": budget_info["budget_daily"],
                "daily_avg_spend": format_micros(daily_avg_micros),
                "projected_spend": format_micros(projected_micros),
                "utilization_pct": utilization_pct,
            })

        # Calculate totals
        total_projected_micros = total_daily_avg_micros * forecast_days
        total_utilization_pct = (
            round((total_daily_avg_micros / total_budget_daily_micros * 100), 2)
            if total_budget_daily_micros > 0
            else 0
        )

        return success_response({
            "forecast_days": forecast_days,
            "totals": {
                "daily_avg_spend": format_micros(total_daily_avg_micros),
                "projected_spend": format_micros(total_projected_micros),
                "total_budget_daily": format_micros(total_budget_daily_micros),
                "utilization_pct": total_utilization_pct,
            },
            "breakdown": breakdown,
            "campaigns_count": len(breakdown),
        })
    except Exception as e:
        logger.error("Failed to generate budget forecast: %s", e, exc_info=True)
        return error_response(f"Failed to generate budget forecast: {e}")
