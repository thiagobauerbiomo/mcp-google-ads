"""Dashboard and MCC summary tools (2 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_service
from ..coordinator import mcp
from ..utils import (
    build_date_clause,
    error_response,
    format_micros,
    resolve_customer_id,
    success_response,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def mcc_performance_summary(
    date_range: Annotated[str | None, "Predefined range: TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, THIS_MONTH, LAST_MONTH"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD (overrides date_range)"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum number of client accounts to include"] = 50,
) -> str:
    """Get a performance summary across ALL active client accounts in the MCC.

    Returns aggregated metrics per account: spend, clicks, impressions, conversions.
    Useful for a quick overview of the entire MCC portfolio.
    """
    try:
        mcc_service = get_service("GoogleAdsService")
        from ..auth import get_config
        mcc_id = get_config().login_customer_id

        clients_query = """
            SELECT
                customer_client.id,
                customer_client.descriptive_name,
                customer_client.status,
                customer_client.currency_code
            FROM customer_client
            WHERE customer_client.manager = false
                AND customer_client.status = 'ENABLED'
            ORDER BY customer_client.descriptive_name ASC
        """
        clients_response = mcc_service.search(customer_id=mcc_id, query=clients_query)

        client_ids = []
        client_names = {}
        for row in clients_response:
            cid = str(row.customer_client.id)
            client_ids.append(cid)
            client_names[cid] = row.customer_client.descriptive_name

        date = build_date_clause(date_range, start_date, end_date)

        accounts_data = []
        errors = []
        totals = {
            "impressions": 0, "clicks": 0, "cost_micros": 0,
            "conversions": 0.0, "accounts_with_spend": 0,
        }

        count = 0
        for cid in client_ids:
            if count >= limit:
                break

            try:
                if date.startswith("segments.date"):
                    where = f"WHERE {date}"
                else:
                    where = date

                perf_query = f"""
                    SELECT
                        metrics.impressions,
                        metrics.clicks,
                        metrics.cost_micros,
                        metrics.conversions,
                        metrics.ctr,
                        metrics.average_cpc
                    FROM customer
                    {where}
                """
                perf_response = get_service("GoogleAdsService").search(
                    customer_id=cid, query=perf_query
                )
                for row in perf_response:
                    account_data = {
                        "customer_id": cid,
                        "name": client_names.get(cid, ""),
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": format_micros(row.metrics.cost_micros),
                        "conversions": round(row.metrics.conversions, 2),
                        "ctr": round(row.metrics.ctr * 100, 2),
                        "avg_cpc": format_micros(row.metrics.average_cpc),
                    }
                    accounts_data.append(account_data)

                    totals["impressions"] += row.metrics.impressions
                    totals["clicks"] += row.metrics.clicks
                    totals["cost_micros"] += row.metrics.cost_micros
                    totals["conversions"] += row.metrics.conversions
                    if row.metrics.cost_micros > 0:
                        totals["accounts_with_spend"] += 1
            except Exception as e:
                logger.warning("Failed to get metrics for account %s: %s", cid, e)
                errors.append({"customer_id": cid, "name": client_names.get(cid, ""), "error": str(e)})

            count += 1

        totals["total_cost"] = format_micros(totals["cost_micros"])
        totals["avg_ctr"] = round(
            (totals["clicks"] / totals["impressions"] * 100), 2
        ) if totals["impressions"] > 0 else 0

        accounts_data.sort(key=lambda x: x.get("cost") or 0, reverse=True)

        result = {
            "totals": totals,
            "accounts": accounts_data,
            "accounts_count": len(accounts_data),
        }
        if errors:
            result["errors"] = errors

        return success_response(result)
    except Exception as e:
        return error_response(f"Failed to get MCC performance summary: {e}")


@mcp.tool()
def account_dashboard(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    date_range: Annotated[str | None, "Predefined range: TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, THIS_MONTH, LAST_MONTH"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
) -> str:
    """Get a complete dashboard summary for a single account.

    Returns in one call: total metrics, active campaigns count, top campaigns by spend,
    optimization score, and pending recommendations count.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        date = build_date_clause(date_range, start_date, end_date)

        # 1. Account-level metrics
        if date.startswith("segments.date"):
            metrics_where = f"WHERE {date}"
        else:
            metrics_where = date

        metrics_query = f"""
            SELECT
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_per_conversion
            FROM customer
            {metrics_where}
        """
        metrics_data = {}
        response = service.search(customer_id=cid, query=metrics_query)
        for row in response:
            metrics_data = {
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "conversion_value": round(row.metrics.conversions_value, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
                "avg_cpc": format_micros(row.metrics.average_cpc),
                "cost_per_conversion": format_micros(row.metrics.cost_per_conversion),
            }

        # 2. Campaign counts by status
        counts_query = """
            SELECT
                campaign.status,
                metrics.impressions
            FROM campaign
            WHERE campaign.status != 'REMOVED'
        """
        status_counts = {"ENABLED": 0, "PAUSED": 0}
        response = service.search(customer_id=cid, query=counts_query)
        for row in response:
            status_name = row.campaign.status.name
            status_counts[status_name] = status_counts.get(status_name, 0) + 1

        # 3. Top 5 campaigns by spend
        if date.startswith("segments.date"):
            top_where = f"WHERE metrics.impressions > 0 AND {date}"
        else:
            top_where = f"WHERE metrics.impressions > 0 {date}"

        top_query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.cost_micros,
                metrics.clicks,
                metrics.conversions,
                metrics.ctr
            FROM campaign
            {top_where}
            ORDER BY metrics.cost_micros DESC
            LIMIT 5
        """
        top_campaigns = []
        response = service.search(customer_id=cid, query=top_query)
        for row in response:
            top_campaigns.append({
                "campaign_id": str(row.campaign.id),
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "cost": format_micros(row.metrics.cost_micros),
                "clicks": row.metrics.clicks,
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
            })

        # 4. Optimization score
        opt_score = None
        try:
            opt_query = """
                SELECT customer.optimization_score
                FROM customer
            """
            response = service.search(customer_id=cid, query=opt_query)
            for row in response:
                if row.customer.optimization_score:
                    opt_score = round(row.customer.optimization_score * 100, 1)
        except Exception as e:
            logger.warning("Failed to get optimization score for %s: %s", cid, e)

        # 5. Recommendations count
        rec_count = 0
        try:
            rec_query = """
                SELECT recommendation.type
                FROM recommendation
                LIMIT 1000
            """
            response = service.search(customer_id=cid, query=rec_query)
            for _ in response:
                rec_count += 1
        except Exception as e:
            logger.warning("Failed to get recommendations count for %s: %s", cid, e)

        return success_response({
            "metrics": metrics_data,
            "campaigns": {
                "enabled": status_counts.get("ENABLED", 0),
                "paused": status_counts.get("PAUSED", 0),
            },
            "top_campaigns": top_campaigns,
            "optimization_score": opt_score,
            "pending_recommendations": rec_count,
        })
    except Exception as e:
        return error_response(f"Failed to get account dashboard: {e}")
