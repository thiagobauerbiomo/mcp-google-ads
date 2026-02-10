"""Tests for shared_sets.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListSharedSets:
    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_returns_sets(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.shared_sets import list_shared_sets

        mock_row = MagicMock()
        mock_row.shared_set.id = 777
        mock_row.shared_set.name = "Negative List"
        mock_row.shared_set.type_.name = "NEGATIVE_KEYWORDS"
        mock_row.shared_set.status.name = "ENABLED"
        mock_row.shared_set.member_count = 50

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_shared_sets("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["shared_sets"][0]["name"] == "Negative List"

    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_empty_results(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.shared_sets import list_shared_sets

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_shared_sets("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["shared_sets"] == []

    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_with_type_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.shared_sets import list_shared_sets

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_shared_sets("123", set_type="NEGATIVE_KEYWORDS"))
        assert result["data"]["count"] == 0
        call_query = mock_service.search.call_args[1]["query"]
        assert "NEGATIVE_KEYWORDS" in call_query

    def test_rejects_invalid_set_type(self):
        from mcp_google_ads.tools.shared_sets import list_shared_sets

        result = assert_error(list_shared_sets("123", set_type="DROP TABLE"))
        assert "Failed to list shared sets" in result["error"]

    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", side_effect=Exception("API error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.shared_sets import list_shared_sets

        result = assert_error(list_shared_sets("123"))
        assert "Failed to list shared sets" in result["error"]


class TestCreateSharedSet:
    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.get_client")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_creates_set(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.shared_sets import create_shared_set

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/sharedSets/777")]
        mock_service.mutate_shared_sets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_shared_set("123", "New List"))
        assert result["data"]["shared_set_id"] == "777"

    def test_rejects_invalid_set_type(self):
        from mcp_google_ads.tools.shared_sets import create_shared_set

        result = assert_error(create_shared_set("123", "Bad List", set_type="'; DROP TABLE"))
        assert "Failed to create shared set" in result["error"]

    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", side_effect=Exception("API error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.shared_sets import create_shared_set

        result = assert_error(create_shared_set("123", "New List"))
        assert "Failed to create shared set" in result["error"]


class TestRemoveSharedSet:
    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.get_client")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_removes_set_successfully(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.shared_sets import remove_shared_set

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/sharedSets/777")]
        mock_service.mutate_shared_sets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(remove_shared_set("123", "777"))
        assert result["data"]["resource_name"] == "customers/123/sharedSets/777"
        assert "removed" in result["message"]

    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", side_effect=Exception("API error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.shared_sets import remove_shared_set

        result = assert_error(remove_shared_set("123", "777"))
        assert "Failed to remove shared set" in result["error"]


class TestListSharedSetMembers:
    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_returns_members(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.shared_sets import list_shared_set_members

        mock_row = MagicMock()
        mock_row.shared_criterion.criterion_id = 999
        mock_row.shared_criterion.type_.name = "KEYWORD"
        mock_row.shared_criterion.keyword.text = "test keyword"
        mock_row.shared_criterion.keyword.match_type.name = "EXACT"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_shared_set_members("123", "777"))
        assert result["data"]["count"] == 1
        member = result["data"]["members"][0]
        assert member["criterion_id"] == "999"
        assert member["type"] == "KEYWORD"
        assert member["keyword"] == "test keyword"
        assert member["match_type"] == "EXACT"

    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_returns_non_keyword_members(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.shared_sets import list_shared_set_members

        mock_row = MagicMock()
        mock_row.shared_criterion.criterion_id = 888
        mock_row.shared_criterion.type_.name = "PLACEMENT"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_shared_set_members("123", "777"))
        assert result["data"]["count"] == 1
        member = result["data"]["members"][0]
        assert member["criterion_id"] == "888"
        assert member["type"] == "PLACEMENT"
        assert "keyword" not in member
        assert "match_type" not in member

    def test_rejects_invalid_shared_set_id(self):
        from mcp_google_ads.tools.shared_sets import list_shared_set_members

        result = assert_error(list_shared_set_members("123", "abc"))
        assert "Failed to list shared set members" in result["error"]

    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", side_effect=Exception("API error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.shared_sets import list_shared_set_members

        result = assert_error(list_shared_set_members("123", "777"))
        assert "Failed to list shared set members" in result["error"]


class TestLinkSharedSetToCampaign:
    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.get_client")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_links_set(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.shared_sets import link_shared_set_to_campaign

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignSharedSets/111~777")]
        mock_service.mutate_campaign_shared_sets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(link_shared_set_to_campaign("123", "111", "777"))
        assert "linked" in result["message"]

    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", side_effect=Exception("API error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.shared_sets import link_shared_set_to_campaign

        result = assert_error(link_shared_set_to_campaign("123", "111", "777"))
        assert "Failed to link shared set to campaign" in result["error"]


class TestUnlinkSharedSetFromCampaign:
    @patch("mcp_google_ads.tools.shared_sets.get_service")
    @patch("mcp_google_ads.tools.shared_sets.get_client")
    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", return_value="123")
    def test_unlinks_successfully(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.shared_sets import unlink_shared_set_from_campaign

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/campaignSharedSets/111~777")]
        mock_service.mutate_campaign_shared_sets.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(unlink_shared_set_from_campaign("123", "111", "777"))
        assert result["data"]["resource_name"] == "customers/123/campaignSharedSets/111~777"
        assert "unlinked" in result["message"]

    @patch("mcp_google_ads.tools.shared_sets.resolve_customer_id", side_effect=Exception("API error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.shared_sets import unlink_shared_set_from_campaign

        result = assert_error(unlink_shared_set_from_campaign("123", "111", "777"))
        assert "Failed to unlink shared set from campaign" in result["error"]
