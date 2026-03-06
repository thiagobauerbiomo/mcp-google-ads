"""Tests for campaign_criteria.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListCampaignCriteria:
    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_returns_criteria(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import list_campaign_criteria

        mock_row = MagicMock()
        cc = mock_row.campaign_criterion
        cc.resource_name = "customers/123/campaignCriteria/456~789"
        cc.criterion_id = 789
        cc.type_.name = "KEYWORD"
        cc.negative = False
        cc.bid_modifier = 1.0
        cc.status.name = "ENABLED"
        cc.keyword.text = "test keyword"
        cc.keyword.match_type.name = "EXACT"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_criteria("123", "456"))
        assert result["data"]["count"] == 1
        assert result["data"]["criteria"][0]["type"] == "KEYWORD"
        assert result["data"]["criteria"][0]["keyword_text"] == "test keyword"

    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_filters_by_type(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import list_campaign_criteria

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_criteria("123", "456", criterion_type="LOCATION"))
        assert result["data"]["count"] == 0
        query = mock_service.search.call_args[1]["query"]
        assert "campaign_criterion.type = 'LOCATION'" in query

    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_returns_ip_block_criterion(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import list_campaign_criteria

        mock_row = MagicMock()
        cc = mock_row.campaign_criterion
        cc.resource_name = "customers/123/campaignCriteria/456~111"
        cc.criterion_id = 111
        cc.type_.name = "IP_BLOCK"
        cc.negative = True
        cc.bid_modifier = 0.0
        cc.status.name = "ENABLED"
        cc.ip_block.ip_address = "192.168.1.1"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_campaign_criteria("123", "456", criterion_type="IP_BLOCK"))
        assert result["data"]["criteria"][0]["ip_address"] == "192.168.1.1"
        assert result["data"]["criteria"][0]["negative"] is True

    def test_rejects_invalid_criterion_type(self):
        from mcp_google_ads.tools.campaign_criteria import list_campaign_criteria

        result = assert_error(list_campaign_criteria("123", "456", criterion_type="DROP TABLE"))
        assert "Failed to list campaign criteria" in result["error"]

    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_criteria import list_campaign_criteria

        result = assert_error(list_campaign_criteria("", "456"))
        assert "Failed to list campaign criteria" in result["error"]


class TestAddCampaignCriterion:
    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.get_client")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_adds_ip_block(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import add_campaign_criterion

        client = MagicMock()
        mock_client.return_value = client

        response = MagicMock()
        response.results = [MagicMock(resource_name="customers/123/campaignCriteria/456~789")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_criteria.return_value = response
        mock_get_service.return_value = mock_service

        result = assert_success(add_campaign_criterion("123", "456", "IP_BLOCK", "10.0.0.1", negative=True))
        assert result["data"]["resource_name"] == "customers/123/campaignCriteria/456~789"
        assert "IP_BLOCK" in result["message"]

    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.get_client")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_adds_placement(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import add_campaign_criterion

        client = MagicMock()
        mock_client.return_value = client

        response = MagicMock()
        response.results = [MagicMock(resource_name="customers/123/campaignCriteria/456~790")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_criteria.return_value = response
        mock_get_service.return_value = mock_service

        result = assert_success(add_campaign_criterion("123", "456", "PLACEMENT", "example.com", negative=True))
        assert result["data"]["resource_name"] == "customers/123/campaignCriteria/456~790"

        operation = client.get_type.return_value
        assert operation.create.placement.url == "example.com"
        assert operation.create.negative is True

    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.get_client")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_adds_topic(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import add_campaign_criterion

        client = MagicMock()
        mock_client.return_value = client

        response = MagicMock()
        response.results = [MagicMock(resource_name="customers/123/campaignCriteria/456~791")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_criteria.return_value = response
        mock_get_service.return_value = mock_service

        result = assert_success(add_campaign_criterion("123", "456", "TOPIC", "123"))
        assert result["data"]["resource_name"] == "customers/123/campaignCriteria/456~791"

        operation = client.get_type.return_value
        assert operation.create.topic.topic_constant == "topicConstants/123"

    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.get_client")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_adds_user_list(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import add_campaign_criterion

        client = MagicMock()
        mock_client.return_value = client

        response = MagicMock()
        response.results = [MagicMock(resource_name="customers/123/campaignCriteria/456~792")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_criteria.return_value = response
        mock_get_service.return_value = mock_service

        result = assert_success(add_campaign_criterion("123", "456", "USER_LIST", "999"))
        assert result["data"]["resource_name"] == "customers/123/campaignCriteria/456~792"

        operation = client.get_type.return_value
        assert operation.create.user_list.user_list == "customers/123/userLists/999"

    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.get_client")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_adds_content_label(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import add_campaign_criterion

        client = MagicMock()
        mock_client.return_value = client

        response = MagicMock()
        response.results = [MagicMock(resource_name="customers/123/campaignCriteria/456~793")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_criteria.return_value = response
        mock_get_service.return_value = mock_service

        result = assert_success(add_campaign_criterion("123", "456", "CONTENT_LABEL", "TRAGEDY", negative=True))
        assert result["data"]["resource_name"] == "customers/123/campaignCriteria/456~793"

    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.get_client")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_adds_webpage(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import add_campaign_criterion

        client = MagicMock()
        mock_client.return_value = client

        response = MagicMock()
        response.results = [MagicMock(resource_name="customers/123/campaignCriteria/456~794")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_criteria.return_value = response
        mock_get_service.return_value = mock_service

        result = assert_success(add_campaign_criterion("123", "456", "WEBPAGE", "/products/*"))
        assert result["data"]["resource_name"] == "customers/123/campaignCriteria/456~794"

    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.get_client")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_adds_with_bid_modifier(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import add_campaign_criterion

        client = MagicMock()
        mock_client.return_value = client

        response = MagicMock()
        response.results = [MagicMock(resource_name="customers/123/campaignCriteria/456~795")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_criteria.return_value = response
        mock_get_service.return_value = mock_service

        result = assert_success(
            add_campaign_criterion("123", "456", "PLACEMENT", "site.com", bid_modifier=1.5)
        )
        assert result["data"]["resource_name"] == "customers/123/campaignCriteria/456~795"

        operation = client.get_type.return_value
        assert operation.create.bid_modifier == 1.5

    def test_rejects_unsupported_type(self):
        from mcp_google_ads.tools.campaign_criteria import add_campaign_criterion

        result = assert_error(add_campaign_criterion("123", "456", "LOCATION", "1001566"))
        assert "Unsupported criterion_type" in result["error"]

    def test_rejects_invalid_type(self):
        from mcp_google_ads.tools.campaign_criteria import add_campaign_criterion

        result = assert_error(add_campaign_criterion("123", "456", "DROP TABLE", "value"))
        assert "Failed to add campaign criterion" in result["error"]

    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_criteria import add_campaign_criterion

        result = assert_error(add_campaign_criterion("", "456", "IP_BLOCK", "1.2.3.4"))
        assert "Failed to add campaign criterion" in result["error"]


class TestRemoveCampaignCriterion:
    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.get_client")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_removes_criterion(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import remove_campaign_criterion

        client = MagicMock()
        mock_client.return_value = client

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        result = assert_success(remove_campaign_criterion("123", "456", "789"))
        assert result["data"]["campaign_id"] == "456"
        assert result["data"]["criterion_id"] == "789"
        assert "removed" in result["message"].lower()
        mock_service.mutate_campaign_criteria.assert_called_once()

    def test_rejects_invalid_campaign_id(self):
        from mcp_google_ads.tools.campaign_criteria import remove_campaign_criterion

        result = assert_error(remove_campaign_criterion("123", "abc", "789"))
        assert "Failed to remove campaign criterion" in result["error"]

    def test_rejects_invalid_criterion_id(self):
        from mcp_google_ads.tools.campaign_criteria import remove_campaign_criterion

        result = assert_error(remove_campaign_criterion("123", "456", "abc"))
        assert "Failed to remove campaign criterion" in result["error"]

    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_criteria import remove_campaign_criterion

        result = assert_error(remove_campaign_criterion("", "456", "789"))
        assert "Failed to remove campaign criterion" in result["error"]


class TestExcludeIpAddresses:
    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.get_client")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_excludes_multiple_ips(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import exclude_ip_addresses

        client = MagicMock()
        mock_client.return_value = client

        response = MagicMock()
        response.results = [
            MagicMock(resource_name="customers/123/campaignCriteria/456~1"),
            MagicMock(resource_name="customers/123/campaignCriteria/456~2"),
            MagicMock(resource_name="customers/123/campaignCriteria/456~3"),
        ]
        mock_service = MagicMock()
        mock_service.mutate_campaign_criteria.return_value = response
        mock_get_service.return_value = mock_service

        result = assert_success(exclude_ip_addresses("123", "456", ["10.0.0.1", "10.0.0.2", "10.0.0.3"]))
        assert result["data"]["excluded_ips"] == 3
        assert len(result["data"]["resource_names"]) == 3

        # Verify 3 operations were sent
        ops = mock_service.mutate_campaign_criteria.call_args[1]["operations"]
        assert len(ops) == 3

    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.get_client")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_excludes_single_ip(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import exclude_ip_addresses

        client = MagicMock()
        mock_client.return_value = client

        response = MagicMock()
        response.results = [MagicMock(resource_name="customers/123/campaignCriteria/456~1")]
        mock_service = MagicMock()
        mock_service.mutate_campaign_criteria.return_value = response
        mock_get_service.return_value = mock_service

        result = assert_success(exclude_ip_addresses("123", "456", ["192.168.1.1"]))
        assert result["data"]["excluded_ips"] == 1

    def test_rejects_empty_list(self):
        from mcp_google_ads.tools.campaign_criteria import exclude_ip_addresses

        result = assert_error(exclude_ip_addresses("123", "456", []))
        assert "empty" in result["error"].lower()

    def test_rejects_too_many_ips(self):
        from mcp_google_ads.tools.campaign_criteria import exclude_ip_addresses

        ips = [f"10.0.{i // 256}.{i % 256}" for i in range(501)]
        result = assert_error(exclude_ip_addresses("123", "456", ips))
        assert "500" in result["error"]

    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_criteria import exclude_ip_addresses

        result = assert_error(exclude_ip_addresses("", "456", ["1.2.3.4"]))
        assert "Failed to exclude IP addresses" in result["error"]


class TestListIpExclusions:
    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_returns_ip_exclusions(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import list_ip_exclusions

        mock_row1 = MagicMock()
        mock_row1.campaign_criterion.criterion_id = 111
        mock_row1.campaign_criterion.ip_block.ip_address = "10.0.0.1"
        mock_row1.campaign_criterion.resource_name = "customers/123/campaignCriteria/456~111"

        mock_row2 = MagicMock()
        mock_row2.campaign_criterion.criterion_id = 222
        mock_row2.campaign_criterion.ip_block.ip_address = "10.0.0.2"
        mock_row2.campaign_criterion.resource_name = "customers/123/campaignCriteria/456~222"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row1, mock_row2]
        mock_get_service.return_value = mock_service

        result = assert_success(list_ip_exclusions("123", "456"))
        assert result["data"]["count"] == 2
        assert result["data"]["ip_exclusions"][0]["ip_address"] == "10.0.0.1"
        assert result["data"]["ip_exclusions"][1]["ip_address"] == "10.0.0.2"

    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_returns_empty_list(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import list_ip_exclusions

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_ip_exclusions("123", "456"))
        assert result["data"]["count"] == 0
        assert result["data"]["ip_exclusions"] == []

    @patch("mcp_google_ads.tools.campaign_criteria.get_service")
    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", return_value="123")
    def test_query_filters_correctly(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.campaign_criteria import list_ip_exclusions

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        list_ip_exclusions("123", "456")

        query = mock_service.search.call_args[1]["query"]
        assert "campaign_criterion.type = 'IP_BLOCK'" in query
        assert "campaign_criterion.negative = true" in query

    @patch("mcp_google_ads.tools.campaign_criteria.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.campaign_criteria import list_ip_exclusions

        result = assert_error(list_ip_exclusions("", "456"))
        assert "Failed to list IP exclusions" in result["error"]
