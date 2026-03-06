"""Account budget management tools (5 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import (
    error_response,
    format_micros,
    resolve_customer_id,
    success_response,
    to_micros,
    validate_enum_value,
    validate_limit,
    validate_numeric_id,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def list_account_budgets(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """List account-level budgets.

    Account budgets set spending limits for the entire account over a time period.
    Different from campaign budgets — these control total account spend.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                account_budget.resource_name,
                account_budget.id,
                account_budget.name,
                account_budget.status,
                account_budget.amount_micros,
                account_budget.total_adjustments_micros,
                account_budget.approved_start_date_time,
                account_budget.approved_end_date_time,
                account_budget.proposed_start_date_time,
                account_budget.proposed_end_date_time,
                account_budget.approved_spending_limit_micros,
                account_budget.proposed_spending_limit_micros,
                account_budget.purchase_order_number
            FROM account_budget
            ORDER BY account_budget.status ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        budgets = []
        for row in response:
            budgets.append({
                "resource_name": row.account_budget.resource_name,
                "id": row.account_budget.id,
                "name": row.account_budget.name,
                "status": row.account_budget.status.name,
                "amount": format_micros(row.account_budget.amount_micros),
                "total_adjustments": format_micros(row.account_budget.total_adjustments_micros),
                "approved_start_date_time": row.account_budget.approved_start_date_time,
                "approved_end_date_time": row.account_budget.approved_end_date_time,
                "proposed_start_date_time": row.account_budget.proposed_start_date_time,
                "proposed_end_date_time": row.account_budget.proposed_end_date_time,
                "approved_spending_limit": format_micros(row.account_budget.approved_spending_limit_micros),
                "proposed_spending_limit": format_micros(row.account_budget.proposed_spending_limit_micros),
                "purchase_order_number": row.account_budget.purchase_order_number,
            })
        return success_response({"account_budgets": budgets, "count": len(budgets)})
    except Exception as e:
        logger.error("Failed to list account budgets: %s", e, exc_info=True)
        return error_response(f"Failed to list account budgets: {e}")


@mcp.tool()
def get_account_budget(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    account_budget_id: Annotated[str, "The account budget ID"],
) -> str:
    """Get detailed information about a specific account budget."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_id = validate_numeric_id(account_budget_id, "account_budget_id")
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                account_budget.resource_name,
                account_budget.id,
                account_budget.name,
                account_budget.status,
                account_budget.amount_micros,
                account_budget.total_adjustments_micros,
                account_budget.approved_start_date_time,
                account_budget.approved_end_date_time,
                account_budget.proposed_start_date_time,
                account_budget.proposed_end_date_time,
                account_budget.approved_spending_limit_micros,
                account_budget.proposed_spending_limit_micros,
                account_budget.purchase_order_number
            FROM account_budget
            WHERE account_budget.id = {safe_id}
        """
        response = service.search(customer_id=cid, query=query)
        budget_data = None
        for row in response:
            budget_data = {
                "resource_name": row.account_budget.resource_name,
                "id": row.account_budget.id,
                "name": row.account_budget.name,
                "status": row.account_budget.status.name,
                "amount": format_micros(row.account_budget.amount_micros),
                "total_adjustments": format_micros(row.account_budget.total_adjustments_micros),
                "approved_start_date_time": row.account_budget.approved_start_date_time,
                "approved_end_date_time": row.account_budget.approved_end_date_time,
                "proposed_start_date_time": row.account_budget.proposed_start_date_time,
                "proposed_end_date_time": row.account_budget.proposed_end_date_time,
                "approved_spending_limit": format_micros(row.account_budget.approved_spending_limit_micros),
                "proposed_spending_limit": format_micros(row.account_budget.proposed_spending_limit_micros),
                "purchase_order_number": row.account_budget.purchase_order_number,
            }

        if not budget_data:
            return error_response(f"Account budget {account_budget_id} not found")

        return success_response(budget_data)
    except Exception as e:
        logger.error("Failed to get account budget: %s", e, exc_info=True)
        return error_response(f"Failed to get account budget: {e}")


@mcp.tool()
def list_account_budget_proposals(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """List account budget proposals.

    Budget proposals are requests to create, update, or remove account budgets.
    They may require approval by the MCC.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                account_budget_proposal.resource_name,
                account_budget_proposal.id,
                account_budget_proposal.account_budget,
                account_budget_proposal.proposal_type,
                account_budget_proposal.status,
                account_budget_proposal.proposed_name,
                account_budget_proposal.proposed_start_date_time,
                account_budget_proposal.proposed_end_date_time,
                account_budget_proposal.proposed_spending_limit_micros,
                account_budget_proposal.proposed_purchase_order_number,
                account_budget_proposal.approved_start_date_time,
                account_budget_proposal.approved_end_date_time,
                account_budget_proposal.approved_spending_limit_micros,
                account_budget_proposal.creation_date_time,
                account_budget_proposal.approval_date_time
            FROM account_budget_proposal
            ORDER BY account_budget_proposal.creation_date_time DESC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        proposals = []
        for row in response:
            proposals.append({
                "resource_name": row.account_budget_proposal.resource_name,
                "id": row.account_budget_proposal.id,
                "account_budget": row.account_budget_proposal.account_budget,
                "proposal_type": row.account_budget_proposal.proposal_type.name,
                "status": row.account_budget_proposal.status.name,
                "proposed_name": row.account_budget_proposal.proposed_name,
                "proposed_start_date_time": row.account_budget_proposal.proposed_start_date_time,
                "proposed_end_date_time": row.account_budget_proposal.proposed_end_date_time,
                "proposed_spending_limit": format_micros(row.account_budget_proposal.proposed_spending_limit_micros),
                "proposed_purchase_order_number": row.account_budget_proposal.proposed_purchase_order_number,
                "approved_start_date_time": row.account_budget_proposal.approved_start_date_time,
                "approved_end_date_time": row.account_budget_proposal.approved_end_date_time,
                "approved_spending_limit": format_micros(row.account_budget_proposal.approved_spending_limit_micros),
                "creation_date_time": row.account_budget_proposal.creation_date_time,
                "approval_date_time": row.account_budget_proposal.approval_date_time,
            })
        return success_response({"proposals": proposals, "count": len(proposals)})
    except Exception as e:
        logger.error("Failed to list account budget proposals: %s", e, exc_info=True)
        return error_response(f"Failed to list account budget proposals: {e}")


@mcp.tool()
def create_account_budget_proposal(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    proposal_type: Annotated[str, "Type: CREATE, UPDATE, REMOVE, END"],
    billing_setup_id: Annotated[str, "The billing setup ID"],
    spending_limit: Annotated[float | None, "Spending limit in currency units (e.g. 1000.00 for R$1000)"] = None,
    name: Annotated[str | None, "Budget name"] = None,
    start_date_time: Annotated[str | None, "Start datetime (YYYY-MM-DD HH:MM:SS)"] = None,
    end_date_time: Annotated[str | None, "End datetime (YYYY-MM-DD HH:MM:SS)"] = None,
    account_budget_id: Annotated[str | None, "Required for UPDATE/REMOVE/END — the existing account budget ID"] = None,
) -> str:
    """Create an account budget proposal.

    For CREATE: sets up a new account budget with spending limits.
    For UPDATE: modifies an existing account budget.
    For REMOVE/END: ends an existing account budget.

    Proposals may require MCC approval before taking effect.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("AccountBudgetProposalService")

        operation = client.get_type("AccountBudgetProposalOperation")
        proposal = operation.create

        safe_type = validate_enum_value(proposal_type, "proposal_type")
        proposal.proposal_type = getattr(client.enums.AccountBudgetProposalTypeEnum, safe_type)

        safe_billing_id = validate_numeric_id(billing_setup_id, "billing_setup_id")
        proposal.billing_setup = f"customers/{cid}/billingSetups/{safe_billing_id}"

        if account_budget_id:
            safe_ab_id = validate_numeric_id(account_budget_id, "account_budget_id")
            proposal.account_budget = f"customers/{cid}/accountBudgets/{safe_ab_id}"

        if name:
            proposal.proposed_name = name
        if spending_limit is not None:
            proposal.proposed_spending_limit_micros = to_micros(spending_limit)
        if start_date_time:
            proposal.proposed_start_date_time = start_date_time
        if end_date_time:
            proposal.proposed_end_date_time = end_date_time

        response = service.mutate_account_budget_proposal(customer_id=cid, operation=operation)
        resource_name = response.result.resource_name
        proposal_id = resource_name.split("/")[-1]

        return success_response(
            {
                "proposal_id": proposal_id,
                "resource_name": resource_name,
                "proposal_type": safe_type,
            },
            message=f"Account budget proposal created ({safe_type})",
        )
    except Exception as e:
        logger.error("Failed to create account budget proposal: %s", e, exc_info=True)
        return error_response(f"Failed to create account budget proposal: {e}")


@mcp.tool()
def remove_account_budget_proposal(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    proposal_id: Annotated[str, "The account budget proposal ID"],
) -> str:
    """Remove (cancel) a pending account budget proposal.

    Only works on proposals that haven't been approved yet.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_proposal_id = validate_numeric_id(proposal_id, "proposal_id")
        client = get_client()
        service = get_service("AccountBudgetProposalService")

        operation = client.get_type("AccountBudgetProposalOperation")
        operation.remove = f"customers/{cid}/accountBudgetProposals/{safe_proposal_id}"

        response = service.mutate_account_budget_proposal(customer_id=cid, operation=operation)

        return success_response(
            {
                "proposal_id": proposal_id,
                "resource_name": response.result.resource_name,
                "action": "removed",
            },
            message=f"Account budget proposal {proposal_id} removed",
        )
    except Exception as e:
        logger.error("Failed to remove account budget proposal: %s", e, exc_info=True)
        return error_response(f"Failed to remove account budget proposal: {e}")
