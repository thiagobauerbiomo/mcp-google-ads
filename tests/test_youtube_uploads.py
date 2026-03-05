"""Tests for youtube_uploads.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestCreateYoutubeVideoUpload:
    @patch("mcp_google_ads.tools.youtube_uploads.get_client")
    @patch("mcp_google_ads.tools.youtube_uploads.resolve_customer_id", return_value="123")
    def test_creates_upload(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.youtube_uploads import create_youtube_video_upload

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/youtubeVideoUploads/456")]
        client.get_service.return_value.mutate_youtube_video_uploads.return_value = mock_response

        result = assert_success(create_youtube_video_upload("123", "Test Video", "Description"))
        assert "youtubeVideoUploads" in result["data"]["resource_name"]

    @patch("mcp_google_ads.tools.youtube_uploads.get_client")
    @patch("mcp_google_ads.tools.youtube_uploads.resolve_customer_id", return_value="123")
    def test_error_handling(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.youtube_uploads import create_youtube_video_upload

        client = MagicMock()
        mock_client.return_value = client
        client.get_service.return_value.mutate_youtube_video_uploads.side_effect = Exception("API error")

        result = assert_error(create_youtube_video_upload("123", "Test", "Desc"))
        assert "Failed to create YouTube video upload" in result["error"]


class TestUpdateYoutubeVideoUpload:
    @patch("mcp_google_ads.tools.youtube_uploads.get_client")
    @patch("mcp_google_ads.tools.youtube_uploads.resolve_customer_id", return_value="123")
    def test_updates_privacy(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.youtube_uploads import update_youtube_video_upload

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/youtubeVideoUploads/456")]
        client.get_service.return_value.mutate_youtube_video_uploads.return_value = mock_response

        result = assert_success(update_youtube_video_upload("123", "456", video_privacy="PUBLIC"))
        assert "updated" in result["message"].lower()

    @patch("mcp_google_ads.tools.youtube_uploads.get_client")
    @patch("mcp_google_ads.tools.youtube_uploads.resolve_customer_id", return_value="123")
    def test_no_fields_error(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.youtube_uploads import update_youtube_video_upload

        result = assert_error(update_youtube_video_upload("123", "456"))
        assert "No fields to update" in result["error"]


class TestRemoveYoutubeVideoUpload:
    @patch("mcp_google_ads.tools.youtube_uploads.get_client")
    @patch("mcp_google_ads.tools.youtube_uploads.resolve_customer_id", return_value="123")
    def test_removes_upload(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.youtube_uploads import remove_youtube_video_upload

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock()]
        client.get_service.return_value.mutate_youtube_video_uploads.return_value = mock_response

        result = assert_success(remove_youtube_video_upload("123", "456"))
        assert "removed" in result["message"].lower()

    @patch("mcp_google_ads.tools.youtube_uploads.get_client")
    @patch("mcp_google_ads.tools.youtube_uploads.resolve_customer_id", return_value="123")
    def test_error_handling(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.youtube_uploads import remove_youtube_video_upload

        client = MagicMock()
        mock_client.return_value = client
        client.get_service.return_value.mutate_youtube_video_uploads.side_effect = Exception("API error")

        result = assert_error(remove_youtube_video_upload("123", "456"))
        assert "Failed to remove YouTube video upload" in result["error"]
