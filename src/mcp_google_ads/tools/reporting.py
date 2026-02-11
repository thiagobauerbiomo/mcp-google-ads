"""Reporting tools (15 tools)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Annotated, Any

from ..auth import get_service
from ..coordinator import mcp
from ..utils import (
    build_date_clause,
    error_response,
    format_micros,
    resolve_customer_id,
    success_response,
    validate_date,
    validate_limit,
    validate_numeric_id,
)

logger = logging.getLogger(__name__)


def _build_where(
    conditions: list[str],
    date_range: str | None,
    start_date: str | None,
    end_date: str | None,
    default_range: str = "LAST_30_DAYS",
) -> str:
    """Build a complete WHERE clause for GAQL reports."""
    date = build_date_clause(date_range, start_date, end_date, default=default_range)
    conditions.append(date)
    return "WHERE " + " AND ".join(conditions) if conditions else ""


def _run_report(
    customer_id: str | None,
    query_template: str,
    field_extractor: Callable[[Any], dict],
    conditions: list[str] | None = None,
    date_range: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 1000,
    default_date_range: str | None = "LAST_30_DAYS",
    report_name: str = "report",
) -> str:
    """Execute a standard report query and return formatted results.

    Encapsulates the common pattern: resolve customer ID, validate limit,
    build WHERE clause, execute GAQL, extract fields, return success_response.

    Args:
        customer_id: The Google Ads customer ID.
        query_template: GAQL query with {where} and {limit} placeholders.
        field_extractor: Callable that receives a row and returns a dict of fields.
        conditions: List of WHERE conditions (e.g. ["metrics.impressions > 0"]).
        date_range: Predefined date range (LAST_7_DAYS, LAST_30_DAYS, etc.).
        start_date: Start date YYYY-MM-DD (overrides date_range).
        end_date: End date YYYY-MM-DD.
        limit: Maximum number of results.
        default_date_range: Default date range when none specified. Use None to skip date clause.
        report_name: Key name for the report data in the response.
    """
    cid = resolve_customer_id(customer_id)
    limit = validate_limit(limit)
    service = get_service("GoogleAdsService")

    if default_date_range is not None:
        where = _build_where(
            conditions or [], date_range, start_date, end_date, default_range=default_date_range
        )
    else:
        where = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = query_template.format(where=where, limit=limit)
    response = service.search(customer_id=cid, query=query)

    rows = [field_extractor(row) for row in response]
    return success_response({report_name: rows, "count": len(rows)})


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
        conditions = ["metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")

        return _run_report(
            customer_id=customer_id,
            query_template="""
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
            """,
            field_extractor=lambda row: {
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
            },
            conditions=conditions,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to get campaign performance: %s", e, exc_info=True)
        return error_response(f"Failed to get campaign performance: {e}")


@mcp.tool()
def ad_group_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str | None, "Predefined range: TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, THIS_MONTH, LAST_MONTH"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD (overrides date_range)"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get ad group performance metrics."""
    try:
        conditions = ["metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")

        return _run_report(
            customer_id=customer_id,
            query_template="""
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
                {where}
                ORDER BY metrics.cost_micros DESC
                LIMIT {limit}
            """,
            field_extractor=lambda row: {
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
            },
            conditions=conditions,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to get ad group performance: %s", e, exc_info=True)
        return error_response(f"Failed to get ad group performance: {e}")


@mcp.tool()
def ad_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    ad_group_id: Annotated[str | None, "Filter by ad group ID"] = None,
    date_range: Annotated[str | None, "Predefined range: TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, THIS_MONTH, LAST_MONTH"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD (overrides date_range)"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get ad-level performance metrics including ad strength."""
    try:
        conditions = ["metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")
        if ad_group_id:
            conditions.append(f"ad_group.id = {validate_numeric_id(ad_group_id, 'ad_group_id')}")

        return _run_report(
            customer_id=customer_id,
            query_template="""
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
                ORDER BY metrics.cost_micros DESC
                LIMIT {limit}
            """,
            field_extractor=lambda row: {
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
            },
            conditions=conditions,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to get ad performance: %s", e, exc_info=True)
        return error_response(f"Failed to get ad performance: {e}")


@mcp.tool()
def keyword_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    ad_group_id: Annotated[str | None, "Filter by ad group ID"] = None,
    date_range: Annotated[str | None, "Predefined range: TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, THIS_MONTH, LAST_MONTH"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD (overrides date_range)"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """Get keyword performance with quality score, CTR, and conversion data."""
    try:
        conditions = ["ad_group_criterion.type = 'KEYWORD'", "metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")
        if ad_group_id:
            conditions.append(f"ad_group.id = {validate_numeric_id(ad_group_id, 'ad_group_id')}")

        return _run_report(
            customer_id=customer_id,
            query_template="""
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
                ORDER BY metrics.cost_micros DESC
                LIMIT {limit}
            """,
            field_extractor=lambda row: {
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
            },
            conditions=conditions,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to get keyword performance: %s", e, exc_info=True)
        return error_response(f"Failed to get keyword performance: {e}")


@mcp.tool()
def search_terms_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str | None, "Predefined range: TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, THIS_MONTH, LAST_MONTH"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD (overrides date_range)"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """Get search terms that triggered ads. Essential for finding negative keyword opportunities."""
    try:
        conditions = ["metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")

        return _run_report(
            customer_id=customer_id,
            query_template="""
                SELECT
                    search_term_view.search_term,
                    search_term_view.status,
                    ad_group.id,
                    ad_group.name,
                    campaign.id,
                    campaign.name,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr
                FROM search_term_view
                {where}
                ORDER BY metrics.impressions DESC
                LIMIT {limit}
            """,
            field_extractor=lambda row: {
                "search_term": row.search_term_view.search_term,
                "status": row.search_term_view.status.name,
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
            },
            conditions=conditions,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to get search terms report: %s", e, exc_info=True)
        return error_response(f"Failed to get search terms report: {e}")


@mcp.tool()
def audience_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str | None, "Predefined range"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get audience segment performance metrics."""
    try:
        conditions = ["metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")

        return _run_report(
            customer_id=customer_id,
            query_template="""
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
                {where}
                ORDER BY metrics.impressions DESC
                LIMIT {limit}
            """,
            field_extractor=lambda row: {
                "resource_name": row.campaign_audience_view.resource_name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
                "avg_cpc": format_micros(row.metrics.average_cpc),
            },
            conditions=conditions,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to get audience performance: %s", e, exc_info=True)
        return error_response(f"Failed to get audience performance: {e}")


@mcp.tool()
def geographic_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str | None, "Predefined range"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get geographic performance by country, region, and city."""
    try:
        conditions = ["metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")

        return _run_report(
            customer_id=customer_id,
            query_template="""
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
                {where}
                ORDER BY metrics.impressions DESC
                LIMIT {limit}
            """,
            field_extractor=lambda row: {
                "country_criterion_id": str(row.geographic_view.country_criterion_id),
                "location_type": row.geographic_view.location_type.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
            },
            conditions=conditions,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to get geographic performance: %s", e, exc_info=True)
        return error_response(f"Failed to get geographic performance: {e}")


@mcp.tool()
def change_history_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    date_range: Annotated[str | None, "Predefined range"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get recent change history showing who made what changes and when."""
    try:
        return _run_report(
            customer_id=customer_id,
            query_template="""
                SELECT
                    change_event.change_date_time,
                    change_event.change_resource_type,
                    change_event.change_resource_name,
                    change_event.resource_change_operation,
                    change_event.user_email,
                    change_event.client_type,
                    change_event.changed_fields
                FROM change_event
                {where}
                ORDER BY change_event.change_date_time DESC
                LIMIT {limit}
            """,
            field_extractor=lambda row: {
                "change_date": row.change_event.change_date_time,
                "resource_type": row.change_event.change_resource_type.name,
                "resource_name": row.change_event.change_resource_name,
                "operation": row.change_event.resource_change_operation.name,
                "user_email": row.change_event.user_email,
                "client_type": row.change_event.client_type.name,
            },
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            default_date_range="LAST_7_DAYS",
            report_name="changes",
        )
    except Exception as e:
        logger.error("Failed to get change history: %s", e, exc_info=True)
        return error_response(f"Failed to get change history: {e}")


@mcp.tool()
def device_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str | None, "Predefined range"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get performance metrics segmented by device (mobile, desktop, tablet)."""
    try:
        conditions = ["metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")

        return _run_report(
            customer_id=customer_id,
            query_template="""
                SELECT
                    segments.device,
                    campaign.id,
                    campaign.name,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc,
                    metrics.cost_per_conversion
                FROM campaign
                {where}
                ORDER BY metrics.cost_micros DESC
                LIMIT {limit}
            """,
            field_extractor=lambda row: {
                "device": row.segments.device.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
                "avg_cpc": format_micros(row.metrics.average_cpc),
                "cost_per_conversion": format_micros(row.metrics.cost_per_conversion),
            },
            conditions=conditions,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to get device performance: %s", e, exc_info=True)
        return error_response(f"Failed to get device performance: {e}")


@mcp.tool()
def hourly_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str | None, "Predefined range"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum results"] = 200,
) -> str:
    """Get performance metrics segmented by hour and day of week.

    Useful for identifying best-performing times to set ad schedules.
    """
    try:
        conditions = ["metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")

        return _run_report(
            customer_id=customer_id,
            query_template="""
                SELECT
                    segments.hour,
                    segments.day_of_week,
                    campaign.id,
                    campaign.name,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr
                FROM campaign
                {where}
                ORDER BY segments.day_of_week, segments.hour
                LIMIT {limit}
            """,
            field_extractor=lambda row: {
                "hour": row.segments.hour,
                "day_of_week": row.segments.day_of_week.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
            },
            conditions=conditions,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            default_date_range="LAST_7_DAYS",
        )
    except Exception as e:
        logger.error("Failed to get hourly performance: %s", e, exc_info=True)
        return error_response(f"Failed to get hourly performance: {e}")


@mcp.tool()
def age_gender_performance_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str | None, "Predefined range"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum results"] = 50,
) -> str:
    """Get performance metrics by age range and gender demographics.

    Useful for understanding which demographics convert best.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        conditions = ["metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")

        where = _build_where(conditions, date_range, start_date, end_date)

        age_query = f"""
            SELECT
                ad_group_criterion.age_range.type,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr
            FROM age_range_view
            {where}
            ORDER BY metrics.impressions DESC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=age_query)
        age_rows = []
        for row in response:
            age_rows.append({
                "age_range": row.ad_group_criterion.age_range.type_.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
            })

        gender_query = f"""
            SELECT
                ad_group_criterion.gender.type,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr
            FROM gender_view
            {where}
            ORDER BY metrics.impressions DESC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=gender_query)
        gender_rows = []
        for row in response:
            gender_rows.append({
                "gender": row.ad_group_criterion.gender.type_.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
            })

        return success_response({
            "age_report": age_rows,
            "gender_report": gender_rows,
            "age_count": len(age_rows),
            "gender_count": len(gender_rows),
        })
    except Exception as e:
        logger.error("Failed to get age/gender performance: %s", e, exc_info=True)
        return error_response(f"Failed to get age/gender performance: {e}")


@mcp.tool()
def placement_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    date_range: Annotated[str | None, "Predefined range"] = None,
    start_date: Annotated[str | None, "Start date YYYY-MM-DD"] = None,
    end_date: Annotated[str | None, "End date YYYY-MM-DD"] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """Get placement performance for Display/Video campaigns.

    Shows which websites, apps, and YouTube channels/videos showed your ads.
    """
    try:
        conditions = ["metrics.impressions > 0"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")

        return _run_report(
            customer_id=customer_id,
            query_template="""
                SELECT
                    detail_placement_view.display_name,
                    detail_placement_view.target_url,
                    detail_placement_view.placement_type,
                    campaign.id,
                    campaign.name,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr
                FROM detail_placement_view
                {where}
                ORDER BY metrics.impressions DESC
                LIMIT {limit}
            """,
            field_extractor=lambda row: {
                "display_name": row.detail_placement_view.display_name,
                "target_url": row.detail_placement_view.target_url,
                "placement_type": row.detail_placement_view.placement_type.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": format_micros(row.metrics.cost_micros),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2),
            },
            conditions=conditions,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to get placement report: %s", e, exc_info=True)
        return error_response(f"Failed to get placement report: {e}")


@mcp.tool()
def quality_score_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """Get detailed quality score data for keywords.

    Includes quality score, expected CTR, ad relevance, and landing page experience.
    """
    try:
        conditions = [
            "ad_group_criterion.type = 'KEYWORD'",
            "ad_group_criterion.status = 'ENABLED'",
        ]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")

        return _run_report(
            customer_id=customer_id,
            query_template="""
                SELECT
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.quality_info.quality_score,
                    ad_group_criterion.quality_info.creative_quality_score,
                    ad_group_criterion.quality_info.post_click_quality_score,
                    ad_group_criterion.quality_info.search_predicted_ctr,
                    ad_group.id,
                    ad_group.name,
                    campaign.id,
                    campaign.name
                FROM ad_group_criterion
                {where}
                ORDER BY ad_group_criterion.quality_info.quality_score ASC
                LIMIT {limit}
            """,
            field_extractor=lambda row: {
                "keyword": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "quality_score": row.ad_group_criterion.quality_info.quality_score,
                "ad_relevance": row.ad_group_criterion.quality_info.creative_quality_score.name,
                "landing_page_experience": row.ad_group_criterion.quality_info.post_click_quality_score.name,
                "expected_ctr": row.ad_group_criterion.quality_info.search_predicted_ctr.name,
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
            },
            conditions=conditions,
            limit=limit,
            default_date_range=None,
        )
    except Exception as e:
        logger.error("Failed to get quality score report: %s", e, exc_info=True)
        return error_response(f"Failed to get quality score report: {e}")


@mcp.tool()
def comparison_report(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    current_start: Annotated[str, "Current period start date (YYYY-MM-DD)"] = "",
    current_end: Annotated[str, "Current period end date (YYYY-MM-DD)"] = "",
    previous_start: Annotated[str, "Previous period start date (YYYY-MM-DD)"] = "",
    previous_end: Annotated[str, "Previous period end date (YYYY-MM-DD)"] = "",
) -> str:
    """Compare campaign performance between two date ranges.

    Returns metrics for both periods plus calculated deltas (absolute and percentage changes).
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        validate_date(current_start)
        validate_date(current_end)
        validate_date(previous_start)
        validate_date(previous_end)

        campaign_filter = ""
        if campaign_id:
            campaign_filter = f"AND campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}"

        def _run_query(start: str, end: str) -> dict:
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversions_value,
                    metrics.ctr,
                    metrics.average_cpc
                FROM campaign
                WHERE segments.date BETWEEN '{start}' AND '{end}'
                    {campaign_filter}
                ORDER BY metrics.cost_micros DESC
            """
            response = service.search(customer_id=cid, query=query)
            totals: dict = {
                "impressions": 0, "clicks": 0, "cost_micros": 0,
                "conversions": 0.0, "conversion_value": 0.0,
            }
            campaigns_data = []
            for row in response:
                totals["impressions"] += row.metrics.impressions
                totals["clicks"] += row.metrics.clicks
                totals["cost_micros"] += row.metrics.cost_micros
                totals["conversions"] += row.metrics.conversions
                totals["conversion_value"] += row.metrics.conversions_value
                campaigns_data.append({
                    "campaign_id": str(row.campaign.id),
                    "campaign_name": row.campaign.name,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": format_micros(row.metrics.cost_micros),
                    "conversions": round(row.metrics.conversions, 2),
                })
            totals["cost"] = format_micros(totals["cost_micros"])
            totals["ctr"] = round((totals["clicks"] / totals["impressions"] * 100), 2) if totals["impressions"] > 0 else 0
            return {"totals": totals, "campaigns": campaigns_data}

        current = _run_query(current_start, current_end)
        previous = _run_query(previous_start, previous_end)

        def _calc_delta(current_val: float, previous_val: float) -> dict:
            delta = current_val - previous_val
            pct = round((delta / previous_val * 100), 2) if previous_val != 0 else 0
            return {"delta": round(delta, 2), "pct_change": pct}

        ct = current["totals"]
        pt = previous["totals"]
        deltas = {
            "impressions": _calc_delta(ct["impressions"], pt["impressions"]),
            "clicks": _calc_delta(ct["clicks"], pt["clicks"]),
            "cost": _calc_delta(ct["cost_micros"], pt["cost_micros"]),
            "conversions": _calc_delta(ct["conversions"], pt["conversions"]),
            "ctr": _calc_delta(ct["ctr"], pt["ctr"]),
        }

        return success_response({
            "current_period": {"start": current_start, "end": current_end, **current},
            "previous_period": {"start": previous_start, "end": previous_end, **previous},
            "deltas": deltas,
        })
    except Exception as e:
        logger.error("Failed to generate comparison report: %s", e, exc_info=True)
        return error_response(f"Failed to generate comparison report: {e}")


@mcp.tool()
def pmax_search_term_insights(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by PMax campaign ID"] = None,
    limit: Annotated[int, "Maximum results"] = 1000,
) -> str:
    """Get search term insights for Performance Max campaigns.

    Shows categories of search terms that triggered PMax ads. Unlike search_terms_report,
    this works specifically with PMax campaigns using campaign_search_term_insight resource.
    Note: Returns category-level insights, not individual search terms.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        conditions = []
        if campaign_id:
            conditions.append(
                f"campaign_search_term_insight.campaign_id = {validate_numeric_id(campaign_id, 'campaign_id')}"
            )

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT
                campaign_search_term_insight.category_label,
                campaign_search_term_insight.id,
                campaign_search_term_insight.campaign_id
            FROM campaign_search_term_insight
            {where}
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        insights = []
        for row in response:
            insights.append({
                "category_label": row.campaign_search_term_insight.category_label,
                "insight_id": str(row.campaign_search_term_insight.id),
                "campaign_id": str(row.campaign_search_term_insight.campaign_id),
            })
        return success_response({"insights": insights, "count": len(insights)})
    except Exception as e:
        logger.error("Failed to get PMax search term insights: %s", e, exc_info=True)
        return error_response(f"Failed to get PMax search term insights: {e}")
