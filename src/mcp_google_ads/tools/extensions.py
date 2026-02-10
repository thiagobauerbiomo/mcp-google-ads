"""Ad extension (asset) management tools (6 tools)."""

from __future__ import annotations

from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response


@mcp.tool()
def list_assets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    asset_type: Annotated[str | None, "Filter: SITELINK, CALLOUT, STRUCTURED_SNIPPET, CALL, IMAGE, etc."] = None,
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """List all assets (extensions) for an account."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        type_filter = f"WHERE asset.type = '{asset_type}'" if asset_type else ""

        query = f"""
            SELECT
                asset.id,
                asset.name,
                asset.type,
                asset.sitelink_asset.description1,
                asset.sitelink_asset.description2,
                asset.sitelink_asset.link_text,
                asset.callout_asset.callout_text,
                asset.structured_snippet_asset.header,
                asset.call_asset.phone_number,
                asset.final_urls
            FROM asset
            {type_filter}
            ORDER BY asset.type ASC, asset.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        assets = []
        for row in response:
            asset_data = {
                "asset_id": str(row.asset.id),
                "name": row.asset.name,
                "type": row.asset.type_.name,
                "final_urls": list(row.asset.final_urls),
            }
            # Add type-specific fields
            if row.asset.type_.name == "SITELINK":
                asset_data["link_text"] = row.asset.sitelink_asset.link_text
                asset_data["description1"] = row.asset.sitelink_asset.description1
                asset_data["description2"] = row.asset.sitelink_asset.description2
            elif row.asset.type_.name == "CALLOUT":
                asset_data["callout_text"] = row.asset.callout_asset.callout_text
            elif row.asset.type_.name == "STRUCTURED_SNIPPET":
                asset_data["header"] = row.asset.structured_snippet_asset.header
            elif row.asset.type_.name == "CALL":
                asset_data["phone_number"] = row.asset.call_asset.phone_number

            assets.append(asset_data)
        return success_response({"assets": assets, "count": len(assets)})
    except Exception as e:
        return error_response(f"Failed to list assets: {e}")


@mcp.tool()
def create_sitelink_assets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    sitelinks: Annotated[list[dict], "List of {link_text, final_url, description1?, description2?}"],
) -> str:
    """Create sitelink extension assets.

    Example: [{"link_text": "Contact Us", "final_url": "https://example.com/contact", "description1": "Get in touch", "description2": "We respond fast"}]
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        operations = []
        for sl in sitelinks:
            operation = client.get_type("AssetOperation")
            asset = operation.create
            asset.sitelink_asset.link_text = sl["link_text"]
            asset.final_urls.append(sl["final_url"])
            if sl.get("description1"):
                asset.sitelink_asset.description1 = sl["description1"]
            if sl.get("description2"):
                asset.sitelink_asset.description2 = sl["description2"]
            operations.append(operation)

        response = service.mutate_assets(customer_id=cid, operations=operations)
        results = [r.resource_name for r in response.results]
        return success_response(
            {"created": len(results), "resource_names": results},
            message=f"{len(results)} sitelink assets created",
        )
    except Exception as e:
        return error_response(f"Failed to create sitelinks: {e}")


@mcp.tool()
def create_callout_assets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    callouts: Annotated[list[str], "List of callout texts (each max 25 chars)"],
) -> str:
    """Create callout extension assets.

    Example: ["Free Shipping", "24/7 Support", "Price Match Guarantee"]
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        operations = []
        for text in callouts:
            operation = client.get_type("AssetOperation")
            asset = operation.create
            asset.callout_asset.callout_text = text
            operations.append(operation)

        response = service.mutate_assets(customer_id=cid, operations=operations)
        results = [r.resource_name for r in response.results]
        return success_response(
            {"created": len(results), "resource_names": results},
            message=f"{len(results)} callout assets created",
        )
    except Exception as e:
        return error_response(f"Failed to create callouts: {e}")


@mcp.tool()
def create_structured_snippet_assets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    header: Annotated[str, "Snippet header (e.g., 'Brands', 'Services', 'Types', 'Models')"],
    values: Annotated[list[str], "List of snippet values"],
) -> str:
    """Create a structured snippet extension asset.

    Headers: Amenities, Brands, Courses, Degree programs, Destinations, Featured hotels,
    Insurance coverage, Models, Neighborhoods, Service catalog, Shows, Styles, Types.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        operation = client.get_type("AssetOperation")
        asset = operation.create
        asset.structured_snippet_asset.header = header
        for value in values:
            asset.structured_snippet_asset.values.append(value)

        response = service.mutate_assets(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Structured snippet '{header}' created with {len(values)} values",
        )
    except Exception as e:
        return error_response(f"Failed to create structured snippet: {e}")


@mcp.tool()
def create_call_asset(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    phone_number: Annotated[str, "Phone number (e.g., '+5511999999999')"],
    country_code: Annotated[str, "Country code (e.g., 'BR', 'US')"] = "BR",
    call_tracking: Annotated[bool, "Enable Google call tracking"] = True,
) -> str:
    """Create a call extension asset with a phone number."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        operation = client.get_type("AssetOperation")
        asset = operation.create
        asset.call_asset.phone_number = phone_number
        asset.call_asset.country_code = country_code
        asset.call_asset.call_tracking_enabled = call_tracking

        response = service.mutate_assets(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Call asset created: {phone_number}",
        )
    except Exception as e:
        return error_response(f"Failed to create call asset: {e}")


@mcp.tool()
def remove_asset(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    asset_id: Annotated[str, "The asset ID to remove"],
) -> str:
    """Remove an asset (extension) permanently."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AssetService")

        operation = client.get_type("AssetOperation")
        operation.remove = f"customers/{cid}/assets/{asset_id}"

        response = service.mutate_assets(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Asset {asset_id} removed",
        )
    except Exception as e:
        return error_response(f"Failed to remove asset: {e}")
