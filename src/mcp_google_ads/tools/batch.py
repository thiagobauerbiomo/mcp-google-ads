"""Batch operations tools (1 tool)."""

from __future__ import annotations

import logging
from typing import Annotated

from google.api_core import protobuf_helpers

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response, validate_numeric_id

logger = logging.getLogger(__name__)

_VALID_RESOURCE_TYPES = {"campaign", "ad_group", "ad"}
_VALID_BATCH_STATUSES = {"ENABLED", "PAUSED"}
_MAX_BATCH_SIZE = 100


@mcp.tool()
def batch_set_status(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    resources: Annotated[list[dict], "List of {type, id, ad_group_id?}. type: campaign|ad_group|ad. ad_group_id required for ads."],
    status: Annotated[str, "New status: ENABLED or PAUSED"],
) -> str:
    """Set status for multiple resources (campaigns, ad groups, ads) in a single API call.

    Example: [{"type": "campaign", "id": "123"}, {"type": "ad_group", "id": "456"}, {"type": "ad", "id": "789", "ad_group_id": "456"}]
    WARNING: Setting campaigns to ENABLED will start spending budget.
    """
    # Validar status (apenas ENABLED e PAUSED, não REMOVED por segurança)
    upper_status = status.upper()
    if upper_status not in _VALID_BATCH_STATUSES:
        return error_response(f"Invalid status '{status}'. Use: ENABLED or PAUSED (REMOVED not allowed in batch for safety)")

    # Validar lista de recursos
    if not resources:
        return error_response("Resources list cannot be empty")

    if len(resources) > _MAX_BATCH_SIZE:
        return error_response(f"Maximum {_MAX_BATCH_SIZE} resources per call, received: {len(resources)}")

    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()

        # Construir MutateOperations
        mutate_operations = []
        for i, resource in enumerate(resources):
            resource_type = resource.get("type", "")
            if resource_type not in _VALID_RESOURCE_TYPES:
                return error_response(
                    f"Item {i}: invalid type '{resource_type}'. Use: campaign, ad_group, ad"
                )

            resource_id = resource.get("id", "")
            if not resource_id:
                return error_response(f"Item {i}: missing required field 'id'")
            safe_id = validate_numeric_id(str(resource_id), f"item {i} id")

            mutate_op = client.get_type("MutateOperation")

            if resource_type == "campaign":
                campaign_op = client.get_type("CampaignOperation")
                campaign = campaign_op.update
                campaign.resource_name = f"customers/{cid}/campaigns/{safe_id}"
                campaign.status = getattr(client.enums.CampaignStatusEnum, upper_status)
                client.copy_from(
                    campaign_op.update_mask,
                    protobuf_helpers.field_mask_pb2.FieldMask(paths=["status"]),
                )
                client.copy_from(mutate_op.campaign_operation, campaign_op)

            elif resource_type == "ad_group":
                ad_group_op = client.get_type("AdGroupOperation")
                ad_group = ad_group_op.update
                ad_group.resource_name = f"customers/{cid}/adGroups/{safe_id}"
                ad_group.status = getattr(client.enums.AdGroupStatusEnum, upper_status)
                client.copy_from(
                    ad_group_op.update_mask,
                    protobuf_helpers.field_mask_pb2.FieldMask(paths=["status"]),
                )
                client.copy_from(mutate_op.ad_group_operation, ad_group_op)

            elif resource_type == "ad":
                ad_group_id = resource.get("ad_group_id", "")
                if not ad_group_id:
                    return error_response(f"Item {i}: ad_group_id is required for ads")
                safe_ag_id = validate_numeric_id(str(ad_group_id), f"item {i} ad_group_id")

                ad_op = client.get_type("AdGroupAdOperation")
                ad_group_ad = ad_op.update
                ad_group_ad.resource_name = f"customers/{cid}/adGroupAds/{safe_ag_id}~{safe_id}"
                ad_group_ad.status = getattr(client.enums.AdGroupAdStatusEnum, upper_status)
                client.copy_from(
                    ad_op.update_mask,
                    protobuf_helpers.field_mask_pb2.FieldMask(paths=["status"]),
                )
                client.copy_from(mutate_op.ad_group_ad_operation, ad_op)

            mutate_operations.append(mutate_op)

        # Executar batch via GoogleAdsService.mutate()
        service = get_service("GoogleAdsService")
        response = service.mutate(customer_id=cid, mutate_operations=mutate_operations)

        results = [r.resource_name for r in response.mutate_operation_responses]
        return success_response(
            {"successful_operations": len(results), "results": results},
            message=f"{len(results)} resources set to {upper_status}",
        )
    except Exception as e:
        logger.error("Failed to batch set status: %s", e, exc_info=True)
        return error_response(f"Failed to batch set status: {e}")
