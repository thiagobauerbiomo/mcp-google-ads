"""Label management tools (8 tools)."""

from __future__ import annotations

from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response


@mcp.tool()
def list_labels(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum number of results"] = 100,
) -> str:
    """List all labels for a customer account.

    Returns label ID, name, description, background color, and status.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                label.id,
                label.name,
                label.description,
                label.text_label.background_color,
                label.text_label.description,
                label.status
            FROM label
            ORDER BY label.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        labels = []
        for row in response:
            labels.append({
                "label_id": str(row.label.id),
                "name": row.label.name,
                "description": row.label.description,
                "background_color": row.label.text_label.background_color,
                "status": row.label.status.name,
            })
        return success_response({"labels": labels, "count": len(labels)})
    except Exception as e:
        return error_response(f"Failed to list labels: {e}")


@mcp.tool()
def create_label(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Label name"],
    description: Annotated[str | None, "Label description"] = None,
    background_color: Annotated[str | None, "Hex color (e.g., '#FF0000')"] = None,
) -> str:
    """Create a new label for organizing resources."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("LabelService")

        operation = client.get_type("LabelOperation")
        label = operation.create
        label.name = name
        if description:
            label.text_label.description = description
        if background_color:
            label.text_label.background_color = background_color

        response = service.mutate_labels(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"label_id": new_id, "resource_name": resource_name},
            message=f"Label '{name}' created",
        )
    except Exception as e:
        return error_response(f"Failed to create label: {e}")


@mcp.tool()
def remove_label(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    label_id: Annotated[str, "The label ID to remove"],
) -> str:
    """Remove a label permanently."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("LabelService")

        operation = client.get_type("LabelOperation")
        operation.remove = f"customers/{cid}/labels/{label_id}"

        response = service.mutate_labels(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Label {label_id} removed",
        )
    except Exception as e:
        return error_response(f"Failed to remove label: {e}")


@mcp.tool()
def apply_label_to_campaign(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    campaign_id: Annotated[str, "The campaign ID"],
    label_id: Annotated[str, "The label ID to apply"],
) -> str:
    """Apply a label to a campaign for organization and filtering."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignLabelService")

        operation = client.get_type("CampaignLabelOperation")
        campaign_label = operation.create
        campaign_label.campaign = f"customers/{cid}/campaigns/{campaign_id}"
        campaign_label.label = f"customers/{cid}/labels/{label_id}"

        response = service.mutate_campaign_labels(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Label {label_id} applied to campaign {campaign_id}",
        )
    except Exception as e:
        return error_response(f"Failed to apply label to campaign: {e}")


@mcp.tool()
def apply_label_to_ad_group(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    label_id: Annotated[str, "The label ID to apply"],
) -> str:
    """Apply a label to an ad group."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupLabelService")

        operation = client.get_type("AdGroupLabelOperation")
        ad_group_label = operation.create
        ad_group_label.ad_group = f"customers/{cid}/adGroups/{ad_group_id}"
        ad_group_label.label = f"customers/{cid}/labels/{label_id}"

        response = service.mutate_ad_group_labels(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Label {label_id} applied to ad group {ad_group_id}",
        )
    except Exception as e:
        return error_response(f"Failed to apply label to ad group: {e}")


@mcp.tool()
def apply_label_to_ad(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    ad_id: Annotated[str, "The ad ID"],
    label_id: Annotated[str, "The label ID to apply"],
) -> str:
    """Apply a label to an ad."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupAdLabelService")

        operation = client.get_type("AdGroupAdLabelOperation")
        ad_label = operation.create
        ad_label.ad_group_ad = f"customers/{cid}/adGroupAds/{ad_group_id}~{ad_id}"
        ad_label.label = f"customers/{cid}/labels/{label_id}"

        response = service.mutate_ad_group_ad_labels(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Label {label_id} applied to ad {ad_id}",
        )
    except Exception as e:
        return error_response(f"Failed to apply label to ad: {e}")


@mcp.tool()
def apply_label_to_keyword(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    ad_group_id: Annotated[str, "The ad group ID"],
    criterion_id: Annotated[str, "The keyword criterion ID"],
    label_id: Annotated[str, "The label ID to apply"],
) -> str:
    """Apply a label to a keyword criterion."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AdGroupCriterionLabelService")

        operation = client.get_type("AdGroupCriterionLabelOperation")
        criterion_label = operation.create
        criterion_label.ad_group_criterion = f"customers/{cid}/adGroupCriteria/{ad_group_id}~{criterion_id}"
        criterion_label.label = f"customers/{cid}/labels/{label_id}"

        response = service.mutate_ad_group_criterion_labels(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Label {label_id} applied to keyword {criterion_id}",
        )
    except Exception as e:
        return error_response(f"Failed to apply label to keyword: {e}")


@mcp.tool()
def remove_label_from_resource(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    resource_type: Annotated[str, "Resource type: campaign, ad_group, ad, keyword"],
    resource_name: Annotated[str, "The full resource name of the label association (e.g., customers/123/campaignLabels/456~789)"],
) -> str:
    """Remove a label from a resource (campaign, ad group, ad, or keyword).

    Use the resource_name returned when listing labels for a specific resource type.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()

        service_map = {
            "campaign": ("CampaignLabelService", "CampaignLabelOperation", "mutate_campaign_labels"),
            "ad_group": ("AdGroupLabelService", "AdGroupLabelOperation", "mutate_ad_group_labels"),
            "ad": ("AdGroupAdLabelService", "AdGroupAdLabelOperation", "mutate_ad_group_ad_labels"),
            "keyword": ("AdGroupCriterionLabelService", "AdGroupCriterionLabelOperation", "mutate_ad_group_criterion_labels"),
        }

        if resource_type not in service_map:
            return error_response(f"Invalid resource_type '{resource_type}'. Must be: campaign, ad_group, ad, keyword")

        service_name, operation_type, mutate_method = service_map[resource_type]
        service = get_service(service_name)

        operation = client.get_type(operation_type)
        operation.remove = resource_name

        response = getattr(service, mutate_method)(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Label removed from {resource_type}",
        )
    except Exception as e:
        return error_response(f"Failed to remove label from {resource_type}: {e}")
