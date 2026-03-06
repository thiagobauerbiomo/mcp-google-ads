"""Tests for user_lists.py tools."""

from __future__ import annotations

import hashlib
from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListUserLists:
    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_returns_user_lists(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.user_lists import list_user_lists

        mock_row = MagicMock()
        mock_row.user_list.resource_name = "customers/123/userLists/456"
        mock_row.user_list.id = 456
        mock_row.user_list.name = "My CRM List"
        mock_row.user_list.description = "Test list"
        mock_row.user_list.type_.name = "CRM_BASED"
        mock_row.user_list.membership_status.name = "OPEN"
        mock_row.user_list.size_for_search = 1000
        mock_row.user_list.size_for_display = 1500
        mock_row.user_list.membership_life_span = 10000
        mock_row.user_list.match_rate_percentage = 45
        mock_row.user_list.eligible_for_search = True
        mock_row.user_list.eligible_for_display = True

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_user_lists("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["user_lists"][0]["name"] == "My CRM List"
        assert result["data"]["user_lists"][0]["type"] == "CRM_BASED"
        assert result["data"]["user_lists"][0]["id"] == "456"

    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_filters_by_type(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.user_lists import list_user_lists

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_user_lists("123", list_type="CRM_BASED"))
        assert result["data"]["count"] == 0

        query = mock_service.search.call_args[1]["query"]
        assert "WHERE user_list.type = 'CRM_BASED'" in query

    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.user_lists import list_user_lists

        result = assert_error(list_user_lists(""))
        assert "Failed to list user lists" in result["error"]

    def test_rejects_invalid_list_type(self):
        from mcp_google_ads.tools.user_lists import list_user_lists

        result = assert_error(list_user_lists("123", list_type="DROP TABLE;"))
        assert "Failed to list user lists" in result["error"]


class TestGetUserList:
    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_returns_user_list(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.user_lists import get_user_list

        mock_row = MagicMock()
        mock_row.user_list.resource_name = "customers/123/userLists/456"
        mock_row.user_list.id = 456
        mock_row.user_list.name = "My List"
        mock_row.user_list.description = "Desc"
        mock_row.user_list.type_.name = "CRM_BASED"
        mock_row.user_list.membership_status.name = "OPEN"
        mock_row.user_list.size_for_search = 500
        mock_row.user_list.size_for_display = 700
        mock_row.user_list.membership_life_span = 10000
        mock_row.user_list.match_rate_percentage = 50
        mock_row.user_list.eligible_for_search = True
        mock_row.user_list.eligible_for_display = True

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(get_user_list("123", "456"))
        assert result["data"]["name"] == "My List"
        assert result["data"]["id"] == "456"

    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_not_found(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.user_lists import get_user_list

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_error(get_user_list("123", "999"))
        assert "not found" in result["error"]

    def test_rejects_invalid_id(self):
        from mcp_google_ads.tools.user_lists import get_user_list

        result = assert_error(get_user_list("123", "abc"))
        assert "Failed to get user list" in result["error"]


class TestCreateCrmUserList:
    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_creates_basic_list(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import create_crm_user_list

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/userLists/789")]
        mock_service = MagicMock()
        mock_service.mutate_user_lists.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_crm_user_list("123", "Test CRM List"))
        assert result["data"]["user_list_id"] == "789"
        assert "Test CRM List" in result["message"]

        mock_service.mutate_user_lists.assert_called_once()

    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_creates_list_with_description(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import create_crm_user_list

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/userLists/790")]
        mock_service = MagicMock()
        mock_service.mutate_user_lists.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_crm_user_list("123", "With Desc", description="My description"))
        assert result["data"]["user_list_id"] == "790"

        operation = client.get_type.return_value
        assert operation.create.description == "My description"

    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_creates_list_with_custom_lifespan(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import create_crm_user_list

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/userLists/791")]
        mock_service = MagicMock()
        mock_service.mutate_user_lists.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(create_crm_user_list("123", "Short Life", membership_life_span=30))
        assert result["data"]["user_list_id"] == "791"

        operation = client.get_type.return_value
        assert operation.create.membership_life_span == 30

    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.user_lists import create_crm_user_list

        result = assert_error(create_crm_user_list("123", "Fail"))
        assert "Failed to create CRM user list" in result["error"]


class TestAddUserListMembers:
    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_adds_emails(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import add_user_list_members

        client = MagicMock()
        mock_client.return_value = client

        mock_job_response = MagicMock()
        mock_job_response.resource_name = "customers/123/offlineUserDataJobs/999"
        mock_job_service = MagicMock()
        mock_job_service.create_offline_user_data_job.return_value = mock_job_response
        mock_get_service.return_value = mock_job_service

        result = assert_success(add_user_list_members("123", "456", emails=["test@example.com", "user@test.com"]))
        assert result["data"]["emails_added"] == 2
        assert result["data"]["phones_added"] == 0
        assert result["data"]["total_members"] == 2

        mock_job_service.add_offline_user_data_job_operations.assert_called_once()
        mock_job_service.run_offline_user_data_job.assert_called_once()

    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_adds_phones(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import add_user_list_members

        client = MagicMock()
        mock_client.return_value = client

        mock_job_response = MagicMock()
        mock_job_response.resource_name = "customers/123/offlineUserDataJobs/998"
        mock_job_service = MagicMock()
        mock_job_service.create_offline_user_data_job.return_value = mock_job_response
        mock_get_service.return_value = mock_job_service

        result = assert_success(add_user_list_members("123", "456", phones=["+5511999999999"]))
        assert result["data"]["phones_added"] == 1
        assert result["data"]["emails_added"] == 0

    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_adds_emails_and_phones(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import add_user_list_members

        client = MagicMock()
        mock_client.return_value = client

        mock_job_response = MagicMock()
        mock_job_response.resource_name = "customers/123/offlineUserDataJobs/997"
        mock_job_service = MagicMock()
        mock_job_service.create_offline_user_data_job.return_value = mock_job_response
        mock_get_service.return_value = mock_job_service

        result = assert_success(
            add_user_list_members("123", "456", emails=["a@b.com"], phones=["+5511988888888"])
        )
        assert result["data"]["emails_added"] == 1
        assert result["data"]["phones_added"] == 1
        assert result["data"]["total_members"] == 2

    def test_rejects_no_emails_or_phones(self):
        from mcp_google_ads.tools.user_lists import add_user_list_members

        result = assert_error(add_user_list_members("123", "456"))
        assert "At least one" in result["error"]

    def test_rejects_invalid_user_list_id(self):
        from mcp_google_ads.tools.user_lists import add_user_list_members

        result = assert_error(add_user_list_members("123", "abc", emails=["test@test.com"]))
        assert "Failed to add user list members" in result["error"]

    def test_hashing_emails(self):
        """Verify that emails are normalized (lowercase, stripped) and SHA256 hashed."""
        email = "  Test@Example.COM  "
        expected_hash = hashlib.sha256(b"test@example.com").hexdigest()
        actual_hash = hashlib.sha256(email.strip().lower().encode()).hexdigest()
        assert actual_hash == expected_hash

    def test_hashing_phones(self):
        """Verify that phones are stripped and SHA256 hashed."""
        phone = "  +5511999999999  "
        expected_hash = hashlib.sha256(b"+5511999999999").hexdigest()
        actual_hash = hashlib.sha256(phone.strip().encode()).hexdigest()
        assert actual_hash == expected_hash

    @patch("mcp_google_ads.tools.user_lists.validate_batch", return_value="Maximum 5000 members per call, received: 6000")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    @patch("mcp_google_ads.tools.user_lists.validate_numeric_id", return_value="456")
    def test_rejects_batch_too_large(self, mock_validate_id, mock_resolve, mock_validate_batch):
        from mcp_google_ads.tools.user_lists import add_user_list_members

        result = assert_error(add_user_list_members("123", "456", emails=["a@b.com"]))
        assert "Maximum 5000" in result["error"]


class TestRemoveUserListMembers:
    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_removes_emails(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import remove_user_list_members

        client = MagicMock()
        mock_client.return_value = client

        mock_job_response = MagicMock()
        mock_job_response.resource_name = "customers/123/offlineUserDataJobs/888"
        mock_job_service = MagicMock()
        mock_job_service.create_offline_user_data_job.return_value = mock_job_response
        mock_get_service.return_value = mock_job_service

        result = assert_success(remove_user_list_members("123", "456", emails=["test@example.com"]))
        assert result["data"]["emails_removed"] == 1
        assert result["data"]["phones_removed"] == 0

        mock_job_service.add_offline_user_data_job_operations.assert_called_once()
        mock_job_service.run_offline_user_data_job.assert_called_once()

    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_removes_phones(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import remove_user_list_members

        client = MagicMock()
        mock_client.return_value = client

        mock_job_response = MagicMock()
        mock_job_response.resource_name = "customers/123/offlineUserDataJobs/887"
        mock_job_service = MagicMock()
        mock_job_service.create_offline_user_data_job.return_value = mock_job_response
        mock_get_service.return_value = mock_job_service

        result = assert_success(remove_user_list_members("123", "456", phones=["+5511999999999"]))
        assert result["data"]["phones_removed"] == 1

    def test_rejects_no_emails_or_phones(self):
        from mcp_google_ads.tools.user_lists import remove_user_list_members

        result = assert_error(remove_user_list_members("123", "456"))
        assert "At least one" in result["error"]

    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.user_lists import remove_user_list_members

        result = assert_error(remove_user_list_members("123", "456", emails=["a@b.com"]))
        assert "Failed to remove user list members" in result["error"]


class TestUpdateUserList:
    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_updates_name(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import update_user_list

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/userLists/456")]
        mock_service = MagicMock()
        mock_service.mutate_user_lists.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_user_list("123", "456", name="New Name"))
        assert result["data"]["user_list_id"] == "456"
        assert "name" in result["data"]["updated_fields"]

        mock_service.mutate_user_lists.assert_called_once()

    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_updates_description(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import update_user_list

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/userLists/456")]
        mock_service = MagicMock()
        mock_service.mutate_user_lists.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_user_list("123", "456", description="Updated desc"))
        assert "description" in result["data"]["updated_fields"]

    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_updates_membership_status(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import update_user_list

        client = MagicMock()
        mock_client.return_value = client

        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name="customers/123/userLists/456")]
        mock_service = MagicMock()
        mock_service.mutate_user_lists.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(update_user_list("123", "456", membership_status="CLOSED"))
        assert "membership_status" in result["data"]["updated_fields"]

    @patch("mcp_google_ads.tools.user_lists.get_service")
    @patch("mcp_google_ads.tools.user_lists.get_client")
    @patch("mcp_google_ads.tools.user_lists.resolve_customer_id", return_value="123")
    def test_rejects_no_fields(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.user_lists import update_user_list

        result = assert_error(update_user_list("123", "456"))
        assert "At least one" in result["error"]

    def test_rejects_invalid_id(self):
        from mcp_google_ads.tools.user_lists import update_user_list

        result = assert_error(update_user_list("123", "abc", name="Test"))
        assert "Failed to update user list" in result["error"]

    def test_rejects_invalid_membership_status(self):
        from mcp_google_ads.tools.user_lists import update_user_list

        result = assert_error(update_user_list("123", "456", membership_status="INVALID;DROP"))
        assert "Failed to update user list" in result["error"]
