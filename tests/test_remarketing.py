"""Tests for remarketing.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListRemarketingActions:
    @patch("mcp_google_ads.tools.remarketing.get_service")
    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", return_value="123")
    def test_returns_actions(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.remarketing import list_remarketing_actions

        snippet = MagicMock()
        snippet.type_.name = "WEBPAGE"
        snippet.global_site_tag = "<script>gtag()</script>"
        snippet.event_snippet = "<script>event()</script>"

        mock_row = MagicMock()
        mock_row.remarketing_action.resource_name = "customers/123/remarketingActions/1"
        mock_row.remarketing_action.id = 1
        mock_row.remarketing_action.name = "Site Visitors"
        mock_row.remarketing_action.tag_snippets = [snippet]

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_remarketing_actions("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["remarketing_actions"][0]["name"] == "Site Visitors"
        assert result["data"]["remarketing_actions"][0]["id"] == "1"
        assert len(result["data"]["remarketing_actions"][0]["tag_snippets"]) == 1
        assert result["data"]["remarketing_actions"][0]["tag_snippets"][0]["type"] == "WEBPAGE"

    @patch("mcp_google_ads.tools.remarketing.get_service")
    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", return_value="123")
    def test_returns_empty_list(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.remarketing import list_remarketing_actions

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_remarketing_actions("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["remarketing_actions"] == []

    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.remarketing import list_remarketing_actions

        result = assert_error(list_remarketing_actions(""))
        assert "Failed to list remarketing actions" in result["error"]


class TestGetRemarketingAction:
    @patch("mcp_google_ads.tools.remarketing.get_service")
    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", return_value="123")
    def test_returns_action(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.remarketing import get_remarketing_action

        snippet = MagicMock()
        snippet.type_.name = "WEBPAGE"
        snippet.global_site_tag = "<script>gtag()</script>"
        snippet.event_snippet = "<script>event()</script>"

        mock_row = MagicMock()
        mock_row.remarketing_action.resource_name = "customers/123/remarketingActions/456"
        mock_row.remarketing_action.id = 456
        mock_row.remarketing_action.name = "Cart Abandoners"
        mock_row.remarketing_action.tag_snippets = [snippet]

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_remarketing_action("123", "456"))
        assert result["data"]["name"] == "Cart Abandoners"
        assert result["data"]["id"] == "456"
        assert len(result["data"]["tag_snippets"]) == 1

    @patch("mcp_google_ads.tools.remarketing.get_service")
    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", return_value="123")
    def test_not_found(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.remarketing import get_remarketing_action

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_error(get_remarketing_action("123", "999"))
        assert "not found" in result["error"]

    def test_rejects_invalid_id(self):
        from mcp_google_ads.tools.remarketing import get_remarketing_action

        result = assert_error(get_remarketing_action("123", "abc"))
        assert "Failed to get remarketing action" in result["error"]


class TestCreateRemarketingAction:
    @patch("mcp_google_ads.tools.remarketing.get_service")
    @patch("mcp_google_ads.tools.remarketing.get_client")
    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", return_value="123")
    def test_creates_action(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.remarketing import create_remarketing_action

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/remarketingActions/789")]
        mock_service = MagicMock()
        mock_service.mutate_remarketing_actions.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_remarketing_action("123", "New Tag"))
        assert result["data"]["remarketing_action_id"] == "789"
        assert result["data"]["resource_name"] == "customers/123/remarketingActions/789"
        assert "created" in result["message"]

        mock_service.mutate_remarketing_actions.assert_called_once()
        operation = client.get_type.return_value
        assert operation.create.name == "New Tag"

    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.remarketing import create_remarketing_action

        result = assert_error(create_remarketing_action("123", "Fail"))
        assert "Failed to create remarketing action" in result["error"]

    @patch("mcp_google_ads.tools.remarketing.get_service")
    @patch("mcp_google_ads.tools.remarketing.get_client")
    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", return_value="123")
    def test_passes_correct_customer_id(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.remarketing import create_remarketing_action

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/remarketingActions/100")]
        mock_service = MagicMock()
        mock_service.mutate_remarketing_actions.return_value = mock_response
        mock_get_service.return_value = mock_service

        assert_success(create_remarketing_action("123", "Tag"))
        mock_service.mutate_remarketing_actions.assert_called_once_with(
            customer_id="123", operations=[client.get_type.return_value]
        )


class TestRemoveRemarketingAction:
    @patch("mcp_google_ads.tools.remarketing.get_service")
    @patch("mcp_google_ads.tools.remarketing.get_client")
    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", return_value="123")
    def test_removes_action(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.remarketing import remove_remarketing_action

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        result = assert_success(remove_remarketing_action("123", "456"))
        assert result["data"]["action"] == "removed"
        assert result["data"]["remarketing_action_id"] == "456"
        assert "removed" in result["message"]

        mock_service.mutate_remarketing_actions.assert_called_once()

    def test_rejects_invalid_id(self):
        from mcp_google_ads.tools.remarketing import remove_remarketing_action

        result = assert_error(remove_remarketing_action("123", "abc"))
        assert "Failed to remove remarketing action" in result["error"]

    @patch("mcp_google_ads.tools.remarketing.get_service")
    @patch("mcp_google_ads.tools.remarketing.get_client")
    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", return_value="123")
    def test_sets_correct_resource_name(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.remarketing import remove_remarketing_action

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        assert_success(remove_remarketing_action("123", "456"))
        operation = client.get_type.return_value
        assert operation.remove == "customers/123/remarketingActions/456"


class TestListCombinedAudiences:
    @patch("mcp_google_ads.tools.remarketing.get_service")
    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", return_value="123")
    def test_returns_audiences(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.remarketing import list_combined_audiences

        mock_row = MagicMock()
        mock_row.combined_audience.resource_name = "customers/123/combinedAudiences/1"
        mock_row.combined_audience.id = 1
        mock_row.combined_audience.name = "High-Value Returners"
        mock_row.combined_audience.description = "Users who visited and purchased"
        mock_row.combined_audience.status.name = "ENABLED"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_combined_audiences("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["combined_audiences"][0]["name"] == "High-Value Returners"
        assert result["data"]["combined_audiences"][0]["status"] == "ENABLED"
        assert result["data"]["combined_audiences"][0]["description"] == "Users who visited and purchased"

    @patch("mcp_google_ads.tools.remarketing.get_service")
    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", return_value="123")
    def test_returns_empty_list(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.remarketing import list_combined_audiences

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_combined_audiences("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["combined_audiences"] == []

    @patch("mcp_google_ads.tools.remarketing.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.remarketing import list_combined_audiences

        result = assert_error(list_combined_audiences(""))
        assert "Failed to list combined audiences" in result["error"]
