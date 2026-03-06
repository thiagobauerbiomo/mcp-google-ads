"""Tests for campaign_drafts.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListCampaignDrafts:
    @patch("mcp_google_ads.tools.campaign_drafts.get_service")
    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", return_value="123")
    def test_returns_drafts(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_drafts import list_campaign_drafts

        mock_row = MagicMock()
        mock_row.campaign_draft.resource_name = "customers/123/campaignDrafts/111~1"
        mock_row.campaign_draft.draft_id = 1
        mock_row.campaign_draft.base_campaign = "customers/123/campaigns/111"
        mock_row.campaign_draft.name = "Test Draft"
        mock_row.campaign_draft.draft_campaign = "customers/123/campaigns/222"
        mock_row.campaign_draft.status.name = "PROPOSED"
        mock_row.campaign_draft.has_experiment_running = False

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_drafts("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["drafts"][0]["name"] == "Test Draft"
        assert result["data"]["drafts"][0]["status"] == "PROPOSED"

    @patch("mcp_google_ads.tools.campaign_drafts.get_service")
    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", return_value="123")
    def test_filters_by_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_drafts import list_campaign_drafts

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_drafts("123", campaign_id="111"))
        assert result["data"]["count"] == 0
        query = mock_service.search.call_args[1]["query"]
        assert "customers/123/campaigns/111" in query

    @patch("mcp_google_ads.tools.campaign_drafts.get_service")
    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", return_value="123")
    def test_returns_empty_list(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_drafts import list_campaign_drafts

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_drafts("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["drafts"] == []

    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_drafts import list_campaign_drafts

        result = assert_error(list_campaign_drafts(""))
        assert "Failed to list campaign drafts" in result["error"]

    def test_rejects_invalid_campaign_id(self):
        from mcp_google_ads.tools.campaign_drafts import list_campaign_drafts

        result = assert_error(list_campaign_drafts("123", campaign_id="abc"))
        assert "Failed to list campaign drafts" in result["error"]


class TestGetCampaignDraft:
    @patch("mcp_google_ads.tools.campaign_drafts.get_service")
    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", return_value="123")
    def test_returns_draft(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_drafts import get_campaign_draft

        mock_row = MagicMock()
        mock_row.campaign_draft.resource_name = "customers/123/campaignDrafts/111~1"
        mock_row.campaign_draft.draft_id = 1
        mock_row.campaign_draft.base_campaign = "customers/123/campaigns/111"
        mock_row.campaign_draft.name = "My Draft"
        mock_row.campaign_draft.draft_campaign = "customers/123/campaigns/222"
        mock_row.campaign_draft.status.name = "PROPOSED"
        mock_row.campaign_draft.has_experiment_running = False

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_campaign_draft("123", "1", "111"))
        assert result["data"]["name"] == "My Draft"
        assert result["data"]["draft_id"] == 1
        query = mock_service.search.call_args[1]["query"]
        assert "customers/123/campaignDrafts/111~1" in query

    @patch("mcp_google_ads.tools.campaign_drafts.get_service")
    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", return_value="123")
    def test_not_found(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_drafts import get_campaign_draft

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_error(get_campaign_draft("123", "999", "111"))
        assert "not found" in result["error"]

    def test_rejects_invalid_draft_id(self):
        from mcp_google_ads.tools.campaign_drafts import get_campaign_draft

        result = assert_error(get_campaign_draft("123", "abc", "111"))
        assert "Failed to get campaign draft" in result["error"]

    def test_rejects_invalid_base_campaign_id(self):
        from mcp_google_ads.tools.campaign_drafts import get_campaign_draft

        result = assert_error(get_campaign_draft("123", "1", "abc"))
        assert "Failed to get campaign draft" in result["error"]


class TestCreateCampaignDraft:
    @patch("mcp_google_ads.tools.campaign_drafts.get_service")
    @patch("mcp_google_ads.tools.campaign_drafts.get_client")
    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", return_value="123")
    def test_creates_draft(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_drafts import create_campaign_draft

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignDrafts/111~1")]
        mock_draft_service = MagicMock()
        mock_draft_service.mutate_campaign_drafts.return_value = mock_response
        mock_get_service.return_value = mock_draft_service

        result = assert_success(create_campaign_draft("123", "111", "My Draft"))
        assert result["data"]["resource_name"] == "customers/123/campaignDrafts/111~1"
        assert result["data"]["name"] == "My Draft"
        assert result["data"]["base_campaign_id"] == "111"
        mock_draft_service.mutate_campaign_drafts.assert_called_once()

        operation = client.get_type.return_value
        assert operation.create.base_campaign == "customers/123/campaigns/111"
        assert operation.create.name == "My Draft"

    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_drafts import create_campaign_draft

        result = assert_error(create_campaign_draft("123", "111", "Fail"))
        assert "Failed to create campaign draft" in result["error"]

    def test_rejects_invalid_base_campaign_id(self):
        from mcp_google_ads.tools.campaign_drafts import create_campaign_draft

        result = assert_error(create_campaign_draft("123", "abc", "My Draft"))
        assert "Failed to create campaign draft" in result["error"]


class TestPromoteCampaignDraft:
    @patch("mcp_google_ads.tools.campaign_drafts.get_service")
    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", return_value="123")
    def test_promotes_draft(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_drafts import promote_campaign_draft

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        result = assert_success(promote_campaign_draft("123", "1", "111"))
        assert result["data"]["action"] == "promoted"
        assert result["data"]["draft_id"] == "1"
        assert result["data"]["base_campaign_id"] == "111"
        mock_service.promote_campaign_draft.assert_called_once_with(
            campaign_draft="customers/123/campaignDrafts/111~1"
        )

    def test_rejects_invalid_draft_id(self):
        from mcp_google_ads.tools.campaign_drafts import promote_campaign_draft

        result = assert_error(promote_campaign_draft("123", "abc", "111"))
        assert "Failed to promote campaign draft" in result["error"]

    def test_rejects_invalid_base_campaign_id(self):
        from mcp_google_ads.tools.campaign_drafts import promote_campaign_draft

        result = assert_error(promote_campaign_draft("123", "1", "abc"))
        assert "Failed to promote campaign draft" in result["error"]

    @patch("mcp_google_ads.tools.campaign_drafts.get_service")
    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", return_value="123")
    def test_api_error(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_drafts import promote_campaign_draft

        mock_service = MagicMock()
        mock_service.promote_campaign_draft.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(promote_campaign_draft("123", "1", "111"))
        assert "Failed to promote campaign draft" in result["error"]


class TestRemoveCampaignDraft:
    @patch("mcp_google_ads.tools.campaign_drafts.get_service")
    @patch("mcp_google_ads.tools.campaign_drafts.get_client")
    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", return_value="123")
    def test_removes_draft(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_drafts import remove_campaign_draft

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        result = assert_success(remove_campaign_draft("123", "1", "111"))
        assert result["data"]["action"] == "removed"
        assert result["data"]["draft_id"] == "1"
        assert result["data"]["base_campaign_id"] == "111"
        mock_service.mutate_campaign_drafts.assert_called_once()

        operation = client.get_type.return_value
        assert operation.remove == "customers/123/campaignDrafts/111~1"

    def test_rejects_invalid_draft_id(self):
        from mcp_google_ads.tools.campaign_drafts import remove_campaign_draft

        result = assert_error(remove_campaign_draft("123", "abc", "111"))
        assert "Failed to remove campaign draft" in result["error"]

    def test_rejects_invalid_base_campaign_id(self):
        from mcp_google_ads.tools.campaign_drafts import remove_campaign_draft

        result = assert_error(remove_campaign_draft("123", "1", "abc"))
        assert "Failed to remove campaign draft" in result["error"]

    @patch("mcp_google_ads.tools.campaign_drafts.get_service")
    @patch("mcp_google_ads.tools.campaign_drafts.get_client")
    @patch("mcp_google_ads.tools.campaign_drafts.resolve_customer_id", return_value="123")
    def test_api_error(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_drafts import remove_campaign_draft

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_service.mutate_campaign_drafts.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(remove_campaign_draft("123", "1", "111"))
        assert "Failed to remove campaign draft" in result["error"]
