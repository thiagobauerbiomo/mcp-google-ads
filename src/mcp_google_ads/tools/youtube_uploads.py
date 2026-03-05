"""YouTube video upload tools (3 tools)."""

from __future__ import annotations

import logging
from typing import Annotated

from ..auth import get_client
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response, validate_enum_value

logger = logging.getLogger(__name__)


@mcp.tool()
def create_youtube_video_upload(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    video_title: Annotated[str, "Title of the video"],
    video_description: Annotated[str, "Description of the video"],
    channel_id: Annotated[str | None, "YouTube channel ID (omit for Google-managed channel)"] = None,
    video_privacy: Annotated[str, "Privacy: UNLISTED, PUBLIC, PRIVATE"] = "UNLISTED",
) -> str:
    """Create a YouTube video upload entry via Google Ads API.

    Initiates a video upload to YouTube. If no channel_id is provided,
    the video is uploaded to the Google-managed YouTube channel.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = client.get_service("YouTubeVideoUploadService")

        operation = client.get_type("YouTubeVideoUploadOperation")
        upload = operation.create
        upload.customer_id = cid
        upload.video_title = video_title
        upload.video_description = video_description

        if channel_id:
            upload.channel_id = channel_id

        privacy_value = validate_enum_value(video_privacy, "video_privacy")
        upload.video_privacy = getattr(client.enums.YouTubeVideoPrivacyEnum, privacy_value)

        response = service.mutate_youtube_video_uploads(customer_id=cid, operations=[operation])
        resource_name = response.results[0].resource_name

        return success_response(
            {"resource_name": resource_name},
            message=f"YouTube video upload created: {video_title}",
        )
    except Exception as e:
        logger.error("Failed to create YouTube video upload: %s", e, exc_info=True)
        return error_response(f"Failed to create YouTube video upload: {e}")


@mcp.tool()
def update_youtube_video_upload(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    video_upload_id: Annotated[str, "The video upload resource name or ID"],
    video_privacy: Annotated[str | None, "New privacy: UNLISTED, PUBLIC, PRIVATE"] = None,
) -> str:
    """Update the privacy setting of a YouTube video upload."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = client.get_service("YouTubeVideoUploadService")

        if not video_privacy:
            return error_response("No fields to update. Provide video_privacy.")

        operation = client.get_type("YouTubeVideoUploadOperation")
        upload = operation.update
        upload.resource_name = video_upload_id if "/" in video_upload_id else f"customers/{cid}/youtubeVideoUploads/{video_upload_id}"

        privacy_value = validate_enum_value(video_privacy, "video_privacy")
        upload.video_privacy = getattr(client.enums.YouTubeVideoPrivacyEnum, privacy_value)

        from google.api_core import protobuf_helpers
        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask_pb2.FieldMask(paths=["video_privacy"]),
        )

        response = service.mutate_youtube_video_uploads(customer_id=cid, operations=[operation])
        return success_response(
            {"resource_name": response.results[0].resource_name},
            message="YouTube video upload updated",
        )
    except Exception as e:
        logger.error("Failed to update YouTube video upload: %s", e, exc_info=True)
        return error_response(f"Failed to update YouTube video upload: {e}")


@mcp.tool()
def remove_youtube_video_upload(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    video_upload_id: Annotated[str, "The video upload resource name or ID"],
) -> str:
    """Remove a YouTube video upload."""
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        service = client.get_service("YouTubeVideoUploadService")

        operation = client.get_type("YouTubeVideoUploadOperation")
        resource_name = video_upload_id if "/" in video_upload_id else f"customers/{cid}/youtubeVideoUploads/{video_upload_id}"
        operation.remove = resource_name

        service.mutate_youtube_video_uploads(customer_id=cid, operations=[operation])
        return success_response(
            {"removed": resource_name},
            message="YouTube video upload removed",
        )
    except Exception as e:
        logger.error("Failed to remove YouTube video upload: %s", e, exc_info=True)
        return error_response(f"Failed to remove YouTube video upload: {e}")
