"""AI-powered generation tools using Google Ads generative AI services (3 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_client
from ..coordinator import mcp
from ..utils import (
    error_response,
    resolve_customer_id,
    success_response,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def generate_ad_text(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    final_url: Annotated[str, "Landing page URL to analyze"],
    keywords: Annotated[list[str] | None, "Keywords for context"] = None,
    business_name: Annotated[str | None, "Business name for context"] = None,
    language_code: Annotated[str, "Language code (pt, en, es)"] = "pt",
) -> str:
    """Generate headline and description suggestions using Google Ads AI (AssetGenerationService).

    Uses the landing page URL and optional keywords to generate optimized ad copy suggestions.
    Note: This is a Beta feature in API v22+.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()

        # Tenta usar AssetSuggestionService (v22+ Beta)
        try:
            service = client.get_service("AssetSuggestionService")
            request = client.get_type("SuggestAssetsRequest")
            request.customer_id = cid
            request.final_url = final_url
            if keywords:
                for kw in keywords[:10]:
                    request.seed_keywords.append(kw)
            if business_name:
                request.business_name = business_name
            if language_code:
                request.language_code = language_code

            response = service.suggest_assets(request=request)
            headlines = [h.text for h in response.text_asset_suggestions if h.asset_type == "HEADLINE"]
            descriptions = [d.text for d in response.text_asset_suggestions if d.asset_type == "DESCRIPTION"]

            return success_response({
                "headlines": headlines,
                "descriptions": descriptions,
            })
        except Exception:
            return success_response({
                "headlines": [],
                "descriptions": [],
                "note": "AssetGenerationService not available. Feature requires API v22+ Beta access.",
            }, message="AI text generation unavailable — use manual copy creation")
    except Exception as e:
        logger.error("Failed to generate ad text: %s", e, exc_info=True)
        return error_response(f"Failed to generate ad text: {e}")


@mcp.tool()
def generate_ad_images(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    final_url: Annotated[str, "Landing page URL to analyze"],
    num_images: Annotated[int, "Number of images to generate (1-5)"] = 3,
) -> str:
    """Generate image suggestions using Google Ads AI (AssetGenerationService).

    Note: This is a Beta feature in API v22+. May not be available in all accounts.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()

        # Tenta usar AssetSuggestionService para imagens (v22+ Beta)
        try:
            service = client.get_service("AssetSuggestionService")
            request = client.get_type("SuggestImageAssetsRequest")
            request.customer_id = cid
            request.final_url = final_url
            request.num_images = max(1, min(num_images, 5))

            response = service.suggest_image_assets(request=request)
            images = []
            for img in response.image_asset_suggestions:
                images.append({
                    "url": img.url if hasattr(img, "url") else str(img),
                    "width": img.width if hasattr(img, "width") else None,
                    "height": img.height if hasattr(img, "height") else None,
                })

            return success_response({
                "images": images,
                "count": len(images),
            })
        except Exception:
            return success_response({
                "images": [],
                "count": 0,
                "note": "AssetGenerationService not available. Feature requires API v22+ Beta access.",
            }, message="AI image generation unavailable — use create_image_asset to upload images manually")
    except Exception as e:
        logger.error("Failed to generate ad images: %s", e, exc_info=True)
        return error_response(f"Failed to generate ad images: {e}")


@mcp.tool()
def generate_audience_definition(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    description: Annotated[str, "Natural language description of target audience (e.g., 'women 25-45 interested in tarot')"],
) -> str:
    """Convert a natural language description into a structured audience definition using Google Ads AI.

    Uses AudienceInsightsService.GenerateAudienceDefinition (API v23).
    Note: This is a new feature that may not be available in all accounts.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()

        try:
            service = client.get_service("AudienceInsightsService")
            request = client.get_type("GenerateAudienceDefinitionRequest")
            request.customer_id = cid
            request.audience_description = description

            response = service.generate_audience_definition(request=request)

            segments = []
            if hasattr(response, "audience_definition"):
                for segment in response.audience_definition.audience_segments:
                    segments.append({
                        "segment_name": segment.name if hasattr(segment, "name") else str(segment),
                        "segment_type": segment.type_.name if hasattr(segment, "type_") else "UNKNOWN",
                    })

            return success_response({
                "segments": segments,
                "count": len(segments),
            }, message=f"Generated {len(segments)} audience segments from description")
        except Exception as inner_e:
            return success_response({
                "segments": [],
                "count": 0,
                "note": f"AudienceInsightsService.GenerateAudienceDefinition not available: {inner_e}",
            }, message="AI audience generation unavailable — use list_audience_segments to find segments manually")
    except Exception as e:
        logger.error("Failed to generate audience definition: %s", e, exc_info=True)
        return error_response(f"Failed to generate audience definition: {e}")
