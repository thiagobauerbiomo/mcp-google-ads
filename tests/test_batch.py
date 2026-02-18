"""Tests for batch.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


def _mock_mutate_response(resource_types):
    """Create a mock mutate response with typed results.

    Args:
        resource_types: list of "campaign" | "ad_group" | "ad"
    """
    _field_map = {"campaign": "campaign_result", "ad_group": "ad_group_result", "ad": "ad_group_ad_result"}
    mock_response = MagicMock()
    results = []
    for i, rt in enumerate(resource_types):
        result = MagicMock(spec=[])  # spec=[] evita auto-create de atributos
        field = _field_map[rt]
        sub_result = MagicMock()
        sub_result.resource_name = f"customers/123/{rt}s/{i}"
        setattr(result, field, sub_result)
        results.append(result)
    mock_response.mutate_operation_responses = results
    return mock_response


class TestBatchSetStatus:
    @patch("mcp_google_ads.tools.batch.get_service")
    @patch("mcp_google_ads.tools.batch.get_client")
    @patch("mcp_google_ads.tools.batch.resolve_customer_id", return_value="123")
    def test_batch_campaigns(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.batch import batch_set_status

        mock_service = MagicMock()
        mock_service.mutate.return_value = _mock_mutate_response(["campaign", "campaign"])
        mock_get_service.return_value = mock_service

        resources = [
            {"type": "campaign", "id": "111"},
            {"type": "campaign", "id": "222"},
        ]
        result = assert_success(batch_set_status("123", resources, "PAUSED"))
        assert result["data"]["successful_operations"] == 2
        assert "PAUSED" in result["message"]
        mock_service.mutate.assert_called_once()

    @patch("mcp_google_ads.tools.batch.get_service")
    @patch("mcp_google_ads.tools.batch.get_client")
    @patch("mcp_google_ads.tools.batch.resolve_customer_id", return_value="123")
    def test_batch_mixed_resources(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.batch import batch_set_status

        mock_service = MagicMock()
        mock_service.mutate.return_value = _mock_mutate_response(["campaign", "ad_group", "ad"])
        mock_get_service.return_value = mock_service

        resources = [
            {"type": "campaign", "id": "111"},
            {"type": "ad_group", "id": "222"},
            {"type": "ad", "id": "333", "ad_group_id": "222"},
        ]
        result = assert_success(batch_set_status("123", resources, "ENABLED"))
        assert result["data"]["successful_operations"] == 3
        assert "ENABLED" in result["message"]

        # Verificar que mutate foi chamado com 3 operações
        call_args = mock_service.mutate.call_args
        assert len(call_args.kwargs["mutate_operations"]) == 3

    def test_rejects_removed_status(self):
        from mcp_google_ads.tools.batch import batch_set_status

        resources = [{"type": "campaign", "id": "111"}]
        result = assert_error(batch_set_status("123", resources, "REMOVED"))
        assert "REMOVED not allowed" in result["error"]

    @patch("mcp_google_ads.tools.batch.get_client")
    @patch("mcp_google_ads.tools.batch.resolve_customer_id", return_value="123")
    def test_rejects_invalid_type(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.batch import batch_set_status

        resources = [{"type": "keyword", "id": "111"}]
        result = assert_error(batch_set_status("123", resources, "PAUSED"))
        assert "invalid type" in result["error"]

    @patch("mcp_google_ads.tools.batch.get_client")
    @patch("mcp_google_ads.tools.batch.resolve_customer_id", return_value="123")
    def test_requires_ad_group_id_for_ads(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.batch import batch_set_status

        resources = [{"type": "ad", "id": "789"}]
        result = assert_error(batch_set_status("123", resources, "PAUSED"))
        assert "ad_group_id is required" in result["error"]

    @patch("mcp_google_ads.tools.batch.resolve_customer_id", side_effect=Exception("connection error"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.batch import batch_set_status

        resources = [{"type": "campaign", "id": "111"}]
        result = assert_error(batch_set_status("123", resources, "PAUSED"))
        assert "Failed to batch set status" in result["error"]

    def test_empty_resources(self):
        from mcp_google_ads.tools.batch import batch_set_status

        result = assert_error(batch_set_status("123", [], "PAUSED"))
        assert "empty" in result["error"]

    @patch("mcp_google_ads.tools.batch.get_client")
    @patch("mcp_google_ads.tools.batch.resolve_customer_id", return_value="123")
    def test_max_limit(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.batch import batch_set_status

        resources = [{"type": "campaign", "id": str(i)} for i in range(101)]
        result = assert_error(batch_set_status("123", resources, "PAUSED"))
        assert "Maximum 100" in result["error"]

    @patch("mcp_google_ads.tools.batch.get_client")
    @patch("mcp_google_ads.tools.batch.resolve_customer_id", return_value="123")
    def test_rejects_missing_id(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.batch import batch_set_status

        resources = [{"type": "campaign"}]
        result = assert_error(batch_set_status("123", resources, "PAUSED"))
        assert "missing required field 'id'" in result["error"]

    @patch("mcp_google_ads.tools.batch.get_client")
    @patch("mcp_google_ads.tools.batch.resolve_customer_id", return_value="123")
    def test_rejects_invalid_id(self, mock_resolve, mock_client):
        from mcp_google_ads.tools.batch import batch_set_status

        resources = [{"type": "campaign", "id": "DROP TABLE"}]
        result = assert_error(batch_set_status("123", resources, "PAUSED"))
        assert "Failed to batch set status" in result["error"]

    @patch("mcp_google_ads.tools.batch.get_service")
    @patch("mcp_google_ads.tools.batch.get_client")
    @patch("mcp_google_ads.tools.batch.resolve_customer_id", return_value="123")
    def test_api_error_propagated(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.batch import batch_set_status

        mock_service = MagicMock()
        mock_service.mutate.side_effect = Exception("Google Ads API error")
        mock_get_service.return_value = mock_service

        resources = [{"type": "campaign", "id": "111"}]
        result = assert_error(batch_set_status("123", resources, "PAUSED"))
        assert "Failed to batch set status" in result["error"]
        assert "Google Ads API error" in result["error"]
