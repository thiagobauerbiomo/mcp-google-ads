"""Conversion tracking and management tools (6 tools)."""

from __future__ import annotations

from typing import Annotated

from google.api_core import protobuf_helpers

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, format_micros, resolve_customer_id, success_response, validate_numeric_id, validate_status


@mcp.tool()
def list_conversion_actions(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    status_filter: Annotated[str | None, "Filter by status: ENABLED, PAUSED, REMOVED, HIDDEN"] = None,
    limit: Annotated[int, "Maximum number of results"] = 100,
) -> str:
    """List all conversion actions for an account.

    Returns conversion action details including type, category, counting type, and value settings.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")
        status_clause = f"WHERE conversion_action.status = '{validate_status(status_filter)}'" if status_filter else ""

        query = f"""
            SELECT
                conversion_action.id,
                conversion_action.name,
                conversion_action.type,
                conversion_action.category,
                conversion_action.status,
                conversion_action.counting_type,
                conversion_action.value_settings.default_value,
                conversion_action.value_settings.always_use_default_value,
                conversion_action.attribution_model_settings.attribution_model,
                conversion_action.click_through_lookback_window_days,
                conversion_action.include_in_conversions_metric
            FROM conversion_action
            {status_clause}
            ORDER BY conversion_action.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        actions = []
        for row in response:
            actions.append({
                "conversion_action_id": str(row.conversion_action.id),
                "name": row.conversion_action.name,
                "type": row.conversion_action.type_.name,
                "category": row.conversion_action.category.name,
                "status": row.conversion_action.status.name,
                "counting_type": row.conversion_action.counting_type.name,
                "default_value": row.conversion_action.value_settings.default_value,
                "always_use_default": row.conversion_action.value_settings.always_use_default_value,
                "attribution_model": row.conversion_action.attribution_model_settings.attribution_model.name,
                "lookback_window_days": row.conversion_action.click_through_lookback_window_days,
                "include_in_conversions": row.conversion_action.include_in_conversions_metric,
            })
        return success_response({"conversion_actions": actions, "count": len(actions)})
    except Exception as e:
        return error_response(f"Failed to list conversion actions: {e}")


@mcp.tool()
def get_conversion_action(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    conversion_action_id: Annotated[str, "The conversion action ID"],
) -> str:
    """Get detailed information about a specific conversion action."""
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                conversion_action.id,
                conversion_action.name,
                conversion_action.type,
                conversion_action.category,
                conversion_action.status,
                conversion_action.counting_type,
                conversion_action.value_settings.default_value,
                conversion_action.value_settings.always_use_default_value,
                conversion_action.attribution_model_settings.attribution_model,
                conversion_action.click_through_lookback_window_days,
                conversion_action.view_through_lookback_window_days,
                conversion_action.include_in_conversions_metric,
                conversion_action.tag_snippets
            FROM conversion_action
            WHERE conversion_action.id = {validate_numeric_id(conversion_action_id, "conversion_action_id")}
        """
        response = service.search(customer_id=cid, query=query)
        for row in response:
            data = {
                "conversion_action_id": str(row.conversion_action.id),
                "name": row.conversion_action.name,
                "type": row.conversion_action.type_.name,
                "category": row.conversion_action.category.name,
                "status": row.conversion_action.status.name,
                "counting_type": row.conversion_action.counting_type.name,
                "default_value": row.conversion_action.value_settings.default_value,
                "always_use_default": row.conversion_action.value_settings.always_use_default_value,
                "attribution_model": row.conversion_action.attribution_model_settings.attribution_model.name,
                "click_lookback_days": row.conversion_action.click_through_lookback_window_days,
                "view_lookback_days": row.conversion_action.view_through_lookback_window_days,
                "include_in_conversions": row.conversion_action.include_in_conversions_metric,
            }
            return success_response(data)
        return error_response(f"Conversion action {conversion_action_id} not found")
    except Exception as e:
        return error_response(f"Failed to get conversion action: {e}")


@mcp.tool()
def create_conversion_action(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Conversion action name"],
    action_type: Annotated[str, "Type: UPLOAD_CLICKS, WEBPAGE, PHONE_CALL, IMPORT, etc."],
    category: Annotated[str, "Category: PURCHASE, LEAD, SIGN_UP, PAGE_VIEW, ADD_TO_CART, etc."],
    default_value: Annotated[float | None, "Default conversion value"] = None,
    counting_type: Annotated[str, "ONE_PER_CLICK or MANY_PER_CLICK"] = "ONE_PER_CLICK",
) -> str:
    """Create a new conversion action for tracking conversions.

    Created as ENABLED by default. Use update_conversion_action to modify settings.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("ConversionActionService")

        operation = client.get_type("ConversionActionOperation")
        conversion_action = operation.create
        conversion_action.name = name
        conversion_action.type_ = getattr(client.enums.ConversionActionTypeEnum, action_type)
        conversion_action.category = getattr(client.enums.ConversionActionCategoryEnum, category)
        conversion_action.counting_type = getattr(client.enums.ConversionActionCountingTypeEnum, counting_type)
        conversion_action.status = client.enums.ConversionActionStatusEnum.ENABLED

        if default_value is not None:
            conversion_action.value_settings.default_value = default_value
            conversion_action.value_settings.always_use_default_value = False

        response = service.mutate_conversion_actions(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name
        new_id = resource_name.split("/")[-1]

        return success_response(
            {"conversion_action_id": new_id, "resource_name": resource_name},
            message=f"Conversion action '{name}' created",
        )
    except Exception as e:
        return error_response(f"Failed to create conversion action: {e}")


@mcp.tool()
def update_conversion_action(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    conversion_action_id: Annotated[str, "The conversion action ID"],
    name: Annotated[str | None, "New name"] = None,
    status: Annotated[str | None, "New status: ENABLED, PAUSED, REMOVED, HIDDEN"] = None,
    default_value: Annotated[float | None, "New default conversion value"] = None,
    counting_type: Annotated[str | None, "ONE_PER_CLICK or MANY_PER_CLICK"] = None,
) -> str:
    """Update an existing conversion action's settings."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = get_service("ConversionActionService")

        operation = client.get_type("ConversionActionOperation")
        conversion_action = operation.update
        conversion_action.resource_name = f"customers/{cid}/conversionActions/{conversion_action_id}"

        fields = []
        if name is not None:
            conversion_action.name = name
            fields.append("name")
        if status is not None:
            conversion_action.status = getattr(client.enums.ConversionActionStatusEnum, status)
            fields.append("status")
        if default_value is not None:
            conversion_action.value_settings.default_value = default_value
            fields.append("value_settings.default_value")
        if counting_type is not None:
            conversion_action.counting_type = getattr(client.enums.ConversionActionCountingTypeEnum, counting_type)
            fields.append("counting_type")

        if not fields:
            return error_response("No fields to update")

        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=fields),
        )

        response = service.mutate_conversion_actions(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message=f"Conversion action {conversion_action_id} updated",
        )
    except Exception as e:
        return error_response(f"Failed to update conversion action: {e}")


@mcp.tool()
def import_offline_conversions(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    conversions: Annotated[list[dict], "List of {gclid, conversion_action_id, conversion_date_time, conversion_value?}"],
) -> str:
    """Import offline click conversions.

    Each conversion needs: gclid, conversion_action_id, conversion_date_time (format: yyyy-mm-dd hh:mm:ss+|-hh:mm).
    Optional: conversion_value (float).

    Example: [{"gclid": "abc123", "conversion_action_id": "456", "conversion_date_time": "2024-01-15 14:30:00-03:00", "conversion_value": 100.0}]
    """
    try:
        cid = resolve_customer_id(customer_id)

        if len(conversions) > 2000:
            return error_response(f"Maximum 2000 conversions per call, received: {len(conversions)}")

        required_fields = ("gclid", "conversion_action_id", "conversion_date_time")
        for conv in conversions:
            for field in required_fields:
                if field not in conv:
                    return error_response(f"Each conversion must have a '{field}' field")

        client = get_client()
        service = get_service("ConversionUploadService")

        click_conversions = []
        for conv in conversions:
            click_conversion = client.get_type("ClickConversion")
            click_conversion.gclid = conv["gclid"]
            click_conversion.conversion_action = f"customers/{cid}/conversionActions/{conv['conversion_action_id']}"
            click_conversion.conversion_date_time = conv["conversion_date_time"]
            if "conversion_value" in conv:
                click_conversion.conversion_value = conv["conversion_value"]
            click_conversions.append(click_conversion)

        response = service.upload_click_conversions(
            customer_id=cid,
            conversions=click_conversions,
            partial_failure=True,
        )

        results = []
        for result in response.results:
            results.append({
                "gclid": result.gclid,
                "conversion_action": result.conversion_action,
                "conversion_date_time": result.conversion_date_time,
            })

        partial_errors = None
        if response.partial_failure_error:
            partial_errors = str(response.partial_failure_error)

        return success_response(
            {"uploaded": len(results), "results": results, "partial_failure_error": partial_errors},
            message=f"{len(results)} offline conversions uploaded",
        )
    except Exception as e:
        return error_response(f"Failed to import offline conversions: {e}")


@mcp.tool()
def list_conversion_goals(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum number of results"] = 100,
) -> str:
    """List customer conversion goals.

    Shows which conversion actions are configured as goals for the account.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                customer_conversion_goal.category,
                customer_conversion_goal.origin,
                customer_conversion_goal.biddable
            FROM customer_conversion_goal
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        goals = []
        for row in response:
            goals.append({
                "category": row.customer_conversion_goal.category.name,
                "origin": row.customer_conversion_goal.origin.name,
                "biddable": row.customer_conversion_goal.biddable,
            })
        return success_response({"conversion_goals": goals, "count": len(goals)})
    except Exception as e:
        return error_response(f"Failed to list conversion goals: {e}")
