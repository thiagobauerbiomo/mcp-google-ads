"""Reporting tools (8 tools)."""

from __future__ import annotations

from typing import Annotated

from ..auth import get_service
from ..coordinator import mcp
from ..utils import error_response, format_micros, resolve_customer_id, success_response


def _default_date_range() -> str:
    return "DURING LAST_30_DAYS"


def _date_clause(date_range: str | None, start_date: str | None, end_date: str | None) -> str:
    if start_date and end_date:
        return f"WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'"
    return _default_date_range() if not date_range else f"DURING {date_range}"


@mcp.tool()
def campaign_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    date_range: Annotated[str | None, "Predefined range: TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, THIS_MONTH, LAST_MONTH"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD (overrides date_range)"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get campaign performance metrics: impressions, clicks, cost, conversions, CTR, CPC."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        conditions = []
        if campaign_id:
            conditions.append(f"campaign.id = {campaign_id}")
        if start_date and end_date:
            conditions.append(f"segments.date BETWEEN '{start_date}' AND '{end_date}'")

        date_part = ""
        if not start_date:
            date_part = _default_date_range() if not date_range else f"DURING {date_range}"

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)
            if date_part:
                where += f" AND metrics.impressions > 0 {date_part}"
        elif date_part:
            where = f"WHERE metrics.impressions > 0 {date_part}"

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.ctr,
                metrics.average_cpc,
                metrics.average_cpm,
                metrics.cost_per_conversion
            FROM campaign
            {where}
            ORDER BY metrics.cost_micros DESC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        rows = []
        for row in response:
            rows.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "status": row.campaign.status.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "conversion_value": round(row.metrics.conversions_value, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
                "avg_cpc": format_micros(row.metrics.average_cpc),
                "cost_per_conversion": format_micros(row.metrics.cost_per_conversion),
            })
        return success_response({"report": rows, "count": len(rows)})
    except Exception as e:
        return error_response(f"Failed to get campaign performance: {e}")


@mcp.tool()
def ad_group_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str, "Predefined range"] = "LAST_30_DAYS",
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get ad group performance metrics."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        campaign_filter = f"AND campaign.id = {campaign_id}" if campaign_id else ""

        query = f"""
            SELECT
                ad_group.id,
                ad_group.name,
                ad_group.status,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc
            FROM ad_group
            WHERE metrics.impressions > 0 {campaign_filter}
            DURING {date_range}
            ORDER BY metrics.cost_micros DESC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        rows = []
        for row in response:
            rows.append({
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "status": row.ad_group.status.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
                "avg_cpc": format_micros(row.metrics.average_cpc),
            })
        return success_response({"report": rows, "count": len(rows)})
    except Exception as e:
        return error_response(f"Failed to get ad group performance: {e}")


@mcp.tool()
def ad_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    ad_group_id: Annotated[str | None, "Filter by ad group ID"] = None,
    date_range: Annotated[str, "Predefined range"] = "LAST_30_DAYS",
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get ad-level performance metrics including ad strength."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        conditions = ["metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {campaign_id}")
        if ad_group_id:
            conditions.append(f"ad_group.id = {ad_group_id}")
        where = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.type,
                ad_group_ad.status,
                ad_group_ad.ad_strength,
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc
            FROM ad_group_ad
            {where}
            DURING {date_range}
            ORDER BY metrics.cost_micros DESC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        rows = []
        for row in response:
            rows.append({
                "ad_id": str(row.ad_group_ad.ad.id),
                "ad_type": row.ad_group_ad.ad.type_.name,
                "status": row.ad_group_ad.status.name,
                "ad_strength": row.ad_group_ad.ad_strength.name,
                "ad_group_id": str(row.ad_group.id),
                "campaign_id": str(row.campaign.id),
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
                "avg_cpc": format_micros(row.metrics.average_cpc),
            })
        return success_response({"report": rows, "count": len(rows)})
    except Exception as e:
        return error_response(f"Failed to get ad performance: {e}")


@mcp.tool()
def keyword_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    ad_group_id: Annotated[str | None, "Filter by ad group ID"] = None,
    date_range: Annotated[str, "Predefined range"] = "LAST_30_DAYS",
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """Get keyword performance with quality score, CTR, and conversion data."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        conditions = ["ad_group_criterion.type = 'KEYWORD'", "metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {campaign_id}")
        if ad_group_id:
            conditions.append(f"ad_group.id = {ad_group_id}")
        where = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.status,
                ad_group_criterion.quality_info.quality_score,
                ad_group.id,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc
            FROM keyword_view
            {where}
            DURING {date_range}
            ORDER BY metrics.cost_micros DESC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        rows = []
        for row in response:
            rows.append({
                "keyword": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "status": row.ad_group_criterion.status.name,
                "quality_score": row.ad_group_criterion.quality_info.quality_score,
                "ad_group_id": str(row.ad_group.id),
                "campaign_id": str(row.campaign.id),
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
                "avg_cpc": format_micros(row.metrics.average_cpc),
            })
        return success_response({"report": rows, "count": len(rows)})
    except Exception as e:
        return error_response(f"Failed to get keyword performance: {e}")


@mcp.tool()
def search_terms_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str, "Predefined range"] = "LAST_30_DAYS",
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """Get search terms that triggered ads. Essential for finding negative keyword opportunities."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        campaign_filter = f"AND campaign.id = {campaign_id}" if campaign_id else ""

        query = f"""
            SELECT
                search_term_view.search_term,
                search_term_view.status,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr
            FROM search_term_view
            WHERE metrics.impressions > 0 {campaign_filter}
            DURING {date_range}
            ORDER BY metrics.impressions DESC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        rows = []
        for row in response:
            rows.append({
                "search_term": row.search_term_view.search_term,
                "status": row.search_term_view.status.name,
                "matched_keyword": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
            })
        return success_response({"report": rows, "count": len(rows)})
    except Exception as e:
        return error_response(f"Failed to get search terms report: {e}")


@mcp.tool()
def audience_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str, "Predefined range"] = "LAST_30_DAYS",
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get audience segment performance metrics."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        campaign_filter = f"AND campaign.id = {campaign_id}" if campaign_id else ""

        query = f"""
            SELECT
                campaign_audience_view.resource_name,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc
            FROM campaign_audience_view
            WHERE metrics.impressions > 0 {campaign_filter}
            DURING {date_range}
            ORDER BY metrics.impressions DESC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        rows = []
        for row in response:
            rows.append({
                "resource_name": row.campaign_audience_view.resource_name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
                "avg_cpc": format_micros(row.metrics.average_cpc),
            })
        return success_response({"report": rows, "count": len(rows)})
    except Exception as e:
        return error_response(f"Failed to get audience performance: {e}")


@mcp.tool()
def geographic_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str, "Predefined range"] = "LAST_30_DAYS",
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get geographic performance by country, region, and city."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        campaign_filter = f"AND campaign.id = {campaign_id}" if campaign_id else ""

        query = f"""
            SELECT
                geographic_view.country_criterion_id,
                geographic_view.location_type,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr
            FROM geographic_view
            WHERE metrics.impressions > 0 {campaign_filter}
            DURING {date_range}
            ORDER BY metrics.impressions DESC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        rows = []
        for row in response:
            rows.append({
                "country_criterion_id": str(row.geographic_view.country_criterion_id),
                "location_type": row.geographic_view.location_type.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
            })
        return success_response({"report": rows, "count": len(rows)})
    except Exception as e:
        return error_response(f"Failed to get geographic performance: {e}")


@mcp.tool()
def change_history_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    date_range: Annotated[str, "Predefined range"] = "LAST_7_DAYS",
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get recent change history showing who made what changes and when."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                change_event.change_date_time,
                change_event.change_resource_type,
                change_event.change_resource_name,
                change_event.resource_change_operation,
                change_event.user_email,
                change_event.client_type,
                change_event.changed_fields
            FROM change_event
            DURING {date_range}
            ORDER BY change_event.change_date_time DESC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        rows = []
        for row in response:
            rows.append({
                "change_date": row.change_event.change_date_time,
                "resource_type": row.change_event.change_resource_type.name,
                "resource_name": row.change_event.change_resource_name,
                "operation": row.change_event.resource_change_operation.name,
                "user_email": row.change_event.user_email,
                "client_type": row.change_event.client_type.name,
            })
        return success_response({"changes": rows, "count": len(rows)})
    except Exception as e:
        return error_response(f"Failed to get change history: {e}")
