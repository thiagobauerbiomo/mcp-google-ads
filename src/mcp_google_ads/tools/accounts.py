"""Account management tools (4 tools)."""

from __future__ import annotations

from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, proto_to_dict, resolve_customer_id, success_response


@mcp.tool()
def list_accessible_customers() -> str:
    """List all Google Ads customer accounts accessible with the current credentials.

    Returns a list of customer resource names that the authenticated user can access.
    Use this as the first step to discover available accounts.
    """
    try:
        service = get_service("CustomerService")
        response = service.list_accessible_customers()
        customer_ids = [rn.split("/")[-1] for rn in response.resource_names]
        return success_response(
            {"customer_ids": customer_ids, "count": len(customer_ids)},
            message="Accessible customers retrieved",
        )
    except Exception as e:
        return error_response(f"Failed to list accessible customers: {e}")


@mcp.tool()
def get_customer_info(
    customer_id: Annotated[str, "The Google Ads customer ID (without dashes)"],
) -> str:
    """Get detailed information about a specific Google Ads customer account.

    Returns account name, currency, timezone, status, and other key details.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        query = """
            SELECT
                customer.id,
                customer.descriptive_name,
                customer.currency_code,
                customer.time_zone,
                customer.status,
                customer.manager,
                customer.test_account,
                customer.auto_tagging_enabled
            FROM customer
            LIMIT 1
        """
        response = service.search(customer_id=cid, query=query)
        for row in response:
            data = {
                "customer_id": str(row.customer.id),
                "name": row.customer.descriptive_name,
                "currency": row.customer.currency_code,
                "timezone": row.customer.time_zone,
                "status": row.customer.status.name,
                "is_manager": row.customer.manager,
                "is_test_account": row.customer.test_account,
                "auto_tagging": row.customer.auto_tagging_enabled,
            }
            return success_response(data)
        return error_response("No customer data found")
    except Exception as e:
        return error_response(f"Failed to get customer info: {e}")


@mcp.tool()
def get_account_hierarchy(
    customer_id: Annotated[str | None, "MCC customer ID. Uses login_customer_id if not provided."] = None,
) -> str:
    """Get the full account hierarchy under an MCC (Manager) account.

    Shows all sub-accounts, their names, and whether they are managers themselves.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        query = """
            SELECT
                customer_client.client_customer,
                customer_client.id,
                customer_client.descriptive_name,
                customer_client.level,
                customer_client.manager,
                customer_client.status,
                customer_client.currency_code,
                customer_client.time_zone
            FROM customer_client
            WHERE customer_client.level <= 1
            ORDER BY customer_client.level ASC, customer_client.descriptive_name ASC
        """
        response = service.search(customer_id=cid, query=query)
        accounts = []
        for row in response:
            accounts.append({
                "customer_id": str(row.customer_client.id),
                "name": row.customer_client.descriptive_name,
                "level": row.customer_client.level,
                "is_manager": row.customer_client.manager,
                "status": row.customer_client.status.name,
                "currency": row.customer_client.currency_code,
                "timezone": row.customer_client.time_zone,
            })
        return success_response({"accounts": accounts, "count": len(accounts)})
    except Exception as e:
        return error_response(f"Failed to get account hierarchy: {e}")


@mcp.tool()
def list_customer_clients(
    customer_id: Annotated[str | None, "MCC customer ID. Uses login_customer_id if not provided."] = None,
) -> str:
    """List all client accounts under an MCC with basic info and spend status.

    Similar to hierarchy but includes more details useful for account selection.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        query = """
            SELECT
                customer_client.id,
                customer_client.descriptive_name,
                customer_client.manager,
                customer_client.status,
                customer_client.currency_code
            FROM customer_client
            WHERE customer_client.manager = false
            ORDER BY customer_client.descriptive_name ASC
        """
        response = service.search(customer_id=cid, query=query)
        clients = []
        for row in response:
            clients.append({
                "customer_id": str(row.customer_client.id),
                "name": row.customer_client.descriptive_name,
                "status": row.customer_client.status.name,
                "currency": row.customer_client.currency_code,
            })
        return success_response({"clients": clients, "count": len(clients)})
    except Exception as e:
        return error_response(f"Failed to list customer clients: {e}")
