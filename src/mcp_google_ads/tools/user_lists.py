"""User list management tools (6 tools)."""

from __future__ import annotations

import hashlib
import logging
from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import (
    error_response,
    resolve_customer_id,
    success_response,
    validate_batch,
    validate_enum_value,
    validate_limit,
    validate_numeric_id,
)

logger = logging.getLogger(__name__)


@mcp.tool()
def list_user_lists(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    list_type: Annotated[str | None, "Filter by type: CRM_BASED, RULE_BASED, REMARKETING, SIMILAR, LOGICAL"] = None,
    limit: Annotated[int, "Maximum number of results"] = 100,
) -> str:
    """List all user lists including remarketing and customer match lists.

    User lists can be used for audience targeting in campaigns.
    """
    try:
        cid = resolve_customer_id(customer_id)
        limit = validate_limit(limit)
        service = get_service("GoogleAdsService")

        type_filter = ""
        if list_type:
            safe_type = validate_enum_value(list_type, "list_type")
            type_filter = f"WHERE user_list.type = '{safe_type}'"

        query = f"""
            SELECT
                user_list.resource_name,
                user_list.id,
                user_list.name,
                user_list.description,
                user_list.type,
                user_list.membership_status,
                user_list.size_for_search,
                user_list.size_for_display,
                user_list.membership_life_span,
                user_list.match_rate_percentage,
                user_list.eligible_for_search,
                user_list.eligible_for_display
            FROM user_list
            {type_filter}
            ORDER BY user_list.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        user_lists = []
        for row in response:
            user_lists.append({
                "resource_name": row.user_list.resource_name,
                "id": str(row.user_list.id),
                "name": row.user_list.name,
                "description": row.user_list.description,
                "type": row.user_list.type_.name,
                "membership_status": row.user_list.membership_status.name,
                "size_for_search": row.user_list.size_for_search,
                "size_for_display": row.user_list.size_for_display,
                "membership_life_span": row.user_list.membership_life_span,
                "match_rate_percentage": row.user_list.match_rate_percentage,
                "eligible_for_search": row.user_list.eligible_for_search,
                "eligible_for_display": row.user_list.eligible_for_display,
            })
        return success_response({"user_lists": user_lists, "count": len(user_lists)})
    except Exception as e:
        logger.error("Failed to list user lists: %s", e, exc_info=True)
        return error_response(f"Failed to list user lists: {e}")


@mcp.tool()
def get_user_list(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    user_list_id: Annotated[str, "The user list ID"],
) -> str:
    """Get detailed information about a specific user list."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_id = validate_numeric_id(user_list_id, "user_list_id")
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                user_list.resource_name,
                user_list.id,
                user_list.name,
                user_list.description,
                user_list.type,
                user_list.membership_status,
                user_list.size_for_search,
                user_list.size_for_display,
                user_list.membership_life_span,
                user_list.match_rate_percentage,
                user_list.eligible_for_search,
                user_list.eligible_for_display
            FROM user_list
            WHERE user_list.id = {safe_id}
        """
        response = service.search(customer_id=cid, query=query)
        user_list_data = None
        for row in response:
            user_list_data = {
                "resource_name": row.user_list.resource_name,
                "id": str(row.user_list.id),
                "name": row.user_list.name,
                "description": row.user_list.description,
                "type": row.user_list.type_.name,
                "membership_status": row.user_list.membership_status.name,
                "size_for_search": row.user_list.size_for_search,
                "size_for_display": row.user_list.size_for_display,
                "membership_life_span": row.user_list.membership_life_span,
                "match_rate_percentage": row.user_list.match_rate_percentage,
                "eligible_for_search": row.user_list.eligible_for_search,
                "eligible_for_display": row.user_list.eligible_for_display,
            }

        if not user_list_data:
            return error_response(f"User list {user_list_id} not found")

        return success_response(user_list_data)
    except Exception as e:
        logger.error("Failed to get user list: %s", e, exc_info=True)
        return error_response(f"Failed to get user list: {e}")


@mcp.tool()
def create_crm_user_list(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "List name"],
    description: Annotated[str | None, "List description"] = None,
    membership_life_span: Annotated[int, "Days to keep members (max 540, 10000=no expiry)"] = 10000,
) -> str:
    """Create a Customer Match (CRM-based) user list.

    After creating, use add_user_list_members to upload customer data (emails, phones).
    Customer Match allows targeting existing customers across Google properties.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("UserListService")

        operation = client.get_type("UserListOperation")
        user_list = operation.create
        user_list.name = name
        if description:
            user_list.description = description
        user_list.membership_life_span = membership_life_span
        user_list.membership_status = client.enums.UserListMembershipStatusEnum.OPEN
        user_list.crm_based_user_list.upload_key_type = client.enums.CustomerMatchUploadKeyTypeEnum.CONTACT_INFO

        response = service.mutate_user_lists(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"user_list_id": new_id, "resource_name": resource_name},
            message=f"Customer Match list '{name}' created",
        )
    except Exception as e:
        logger.error("Failed to create CRM user list: %s", e, exc_info=True)
        return error_response(f"Failed to create CRM user list: {e}")


@mcp.tool()
def add_user_list_members(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    user_list_id: Annotated[str, "The user list ID"],
    emails: Annotated[list[str] | None, "List of email addresses to add (will be SHA256 hashed)"] = None,
    phones: Annotated[list[str] | None, "List of phone numbers in E.164 format (will be SHA256 hashed)"] = None,
) -> str:
    """Add members to a Customer Match user list.

    Emails and phone numbers are automatically SHA256 hashed before upload (Google requirement).
    Provide at least one of emails or phones.
    Maximum 5000 members per call.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_list_id = validate_numeric_id(user_list_id, "user_list_id")

        if not emails and not phones:
            return error_response("At least one of emails or phones must be provided")

        all_items = (emails or []) + (phones or [])
        batch_error = validate_batch(all_items, max_size=5000, item_name="members")
        if batch_error:
            return error_response(batch_error)

        client = get_client()
        job_service = get_service("OfflineUserDataJobService")

        job = client.get_type("OfflineUserDataJob")
        job.type_ = client.enums.OfflineUserDataJobTypeEnum.CUSTOMER_MATCH_USER_LIST
        job.customer_match_user_list_metadata.user_list = f"customers/{cid}/userLists/{safe_list_id}"

        job_response = job_service.create_offline_user_data_job(customer_id=cid, job=job)
        job_resource_name = job_response.resource_name

        operations = []
        if emails:
            for email in emails:
                op = client.get_type("OfflineUserDataJobOperation")
                user_identifier = client.get_type("UserIdentifier")
                user_identifier.hashed_email = hashlib.sha256(email.strip().lower().encode()).hexdigest()
                op.create.user_identifiers.append(user_identifier)
                operations.append(op)

        if phones:
            for phone in phones:
                op = client.get_type("OfflineUserDataJobOperation")
                user_identifier = client.get_type("UserIdentifier")
                user_identifier.hashed_phone_number = hashlib.sha256(phone.strip().encode()).hexdigest()
                op.create.user_identifiers.append(user_identifier)
                operations.append(op)

        job_service.add_offline_user_data_job_operations(
            resource_name=job_resource_name,
            operations=operations,
        )
        job_service.run_offline_user_data_job(resource_name=job_resource_name)

        email_count = len(emails) if emails else 0
        phone_count = len(phones) if phones else 0

        return success_response(
            {
                "user_list_id": safe_list_id,
                "job_resource_name": job_resource_name,
                "emails_added": email_count,
                "phones_added": phone_count,
                "total_members": email_count + phone_count,
            },
            message=f"Added {email_count + phone_count} members to user list {safe_list_id}",
        )
    except Exception as e:
        logger.error("Failed to add user list members: %s", e, exc_info=True)
        return error_response(f"Failed to add user list members: {e}")


@mcp.tool()
def remove_user_list_members(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    user_list_id: Annotated[str, "The user list ID"],
    emails: Annotated[list[str] | None, "List of email addresses to remove"] = None,
    phones: Annotated[list[str] | None, "List of phone numbers to remove"] = None,
) -> str:
    """Remove members from a Customer Match user list.

    Same hashing rules apply. Maximum 5000 members per call.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_list_id = validate_numeric_id(user_list_id, "user_list_id")

        if not emails and not phones:
            return error_response("At least one of emails or phones must be provided")

        all_items = (emails or []) + (phones or [])
        batch_error = validate_batch(all_items, max_size=5000, item_name="members")
        if batch_error:
            return error_response(batch_error)

        client = get_client()
        job_service = get_service("OfflineUserDataJobService")

        job = client.get_type("OfflineUserDataJob")
        job.type_ = client.enums.OfflineUserDataJobTypeEnum.CUSTOMER_MATCH_USER_LIST
        job.customer_match_user_list_metadata.user_list = f"customers/{cid}/userLists/{safe_list_id}"

        job_response = job_service.create_offline_user_data_job(customer_id=cid, job=job)
        job_resource_name = job_response.resource_name

        operations = []
        if emails:
            for email in emails:
                op = client.get_type("OfflineUserDataJobOperation")
                user_identifier = client.get_type("UserIdentifier")
                user_identifier.hashed_email = hashlib.sha256(email.strip().lower().encode()).hexdigest()
                op.remove.user_identifiers.append(user_identifier)
                operations.append(op)

        if phones:
            for phone in phones:
                op = client.get_type("OfflineUserDataJobOperation")
                user_identifier = client.get_type("UserIdentifier")
                user_identifier.hashed_phone_number = hashlib.sha256(phone.strip().encode()).hexdigest()
                op.remove.user_identifiers.append(user_identifier)
                operations.append(op)

        job_service.add_offline_user_data_job_operations(
            resource_name=job_resource_name,
            operations=operations,
        )
        job_service.run_offline_user_data_job(resource_name=job_resource_name)

        email_count = len(emails) if emails else 0
        phone_count = len(phones) if phones else 0

        return success_response(
            {
                "user_list_id": safe_list_id,
                "job_resource_name": job_resource_name,
                "emails_removed": email_count,
                "phones_removed": phone_count,
                "total_members": email_count + phone_count,
            },
            message=f"Removed {email_count + phone_count} members from user list {safe_list_id}",
        )
    except Exception as e:
        logger.error("Failed to remove user list members: %s", e, exc_info=True)
        return error_response(f"Failed to remove user list members: {e}")


@mcp.tool()
def update_user_list(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    user_list_id: Annotated[str, "The user list ID"],
    name: Annotated[str | None, "New name"] = None,
    description: Annotated[str | None, "New description"] = None,
    membership_status: Annotated[str | None, "OPEN or CLOSED"] = None,
) -> str:
    """Update a user list's name, description, or membership status."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_id = validate_numeric_id(user_list_id, "user_list_id")
        client = get_client()
        service = get_service("UserListService")

        if not name and not description and not membership_status:
            return error_response("At least one of name, description, or membership_status must be provided")

        operation = client.get_type("UserListOperation")
        user_list = operation.update
        user_list.resource_name = f"customers/{cid}/userLists/{safe_id}"

        update_fields = []
        if name:
            user_list.name = name
            update_fields.append("name")
        if description:
            user_list.description = description
            update_fields.append("description")
        if membership_status:
            safe_status = validate_enum_value(membership_status, "membership_status")
            user_list.membership_status = getattr(client.enums.UserListMembershipStatusEnum, safe_status)
            update_fields.append("membership_status")

        field_mask = client.get_type("FieldMask")
        field_mask.paths.extend(update_fields)
        client.copy_from(operation.update_mask, field_mask)

        response = service.mutate_user_lists(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name

        return success_response(
            {"user_list_id": safe_id, "resource_name": resource_name, "updated_fields": update_fields},
            message=f"User list {safe_id} updated",
        )
    except Exception as e:
        logger.error("Failed to update user list: %s", e, exc_info=True)
        return error_response(f"Failed to update user list: {e}")
