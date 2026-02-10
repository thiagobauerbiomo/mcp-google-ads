"""Account management and information tools (3 tools)."""

from __future__ import annotations

from typing import Annotated

from ..auth import get_service
from ..coordinator import mcp
from ..utils import error_response, format_micros, resolve_customer_id, success_response


@mcp.tool()
def list_account_links(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum number of results"] = 100,
) -> str:
    """List all account links (Google Analytics, Merchant Center, etc.).

    Shows linked accounts and their status.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                account_link.account_link_id,
                account_link.status,
                account_link.type,
                account_link.linked_account_type
            FROM account_link
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        links = []
        for row in response:
            links.append({
                "account_link_id": str(row.account_link.account_link_id),
                "status": row.account_link.status.name,
                "type": row.account_link.type_.name,
                "linked_account_type": row.account_link.linked_account_type.name,
            })
        return success_response({"account_links": links, "count": len(links)})
    except Exception as e:
        return error_response(f"Failed to list account links: {e}")


@mcp.tool()
def get_billing_info(
    customer_id: Annotated[str, "The Google Ads customer ID"],
) -> str:
    """Get billing setup information for the account.

    Returns billing status, payment type, and payment details.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        query = """
            SELECT
                billing_setup.id,
                billing_setup.status,
                billing_setup.payments_account,
                billing_setup.payments_account_info.payments_account_id,
                billing_setup.payments_account_info.payments_account_name,
                billing_setup.payments_account_info.payments_profile_id,
                billing_setup.payments_account_info.payments_profile_name
            FROM billing_setup
            WHERE billing_setup.status = 'APPROVED'
        """
        response = service.search(customer_id=cid, query=query)
        setups = []
        for row in response:
            setups.append({
                "billing_setup_id": str(row.billing_setup.id),
                "status": row.billing_setup.status.name,
                "payments_account": row.billing_setup.payments_account,
                "payments_account_id": row.billing_setup.payments_account_info.payments_account_id,
                "payments_account_name": row.billing_setup.payments_account_info.payments_account_name,
                "payments_profile_id": row.billing_setup.payments_account_info.payments_profile_id,
                "payments_profile_name": row.billing_setup.payments_account_info.payments_profile_name,
            })
        return success_response({"billing_setups": setups, "count": len(setups)})
    except Exception as e:
        return error_response(f"Failed to get billing info: {e}")


@mcp.tool()
def list_account_users(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum number of results"] = 100,
) -> str:
    """List all users with access to the account.

    Returns user email, access role, and invitation status.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                customer_user_access.user_id,
                customer_user_access.email_address,
                customer_user_access.access_role,
                customer_user_access.access_creation_date_time,
                customer_user_access.inviter_user_email_address
            FROM customer_user_access
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        users = []
        for row in response:
            users.append({
                "user_id": str(row.customer_user_access.user_id),
                "email": row.customer_user_access.email_address,
                "access_role": row.customer_user_access.access_role.name,
                "access_created": row.customer_user_access.access_creation_date_time,
                "inviter_email": row.customer_user_access.inviter_user_email_address,
            })
        return success_response({"users": users, "count": len(users)})
    except Exception as e:
        return error_response(f"Failed to list account users: {e}")
