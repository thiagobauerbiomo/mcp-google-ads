"""Keyword management tools (8 tools)."""

from __future__ import annotations

from typing import Annotated

from google.api_core import protobuf_helpers

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response, to_micros


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
        service = get_service("GoogleAdsService")
        conditions = ["ad_group_criterion.type = 'KEYWORD'"]
        if ad_group_id:
            conditions.append(f"ad_group.id = {ad_group_id}")
        if campaign_id:
            conditions.append(f"campaign.id = {campaign_id}")
        if status_filter:
            conditions.append(f"ad_group_criterion.status = '{status_filter}'")
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
                "cpc_bid": row.ad_group_criterion.cpc_bid_micros / 1_000_000 if row.ad_group_criterion.cpc_bid_micros else None,
                "quality_score": row.ad_group_criterion.quality_info.quality_score,
                "ad_group_id": str(row.ad_group.id),
                "campaign_id": str(row.campaign.id),
            })
        return success_response({"keywords": keywords, "count": len(keywords)})
    except Exception as e:
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
        client = get_client()
        service = get_service("AdGroupCriterionService")

        operations = []
        for kw in keywords:
            operation = client.get_type("AdGroupCriterionOperation")
            criterion = operation.create
            criterion.ad_group = f"customers/{cid}/adGroups/{ad_group_id}"
            criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            criterion.keyword.text = kw["text"]
            criterion.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum, kw.get("match_type", "BROAD")
            )
            if cpc_bid is not None:
                criterion.cpc_bid_micros = to_micros(cpc_bid)
            operations.append(operation)

        response = service.mutate_ad_group_criteria(customer_id=cid, operations=operations)
        results = [r.resource_name for r in response.results]

        return success_response(
            {"added": len(results), "resource_names": results},
            message=f"{len(results)} keywords added to ad group {ad_group_id}",
        )
    except Exception as e:
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
        client = get_client()
        service = get_service("CampaignCriterionService")

        operations = []
        for kw in keywords:
            operation = client.get_type("CampaignCriterionOperation")
            criterion = operation.create
            criterion.campaign = f"customers/{cid}/campaigns/{campaign_id}"
            criterion.negative = True
            criterion.keyword.text = kw["text"]
            criterion.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum, kw.get("match_type", "BROAD")
            )
            operations.append(operation)

        response = service.mutate_campaign_criteria(customer_id=cid, operations=operations)
        return success_response(
            {"added": len(response.results)},
            message=f"{len(response.results)} negative keywords added to campaign {campaign_id}",
        )
    except Exception as e:
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
        client = get_client()
        service = get_service("SharedCriterionService")

        operations = []
        for kw_text in keywords:
            operation = client.get_type("SharedCriterionOperation")
            criterion = operation.create
            criterion.shared_set = f"customers/{cid}/sharedSets/{shared_set_id}"
            criterion.keyword.text = kw_text
            criterion.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum, match_type
            )
            operations.append(operation)

        response = service.mutate_shared_criteria(customer_id=cid, operations=operations)
        return success_response(
            {"added": len(response.results)},
            message=f"{len(response.results)} negatives added to shared set {shared_set_id}",
        )
    except Exception as e:
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
        return error_response(f"Failed to generate keyword ideas: {e}")


@mcp.tool()
def get_keyword_forecast(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    keywords: Annotated[list[str], "Keywords to forecast"],
    match_type: Annotated[str, "Match type: EXACT, PHRASE, BROAD"] = "BROAD",
    daily_budget_micros: Annotated[int | None, "Daily budget in micros for forecast"] = None,
) -> str:
    """Get performance forecasts for keywords (clicks, impressions, cost estimates).

    Uses the Keyword Planner forecast endpoint for campaign planning.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("KeywordPlanIdeaService")

        request = client.get_type("GenerateKeywordForecastMetricsRequest")
        request.customer_id = cid

        campaign = request.campaign
        if daily_budget_micros:
            campaign.daily_budget_micros = daily_budget_micros

        for kw_text in keywords:
            ad_group = client.get_type("KeywordForecastAdGroup")
            biddable_keyword = client.get_type("BiddableKeyword")
            biddable_keyword.keyword.text = kw_text
            biddable_keyword.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum, match_type
            )
            ad_group.biddable_keywords.append(biddable_keyword)
            campaign.ad_groups.append(ad_group)

        response = service.generate_keyword_forecast_metrics(request=request)

        forecasts = []
        if response.campaign_forecast_metrics:
            m = response.campaign_forecast_metrics
            forecasts.append({
                "type": "campaign_total",
                "clicks": m.clicks,
                "impressions": m.impressions,
                "cost_micros": m.cost_micros,
                "ctr": m.ctr,
                "avg_cpc_micros": m.average_cpc_micros,
            })

        return success_response({"forecasts": forecasts})
    except Exception as e:
        return error_response(f"Failed to get keyword forecast: {e}")
