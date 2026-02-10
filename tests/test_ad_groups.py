"""Tests for ad_groups.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success

# --- Helper para criar mock de row de ad_group ---

def _make_ad_group_row(
    ad_group_id=222,
    name="Ad Group 1",
    status="ENABLED",
    type_name="SEARCH_STANDARD",
    cpc_bid_micros=1_500_000,
    cpm_bid_micros=0,
    target_cpa_micros=0,
    target_roas=0.0,
    effective_target_cpa_micros=0,
    campaign_id=111,
    campaign_name="Campaign 1",
):
    row = MagicMock()
    row.ad_group.id = ad_group_id
    row.ad_group.name = name
    row.ad_group.status.name = status
    row.ad_group.type_.name = type_name
    row.ad_group.cpc_bid_micros = cpc_bid_micros
    row.ad_group.cpm_bid_micros = cpm_bid_micros
    row.ad_group.target_cpa_micros = target_cpa_micros
    row.ad_group.target_roas = target_roas
    row.ad_group.effective_target_cpa_micros = effective_target_cpa_micros
    row.campaign.id = campaign_id
    row.campaign.name = campaign_name
    return row


def _mock_mutate_response(resource_name="customers/123/adGroups/222"):
    response = MagicMock()
    result = MagicMock()
    result.resource_name = resource_name
    response.results = [result]
    return response


class TestListAdGroups:
    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_returns_ad_groups(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        mock_row = _make_ad_group_row()
        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_ad_groups("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["ad_groups"][0]["name"] == "Ad Group 1"

    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", side_effect=Exception("fail"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        result = assert_error(list_ad_groups(""))
        assert "Failed" in result["error"]

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_filter_by_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        mock_row = _make_ad_group_row()
        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_ad_groups("123", campaign_id="111"))
        assert result["data"]["count"] == 1
        query_called = mock_service.search.call_args[1]["query"]
        assert "campaign.id = 111" in query_called

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_filter_by_status(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_ad_groups("123", status_filter="PAUSED"))
        assert result["data"]["count"] == 0
        query_called = mock_service.search.call_args[1]["query"]
        assert "ad_group.status = 'PAUSED'" in query_called

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_filter_by_campaign_and_status(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        assert_success(list_ad_groups("123", campaign_id="111", status_filter="ENABLED"))
        query_called = mock_service.search.call_args[1]["query"]
        assert "campaign.id = 111" in query_called
        assert "ad_group.status = 'ENABLED'" in query_called

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_invalid_campaign_id(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        result = assert_error(list_ad_groups("123", campaign_id="abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_empty_response(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_success(list_ad_groups("123"))
        assert result["data"]["count"] == 0
        assert result["data"]["ad_groups"] == []

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_multiple_ad_groups(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        rows = [
            _make_ad_group_row(ad_group_id=1, name="Group A"),
            _make_ad_group_row(ad_group_id=2, name="Group B"),
            _make_ad_group_row(ad_group_id=3, name="Group C"),
        ]
        mock_service = MagicMock()
        mock_service.search.return_value = rows
        mock_get_service.return_value = mock_service

        result = assert_success(list_ad_groups("123"))
        assert result["data"]["count"] == 3

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_invalid_status_filter(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        result = assert_error(list_ad_groups("123", status_filter="INVALID"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_ad_group_fields_mapping(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import list_ad_groups

        mock_row = _make_ad_group_row(
            ad_group_id=555,
            name="Test Group",
            status="PAUSED",
            type_name="DISPLAY_STANDARD",
            cpc_bid_micros=2_000_000,
            campaign_id=999,
            campaign_name="Test Campaign",
        )
        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_ad_groups("123"))
        group = result["data"]["ad_groups"][0]
        assert group["ad_group_id"] == "555"
        assert group["name"] == "Test Group"
        assert group["status"] == "PAUSED"
        assert group["type"] == "DISPLAY_STANDARD"
        assert group["cpc_bid_micros"] == 2_000_000
        assert group["cpc_bid"] == 2.0
        assert group["campaign_id"] == "999"
        assert group["campaign_name"] == "Test Campaign"


class TestGetAdGroup:
    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_returns_ad_group(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import get_ad_group

        mock_row = _make_ad_group_row()
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter([mock_row]))
        mock_service.search.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(get_ad_group("123", "222"))
        assert result["data"]["ad_group_id"] == "222"
        assert result["data"]["name"] == "Ad Group 1"
        assert result["data"]["status"] == "ENABLED"
        assert result["data"]["type"] == "SEARCH_STANDARD"
        assert result["data"]["cpc_bid_micros"] == 1_500_000
        assert result["data"]["cpc_bid"] == 1.5

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_not_found(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import get_ad_group

        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter([]))
        mock_service.search.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_error(get_ad_group("123", "999"))
        assert "not found" in result["error"]

    def test_invalid_ad_group_id(self):
        from mcp_google_ads.tools.ad_groups import get_ad_group

        result = assert_error(get_ad_group("123", "abc"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_returns_target_fields(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import get_ad_group

        mock_row = _make_ad_group_row(target_cpa_micros=5_000_000, target_roas=3.5)
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter([mock_row]))
        mock_service.search.return_value = mock_response
        mock_get_service.return_value = mock_service

        result = assert_success(get_ad_group("123", "222"))
        assert result["data"]["target_cpa_micros"] == 5_000_000
        assert result["data"]["target_roas"] == 3.5

    @patch("mcp_google_ads.tools.ad_groups.get_service", side_effect=Exception("API error"))
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_error_handling(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.ad_groups import get_ad_group

        result = assert_error(get_ad_group("123", "222"))
        assert "Failed to get ad group" in result["error"]


class TestCreateAdGroup:
    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_create_success(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import create_ad_group

        mock_client = MagicMock()
        mock_client.enums.AdGroupStatusEnum.PAUSED = 2
        mock_client.enums.AdGroupTypeEnum.SEARCH_STANDARD = 1

        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response("customers/123/adGroups/555")
        mock_get_service.return_value = mock_service

        result = assert_success(create_ad_group("123", "111", "New Group"))
        assert result["data"]["ad_group_id"] == "555"
        assert result["data"]["status"] == "PAUSED"
        assert "PAUSED" in result["message"]

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_create_with_cpc_bid(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import create_ad_group

        mock_client = MagicMock()
        mock_client.enums.AdGroupStatusEnum.PAUSED = 2
        mock_client.enums.AdGroupTypeEnum.SEARCH_STANDARD = 1

        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response("customers/123/adGroups/556")
        mock_get_service.return_value = mock_service

        result = assert_success(create_ad_group("123", "111", "Group CPC", cpc_bid=2.5))
        assert result["data"]["ad_group_id"] == "556"
        # Verifica que cpc_bid_micros foi setado no mock
        assert operation.create.cpc_bid_micros == 2_500_000

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_create_with_type(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import create_ad_group

        mock_client = MagicMock()
        mock_client.enums.AdGroupStatusEnum.PAUSED = 2
        mock_client.enums.AdGroupTypeEnum.DISPLAY_STANDARD = 2

        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response("customers/123/adGroups/557")
        mock_get_service.return_value = mock_service

        result = assert_success(create_ad_group("123", "111", "Display Group", ad_group_type="DISPLAY_STANDARD"))
        assert result["data"]["ad_group_id"] == "557"

    @patch("mcp_google_ads.tools.ad_groups.get_service", side_effect=Exception("API error"))
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_create_error(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import create_ad_group

        mock_client = MagicMock()
        mock_client.enums.AdGroupStatusEnum.PAUSED = 2
        mock_client.enums.AdGroupTypeEnum.SEARCH_STANDARD = 1
        mock_get_client.return_value = mock_client

        result = assert_error(create_ad_group("123", "111", "Fail Group"))
        assert "Failed to create ad group" in result["error"]

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_create_invalid_type(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import create_ad_group

        mock_client = MagicMock()
        mock_client.enums.AdGroupStatusEnum.PAUSED = 2
        mock_get_client.return_value = mock_client

        result = assert_error(create_ad_group("123", "111", "Bad Type", ad_group_type="INVALID TYPE!"))
        assert "inválido" in result["error"]


class TestUpdateAdGroup:
    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_update_name(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import update_ad_group

        mock_client = MagicMock()
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response("customers/123/adGroups/222")
        mock_get_service.return_value = mock_service

        result = assert_success(update_ad_group("123", "222", name="Updated Name"))
        assert "updated" in result["message"]

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_update_cpc_bid(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import update_ad_group

        mock_client = MagicMock()
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        assert_success(update_ad_group("123", "222", cpc_bid=3.0))
        assert operation.update.cpc_bid_micros == 3_000_000

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_update_target_cpa(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import update_ad_group

        mock_client = MagicMock()
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        assert_success(update_ad_group("123", "222", target_cpa_micros=5_000_000))
        assert operation.update.target_cpa_micros == 5_000_000

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_update_multiple_fields(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import update_ad_group

        mock_client = MagicMock()
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(update_ad_group("123", "222", name="New Name", cpc_bid=1.5, target_cpa_micros=2_000_000))
        assert result["data"]["resource_name"] == "customers/123/adGroups/222"

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_update_no_fields(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import update_ad_group

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = assert_error(update_ad_group("123", "222"))
        assert "No fields to update" in result["error"]

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_update_api_error(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import update_ad_group

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(update_ad_group("123", "222", name="Fail"))
        assert "Failed to update ad group" in result["error"]


class TestSetAdGroupStatus:
    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_set_status_enabled(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import set_ad_group_status

        mock_client = MagicMock()
        mock_client.enums.AdGroupStatusEnum.ENABLED = 1
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(set_ad_group_status("123", "222", "ENABLED"))
        assert result["data"]["new_status"] == "ENABLED"
        assert "ENABLED" in result["message"]

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_set_status_paused(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import set_ad_group_status

        mock_client = MagicMock()
        mock_client.enums.AdGroupStatusEnum.PAUSED = 2
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(set_ad_group_status("123", "222", "PAUSED"))
        assert result["data"]["new_status"] == "PAUSED"

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_set_status_removed(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import set_ad_group_status

        mock_client = MagicMock()
        mock_client.enums.AdGroupStatusEnum.REMOVED = 3
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(set_ad_group_status("123", "222", "REMOVED"))
        assert result["data"]["new_status"] == "REMOVED"

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_invalid_status_with_spaces(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import set_ad_group_status

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = assert_error(set_ad_group_status("123", "222", "NOT VALID"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_invalid_status_special_chars(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import set_ad_group_status

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = assert_error(set_ad_group_status("123", "222", "DROP TABLE;"))
        assert "inválido" in result["error"]

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_set_status_api_error(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import set_ad_group_status

        mock_client = MagicMock()
        mock_client.enums.AdGroupStatusEnum.ENABLED = 1
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(set_ad_group_status("123", "222", "ENABLED"))
        assert "Failed to set ad group status" in result["error"]


class TestRemoveAdGroup:
    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_remove_success(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import remove_ad_group

        mock_client = MagicMock()
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        result = assert_success(remove_ad_group("123", "222"))
        assert "removed" in result["message"]
        assert result["data"]["resource_name"] == "customers/123/adGroups/222"

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_remove_sets_correct_resource_name(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import remove_ad_group

        mock_client = MagicMock()
        operation = MagicMock()
        mock_client.get_type.return_value = operation
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.return_value = _mock_mutate_response()
        mock_get_service.return_value = mock_service

        remove_ad_group("123", "444")
        assert operation.remove == "customers/123/adGroups/444"

    @patch("mcp_google_ads.tools.ad_groups.get_service")
    @patch("mcp_google_ads.tools.ad_groups.get_client")
    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", return_value="123")
    def test_remove_api_error(self, mock_resolve, mock_get_client, mock_get_service):
        from mcp_google_ads.tools.ad_groups import remove_ad_group

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_service = MagicMock()
        mock_service.mutate_ad_groups.side_effect = Exception("API error")
        mock_get_service.return_value = mock_service

        result = assert_error(remove_ad_group("123", "222"))
        assert "Failed to remove ad group" in result["error"]

    @patch("mcp_google_ads.tools.ad_groups.resolve_customer_id", side_effect=Exception("bad customer"))
    def test_remove_bad_customer(self, mock_resolve):
        from mcp_google_ads.tools.ad_groups import remove_ad_group

        result = assert_error(remove_ad_group("bad", "222"))
        assert "Failed to remove ad group" in result["error"]
