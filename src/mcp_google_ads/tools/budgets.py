"""Budget management tools (4 tools)."""

from __future__ import annotations

from typing import Annotated

from google.api_core import protobuf_helpers

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, format_micros, resolve_customer_id, success_response, to_micros, validate_numeric_id


@mcp.tool()
def list_budgets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum results"] = 100,
) -> str:
    """List all campaign budgets for an account."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                campaign_budget.id,
                campaign_budget.name,
                campaign_budget.amount_micros,
                campaign_budget.delivery_method,
                campaign_budget.status,
                campaign_budget.total_amount_micros,
                campaign_budget.explicitly_shared
            FROM campaign_budget
            ORDER BY campaign_budget.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        budgets = []
        for row in response:
            budgets.append({
                "budget_id": str(row.campaign_budget.id),
                "name": row.campaign_budget.name,
                "amount_micros": row.campaign_budget.amount_micros,
                "amount": format_micros(row.campaign_budget.amount_micros),
                "delivery_method": row.campaign_budget.delivery_method.name,
                "status": row.campaign_budget.status.name,
                "total_amount_micros": row.campaign_budget.total_amount_micros,
                "shared": row.campaign_budget.explicitly_shared,
            })
        return success_response({"budgets": budgets, "count": len(budgets)})
    except Exception as e:
        return error_response(f"Failed to list budgets: {e}")


@mcp.tool()
def get_budget(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    budget_id: Annotated[str, "The budget ID"],
) -> str:
    """Get detailed information about a specific campaign budget."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_id = validate_numeric_id(budget_id, "budget_id")
        service = get_service("GoogleAdsService")
        query = f"""
            SELECT
                campaign_budget.id,
                campaign_budget.name,
                campaign_budget.amount_micros,
                campaign_budget.delivery_method,
                campaign_budget.status,
                campaign_budget.total_amount_micros,
                campaign_budget.explicitly_shared,
                campaign_budget.reference_count,
                campaign_budget.recommended_budget_amount_micros,
                campaign_budget.recommended_budget_estimated_change_weekly_clicks,
                campaign_budget.recommended_budget_estimated_change_weekly_interactions
            FROM campaign_budget
            WHERE campaign_budget.id = {safe_id}
        """
        response = service.search(customer_id=cid, query=query)
        for row in response:
            data = {
                "budget_id": str(row.campaign_budget.id),
                "name": row.campaign_budget.name,
                "amount_micros": row.campaign_budget.amount_micros,
                "amount": format_micros(row.campaign_budget.amount_micros),
                "delivery_method": row.campaign_budget.delivery_method.name,
                "status": row.campaign_budget.status.name,
                "shared": row.campaign_budget.explicitly_shared,
                "reference_count": row.campaign_budget.reference_count,
                "recommended_amount_micros": row.campaign_budget.recommended_budget_amount_micros,
                "recommended_change_weekly_clicks": row.campaign_budget.recommended_budget_estimated_change_weekly_clicks,
            }
            return success_response(data)
        return error_response(f"Budget {budget_id} not found")
    except Exception as e:
        return error_response(f"Failed to get budget: {e}")


@mcp.tool()
def create_budget(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Budget name"],
    amount: Annotated[float, "Daily budget amount in account currency"],
    delivery_method: Annotated[str, "STANDARD or ACCELERATED"] = "STANDARD",
    shared: Annotated[bool, "Whether this budget can be shared across campaigns"] = False,
) -> str:
    """Create a new campaign budget."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignBudgetService")

        operation = client.get_type("CampaignBudgetOperation")
        budget = operation.create
        budget.name = name
        budget.amount_micros = to_micros(amount)
        budget.delivery_method = getattr(
            client.enums.BudgetDeliveryMethodEnum, delivery_method
        )
        budget.explicitly_shared = shared

        response = service.mutate_campaign_budgets(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"budget_id": new_id, "resource_name": resource_name},
            message=f"Budget '{name}' created ({amount} daily)",
        )
    except Exception as e:
        return error_response(f"Failed to create budget: {e}")


@mcp.tool()
def update_budget(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    budget_id: Annotated[str, "The budget ID to update"],
    amount: Annotated[float | None, "New daily budget amount in account currency"] = None,
    name: Annotated[str | None, "New budget name"] = None,
    delivery_method: Annotated[str | None, "STANDARD or ACCELERATED"] = None,
) -> str:
    """Update an existing campaign budget amount, name, or delivery method."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("CampaignBudgetService")

        operation = client.get_type("CampaignBudgetOperation")
        budget = operation.update
        budget.resource_name = f"customers/{cid}/campaignBudgets/{budget_id}"

        fields = []
        if amount is not None:
            budget.amount_micros = to_micros(amount)
            fields.append("amount_micros")
        if name is not None:
            budget.name = name
            fields.append("name")
        if delivery_method is not None:
            budget.delivery_method = getattr(
                client.enums.BudgetDeliveryMethodEnum, delivery_method
            )
            fields.append("delivery_method")

        if not fields:
            return error_response("No fields to update")

        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=fields),
        )

        response = service.mutate_campaign_budgets(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Budget {budget_id} updated",
        )
    except Exception as e:
        return error_response(f"Failed to update budget: {e}")
