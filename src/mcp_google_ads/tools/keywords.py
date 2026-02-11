"""Keyword management tools (9 tools)."""

from __future__ import annotations

import logging
from datetime import date, timedelta
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
    validate_batch,
    validate_enum_value,
    validate_limit,
    validate_numeric_id,
    validate_status,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def list_keywords(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str | None, "Filter by ad group ID"] = None,
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    status_filter: Annotated[str | None, "Filter: ENABLED, PAUSED, REMOVED"] = None,
    limit: Annotated[int, "Maximum results"] = 200,
) -> str:
    """List keywords with their match type, bid, quality score, and status."""
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")
        conditions = ["ad_group_criterion.type = 'KEYWORD'"]
        if ad_group_id:
            conditions.append(f"ad_group.id = {validate_numeric_id(ad_group_id, 'ad_group_id')}")
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")
        if status_filter:
            conditions.append(f"ad_group_criterion.status = '{validate_status(status_filter)}'")
        where = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                ad_group_criterion.criterion_id,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.status,
                ad_group_criterion.cpc_bid_micros,
                ad_group_criterion.quality_info.quality_score,
                ad_group_criterion.effective_cpc_bid_micros,
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name
            FROM ad_group_criterion
            {where}
            ORDER BY ad_group_criterion.keyword.text ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        keywords = []
        for row in response:
            keywords.append({
                "criterion_id": str(row.ad_group_criterion.criterion_id),
                "keyword": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "status": row.ad_group_criterion.status.name,
                "cpc_bid": format_micros(row.ad_group_criterion.cpc_bid_micros),
                "quality_score": row.ad_group_criterion.quality_info.quality_score,
                "ad_group_id": str(row.ad_group.id),
                "campaign_id": str(row.campaign.id),
            })
        return success_response({"keywords": keywords, "count": len(keywords)})
    except Exception as e:
        logger.error("Failed to list keywords: %s", e, exc_info=True)
        return error_response(f"Failed to list keywords: {e}")


@mcp.tool()
def add_keywords(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    keywords: Annotated[list[dict], "List of {text, match_type} where match_type is EXACT, PHRASE, or BROAD"],
    cpc_bid: Annotated[float | None, "CPC bid for all keywords in account currency"] = None,
) -> str:
    """Add keywords to an ad group. Keywords are added as ENABLED.

    Example keywords: [{"text": "buy shoes", "match_type": "PHRASE"}, {"text": "sneakers", "match_type": "BROAD"}]
    """
    try:
        cid = resolve_customer_id(customer_id)

        error = validate_batch(keywords, max_size=5000, required_fields=["text"], item_name="keywords")
        if error:
            return error_response(error)

        seen = set()
        unique_keywords = []
        for kw in keywords:
            key = (kw["text"], kw.get("match_type", "BROAD"))
            if key not in seen:
                seen.add(key)
                unique_keywords.append(kw)

        client = get_client()
        service = get_service("AdGroupCriterionService")

        operations = []
        for kw in unique_keywords:
            operation = client.get_type("AdGroupCriterionOperation")
            criterion = operation.create
            criterion.ad_group = f"customers/{cid}/adGroups/{ad_group_id}"
            criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            criterion.keyword.text = kw["text"]
            match = kw.get("match_type", "BROAD")
            validate_enum_value(match, "match_type")
            criterion.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum, match
            )
            if cpc_bid is not None:
                criterion.cpc_bid_micros = to_micros(cpc_bid)
            operations.append(operation)

        response = service.mutate_ad_group_criteria(customer_id=cid, operations=operations)
        results = [r.resource_name for r in response.results]
        result_data = {"added": len(results), "resource_names": results}
        return success_response(
            result_data,
            message=f"{len(results)} keywords added to ad group {ad_group_id}",
        )
    except Exception as e:
        logger.error("Failed to add keywords: %s", e, exc_info=True)
        return error_response(f"Failed to add keywords: {e}")


@mcp.tool()
def update_keyword(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    criterion_id: Annotated[str, "The keyword criterion ID"],
    cpc_bid: Annotated[float | None, "New CPC bid in account currency"] = None,
    status: Annotated[str | None, "New status: ENABLED, PAUSED"] = None,
    final_url: Annotated[str | None, "Keyword-level final URL"] = None,
) -> str:
    """Update a keyword's bid, status, or final URL."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupCriterionService")

        operation = client.get_type("AdGroupCriterionOperation")
        criterion = operation.update
        criterion.resource_name = f"customers/{cid}/adGroupCriteria/{ad_group_id}~{criterion_id}"

        fields = []
        if cpc_bid is not None:
            criterion.cpc_bid_micros = to_micros(cpc_bid)
            fields.append("cpc_bid_micros")
        if status is not None:
            validate_enum_value(status, "status")
            criterion.status = getattr(client.enums.AdGroupCriterionStatusEnum, status)
            fields.append("status")
        if final_url is not None:
            criterion.final_urls.append(final_url)
            fields.append("final_urls")

        if not fields:
            return error_response("No fields to update")

        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=fields),
        )

        response = service.mutate_ad_group_criteria(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Keyword {criterion_id} updated",
        )
    except Exception as e:
        logger.error("Failed to update keyword: %s", e, exc_info=True)
        return error_response(f"Failed to update keyword: {e}")


@mcp.tool()
def remove_keywords(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    criterion_ids: Annotated[list[str], "List of keyword criterion IDs to remove"],
) -> str:
    """Remove keywords from an ad group permanently."""
    try:
        cid = resolve_customer_id(customer_id)

        if len(criterion_ids) > 5000:
            return error_response(f"Maximum 5000 keywords per call, received: {len(criterion_ids)}")

        client = get_client()
        service = get_service("AdGroupCriterionService")

        operations = []
        for criterion_id in criterion_ids:
            operation = client.get_type("AdGroupCriterionOperation")
            operation.remove = f"customers/{cid}/adGroupCriteria/{ad_group_id}~{criterion_id}"
            operations.append(operation)

        response = service.mutate_ad_group_criteria(customer_id=cid, operations=operations)
        return success_response(
            {"removed": len(response.results)},
            message=f"{len(response.results)} keywords removed",
        )
    except Exception as e:
        logger.error("Failed to remove keywords: %s", e, exc_info=True)
        return error_response(f"Failed to remove keywords: {e}")


@mcp.tool()
def add_negative_keywords_to_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    keywords: Annotated[list[dict], "List of {text, match_type} for negative keywords"],
) -> str:
    """Add negative keywords at the campaign level to prevent unwanted matches."""
    try:
        cid = resolve_customer_id(customer_id)

        error = validate_batch(keywords, max_size=5000, required_fields=["text"], item_name="keywords")
        if error:
            return error_response(error)

        seen = set()
        unique_keywords = []
        for kw in keywords:
            key = (kw["text"], kw.get("match_type", "BROAD"))
            if key not in seen:
                seen.add(key)
                unique_keywords.append(kw)

        client = get_client()
        service = get_service("CampaignCriterionService")

        operations = []
        for kw in unique_keywords:
            operation = client.get_type("CampaignCriterionOperation")
            criterion = operation.create
            criterion.campaign = f"customers/{cid}/campaigns/{campaign_id}"
            criterion.negative = True
            criterion.keyword.text = kw["text"]
            match = kw.get("match_type", "BROAD")
            validate_enum_value(match, "match_type")
            criterion.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum, match
            )
            operations.append(operation)

        response = service.mutate_campaign_criteria(customer_id=cid, operations=operations)
        return success_response(
            {"added": len(response.results)},
            message=f"{len(response.results)} negative keywords added to campaign {campaign_id}",
        )
    except Exception as e:
        logger.error("Failed to add negative keywords: %s", e, exc_info=True)
        return error_response(f"Failed to add negative keywords: {e}")


@mcp.tool()
def add_negative_keywords_to_shared_set(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    shared_set_id: Annotated[str, "The shared set ID (negative keyword list)"],
    keywords: Annotated[list[str], "List of keyword texts to add as negatives"],
    match_type: Annotated[str, "Match type for all: EXACT, PHRASE, BROAD"] = "BROAD",
) -> str:
    """Add negative keywords to a shared negative keyword list."""
    try:
        cid = resolve_customer_id(customer_id)

        error = validate_batch(keywords, max_size=5000, item_name="keywords")
        if error:
            return error_response(error)

        unique_keywords = list(dict.fromkeys(keywords))

        client = get_client()
        service = get_service("GoogleAdsService")

        mutate_operations = []
        for kw_text in unique_keywords:
            mutate_op = client.get_type("MutateOperation")
            criterion = mutate_op.shared_criterion_operation.create
            criterion.shared_set = f"customers/{cid}/sharedSets/{shared_set_id}"
            criterion.keyword.text = kw_text
            validate_enum_value(match_type, "match_type")
            criterion.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum, match_type
            )
            mutate_operations.append(mutate_op)

        response = service.mutate(customer_id=cid, mutate_operations=mutate_operations)
        added = len(response.mutate_operation_responses)
        return success_response(
            {"added": added},
            message=f"{added} negatives added to shared set {shared_set_id}",
        )
    except Exception as e:
        logger.error("Failed to add to shared set: %s", e, exc_info=True)
        return error_response(f"Failed to add to shared set: {e}")


@mcp.tool()
def generate_keyword_ideas(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    seed_keywords: Annotated[list[str] | None, "Seed keywords to generate ideas from"] = None,
    page_url: Annotated[str | None, "URL to generate keyword ideas from"] = None,
    language_id: Annotated[str, "Language criterion ID (1000=English, 1014=Portuguese)"] = "1014",
    geo_target_id: Annotated[str, "Geo target criterion ID (2076=Brazil, 2840=US)"] = "2076",
    limit: Annotated[int, "Maximum ideas to return"] = 50,
) -> str:
    """Generate keyword ideas using Google's Keyword Planner.

    Provide seed keywords and/or a page URL. Returns search volume and competition data.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("KeywordPlanIdeaService")

        request = client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = cid
        request.language = f"languageConstants/{language_id}"
        request.geo_target_constants.append(f"geoTargetConstants/{geo_target_id}")
        request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH

        if seed_keywords:
            request.keyword_seed.keywords.extend(seed_keywords)
        if page_url:
            request.url_seed.url = page_url

        if not seed_keywords and not page_url:
            return error_response("Provide seed_keywords and/or page_url")

        response = service.generate_keyword_ideas(request=request)
        ideas = []
        count = 0
        for result in response:
            if count >= limit:
                break
            ideas.append({
                "keyword": result.text,
                "avg_monthly_searches": result.keyword_idea_metrics.avg_monthly_searches,
                "competition": result.keyword_idea_metrics.competition.name,
                "competition_index": result.keyword_idea_metrics.competition_index,
                "low_top_of_page_bid_micros": result.keyword_idea_metrics.low_top_of_page_bid_micros,
                "high_top_of_page_bid_micros": result.keyword_idea_metrics.high_top_of_page_bid_micros,
            })
            count += 1
        return success_response({"ideas": ideas, "count": len(ideas)})
    except Exception as e:
        logger.error("Failed to generate keyword ideas: %s", e, exc_info=True)
        return error_response(f"Failed to generate keyword ideas: {e}")


@mcp.tool()
def get_keyword_forecast(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    keywords: Annotated[list[str], "Keywords to forecast"],
    match_type: Annotated[str, "Match type: EXACT, PHRASE, BROAD"] = "EXACT",
    daily_budget_micros: Annotated[int | None, "Daily budget in micros for forecast (e.g. 20_000_000 = R$20)"] = None,
    max_cpc_bid_micros: Annotated[int | None, "Max CPC bid in micros per keyword (e.g. 4_000_000 = R$4)"] = None,
    geo_target_ids: Annotated[list[str] | None, "Geo target IDs (e.g. ['2076'] for Brazil, ['1001773'] for São Paulo)"] = None,
    language_id: Annotated[str | None, "Language criterion ID (1014=Portuguese, 1000=English)"] = None,
    conversion_rate: Annotated[float, "Estimated conversion rate for CPA calculation (0.03 = 3%)"] = 0.03,
) -> str:
    """Get performance forecasts for keywords with CPA estimation.

    Uses the Keyword Planner forecast endpoint. Returns campaign totals,
    per-keyword breakdown, and estimated CPA based on conversion_rate.
    Supports geo targeting, language, and max CPC bid.
    """
    try:
        cid = resolve_customer_id(customer_id)
        validate_enum_value(match_type, "match_type")
        client = get_client()
        service = get_service("KeywordPlanIdeaService")

        request = client.get_type("GenerateKeywordForecastMetricsRequest")
        request.customer_id = cid

        tomorrow = date.today() + timedelta(days=1)
        request.forecast_period.start_date = tomorrow.strftime("%Y-%m-%d")
        request.forecast_period.end_date = (tomorrow + timedelta(days=30)).strftime("%Y-%m-%d")

        campaign = request.campaign
        campaign.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
        if daily_budget_micros or max_cpc_bid_micros:
            manual_cpc = campaign.bidding_strategy.manual_cpc_bidding_strategy
            if daily_budget_micros:
                manual_cpc.daily_budget_micros = daily_budget_micros
            if max_cpc_bid_micros:
                manual_cpc.max_cpc_bid_micros = max_cpc_bid_micros

        if geo_target_ids:
            for geo_id in geo_target_ids:
                geo_modifier = client.get_type("CriterionBidModifier")
                geo_modifier.geo_target_constant = f"geoTargetConstants/{geo_id}"
                campaign.geo_modifiers.append(geo_modifier)

        if language_id:
            campaign.language_constants.append(f"languageConstants/{language_id}")

        for kw_text in keywords:
            ad_group = client.get_type("ForecastAdGroup")
            biddable_keyword = client.get_type("BiddableKeyword")
            biddable_keyword.keyword.text = kw_text
            biddable_keyword.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum, match_type
            )
            if max_cpc_bid_micros:
                biddable_keyword.max_cpc_bid_micros = max_cpc_bid_micros
            ad_group.biddable_keywords.append(biddable_keyword)
            campaign.ad_groups.append(ad_group)

        response = service.generate_keyword_forecast_metrics(request=request)

        result = {}

        if response.campaign_forecast_metrics:
            m = response.campaign_forecast_metrics
            clicks = m.clicks or 0
            impressions = m.impressions or 0
            cost = m.cost_micros or 0
            ctr = m.click_through_rate or 0
            avg_cpc = m.average_cpc_micros or 0
            conversions_api = m.conversions or 0
            conversion_rate_api = m.conversion_rate or 0
            avg_cpa_api = m.average_cpa_micros or 0
            estimated_conversions = round(clicks * conversion_rate, 2)
            estimated_cpa_brl = round(format_micros(cost) / estimated_conversions, 2) if estimated_conversions > 0 else None
            result["campaign_total"] = {
                "impressions": impressions,
                "clicks": clicks,
                "click_through_rate": round(ctr, 4),
                "cost_brl": format_micros(cost),
                "cost_micros": cost,
                "avg_cpc_brl": format_micros(avg_cpc),
                "avg_cpc_micros": avg_cpc,
                "conversions_api": conversions_api,
                "conversion_rate_api": round(conversion_rate_api, 4),
                "avg_cpa_api_brl": format_micros(avg_cpa_api),
                "avg_cpa_api_micros": avg_cpa_api,
                "estimated_conversions_custom": estimated_conversions,
                "estimated_cpa_custom_brl": estimated_cpa_brl,
                "custom_conversion_rate_used": conversion_rate,
            }

        forecast_start = tomorrow.strftime("%Y-%m-%d")
        forecast_end = (tomorrow + timedelta(days=30)).strftime("%Y-%m-%d")
        result["parameters"] = {
            "keywords_count": len(keywords),
            "match_type": match_type,
            "daily_budget_brl": format_micros(daily_budget_micros) if daily_budget_micros else None,
            "max_cpc_brl": format_micros(max_cpc_bid_micros) if max_cpc_bid_micros else None,
            "geo_target_ids": geo_target_ids,
            "language_id": language_id,
            "conversion_rate": conversion_rate,
            "forecast_period": f"{forecast_start} to {forecast_end}",
        }

        return success_response(result)
    except Exception as e:
        logger.error("Failed to get keyword forecast: %s", e, exc_info=True)
        return error_response(f"Failed to get keyword forecast: {e}")


@mcp.tool()
def list_negative_keywords(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str | None, "Filter by campaign ID"] = None,
    limit: Annotated[int, "Maximum results"] = 200,
) -> str:
    """List negative keywords at the campaign level.

    Shows all negative keywords that prevent ads from showing for certain search terms.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        conditions = ["campaign_criterion.negative = true", "campaign_criterion.type = 'KEYWORD'"]
        if campaign_id:
            conditions.append(f"campaign.id = {validate_numeric_id(campaign_id, 'campaign_id')}")

        where = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                campaign_criterion.criterion_id,
                campaign_criterion.keyword.text,
                campaign_criterion.keyword.match_type,
                campaign.id,
                campaign.name
            FROM campaign_criterion
            {where}
            ORDER BY campaign_criterion.keyword.text ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        negatives = []
        for row in response:
            negatives.append({
                "criterion_id": str(row.campaign_criterion.criterion_id),
                "keyword": row.campaign_criterion.keyword.text,
                "match_type": row.campaign_criterion.keyword.match_type.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
            })
        return success_response({"negative_keywords": negatives, "count": len(negatives)})
    except Exception as e:
        logger.error("Failed to list negative keywords: %s", e, exc_info=True)
        return error_response(f"Failed to list negative keywords: {e}")
