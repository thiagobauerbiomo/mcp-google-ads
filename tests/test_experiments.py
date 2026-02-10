"""Tests for experiments.py tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import assert_error, assert_success


class TestListExperiments:
    @patch("mcp_google_ads.tools.experiments.get_service")
    @patch("mcp_google_ads.tools.experiments.resolve_customer_id", return_value="123")
    def test_returns_experiments(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.experiments import list_experiments

        mock_row = MagicMock()
        mock_row.experiment.resource_name = "customers/123/experiments/1"
        mock_row.experiment.name = "Test Experiment"
        mock_row.experiment.description = "Testing"
        mock_row.experiment.status.name = "ENABLED"
        mock_row.experiment.start_date = "2024-01-01"
        mock_row.experiment.end_date = "2024-02-01"

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_row]
        mock_get_service.return_value = mock_service

        result = assert_success(list_experiments("123"))
        assert result["data"]["count"] == 1
        assert result["data"]["experiments"][0]["name"] == "Test Experiment"

    @patch("mcp_google_ads.tools.experiments.resolve_customer_id", side_effect=Exception("No ID"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.experiments import list_experiments

        result = assert_error(list_experiments(""))
        assert "Failed to list experiments" in result["error"]


class TestCreateExperiment:
    @patch("mcp_google_ads.tools.experiments.get_service")
    @patch("mcp_google_ads.tools.experiments.get_client")
    @patch("mcp_google_ads.tools.experiments.resolve_customer_id", return_value="123")
    def test_creates_experiment_basic(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.experiments import create_experiment

        client = MagicMock()
        mock_client.return_value = client

        exp_response = MagicMock()
        exp_response.results = [MagicMock(resource_name="customers/123/experiments/555")]
        exp_service = MagicMock()
        exp_service.mutate_experiments.return_value = exp_response

        arm_service = MagicMock()

        mock_get_service.side_effect = [exp_service, arm_service]

        result = assert_success(create_experiment("123", "Test Exp", "111", 30))
        assert result["data"]["experiment_id"] == "555"
        assert "30%" in result["data"]["traffic_split"]
        assert "70%" in result["data"]["traffic_split"]

        exp_service.mutate_experiments.assert_called_once()
        arm_service.mutate_experiment_arms.assert_called_once()
        exp_service.schedule_experiment.assert_called_once_with(
            resource_name="customers/123/experiments/555"
        )

    @patch("mcp_google_ads.tools.experiments.get_service")
    @patch("mcp_google_ads.tools.experiments.get_client")
    @patch("mcp_google_ads.tools.experiments.resolve_customer_id", return_value="123")
    def test_creates_experiment_with_dates(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.experiments import create_experiment

        client = MagicMock()
        mock_client.return_value = client

        exp_response = MagicMock()
        exp_response.results = [MagicMock(resource_name="customers/123/experiments/556")]
        exp_service = MagicMock()
        exp_service.mutate_experiments.return_value = exp_response

        arm_service = MagicMock()

        mock_get_service.side_effect = [exp_service, arm_service]

        result = assert_success(
            create_experiment("123", "Dated Exp", "111", 40, start_date="2024-01-01", end_date="2024-02-01")
        )
        assert result["data"]["experiment_id"] == "556"

        # Verifica que as datas foram atribuidas ao experimento
        operation = client.get_type.return_value
        assert operation.create.start_date == "2024-01-01"
        assert operation.create.end_date == "2024-02-01"

    @patch("mcp_google_ads.tools.experiments.get_service")
    @patch("mcp_google_ads.tools.experiments.get_client")
    @patch("mcp_google_ads.tools.experiments.resolve_customer_id", return_value="123")
    def test_creates_experiment_with_description(self, mock_resolve, mock_client, mock_get_service):
        from mcp_google_ads.tools.experiments import create_experiment

        client = MagicMock()
        mock_client.return_value = client

        exp_response = MagicMock()
        exp_response.results = [MagicMock(resource_name="customers/123/experiments/557")]
        exp_service = MagicMock()
        exp_service.mutate_experiments.return_value = exp_response

        arm_service = MagicMock()

        mock_get_service.side_effect = [exp_service, arm_service]

        result = assert_success(
            create_experiment("123", "Desc Exp", "111", 50, description="Test description")
        )
        assert result["data"]["experiment_id"] == "557"

        operation = client.get_type.return_value
        assert operation.create.description == "Test description"

    @patch("mcp_google_ads.tools.experiments.resolve_customer_id", side_effect=Exception("Auth failed"))
    def test_error_handling(self, mock_resolve):
        from mcp_google_ads.tools.experiments import create_experiment

        result = assert_error(create_experiment("123", "Fail Exp", "111", 30))
        assert "Failed to create experiment" in result["error"]


class TestGetExperiment:
    @patch("mcp_google_ads.tools.experiments.get_service")
    @patch("mcp_google_ads.tools.experiments.resolve_customer_id", return_value="123")
    def test_returns_experiment_with_arms(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.experiments import get_experiment

        mock_exp_row = MagicMock()
        mock_exp_row.experiment.resource_name = "customers/123/experiments/1"
        mock_exp_row.experiment.name = "Test"
        mock_exp_row.experiment.description = "Desc"
        mock_exp_row.experiment.status.name = "ENABLED"
        mock_exp_row.experiment.start_date = "2024-01-01"
        mock_exp_row.experiment.end_date = "2024-02-01"
        mock_exp_row.experiment.suffix = " [Experiment]"

        mock_arm_row = MagicMock()
        mock_arm_row.experiment_arm.name = "Control"
        mock_arm_row.experiment_arm.control = True
        mock_arm_row.experiment_arm.traffic_split = 80
        mock_arm_row.experiment_arm.campaigns = ["customers/123/campaigns/111"]

        mock_service = MagicMock()
        mock_service.search.side_effect = [[mock_exp_row], [mock_arm_row]]
        mock_get_service.return_value = mock_service

        result = assert_success(get_experiment("123", "1"))
        assert result["data"]["name"] == "Test"
        assert len(result["data"]["arms"]) == 1

    def test_rejects_invalid_experiment_id(self):
        from mcp_google_ads.tools.experiments import get_experiment

        result = assert_error(get_experiment("123", "abc"))
        assert "Failed to get experiment" in result["error"]

    @patch("mcp_google_ads.tools.experiments.get_service")
    @patch("mcp_google_ads.tools.experiments.resolve_customer_id", return_value="123")
    def test_not_found(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.experiments import get_experiment

        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service

        result = assert_error(get_experiment("123", "999"))
        assert "not found" in result["error"]


class TestPromoteExperiment:
    @patch("mcp_google_ads.tools.experiments.get_service")
    @patch("mcp_google_ads.tools.experiments.resolve_customer_id", return_value="123")
    def test_promotes_experiment(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.experiments import promote_experiment

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        result = assert_success(promote_experiment("123", "111"))
        assert result["data"]["action"] == "promoted"
        mock_service.promote_experiment.assert_called_once()

    def test_rejects_invalid_id(self):
        from mcp_google_ads.tools.experiments import promote_experiment

        result = assert_error(promote_experiment("123", "abc"))
        assert "Failed to promote experiment" in result["error"]


class TestEndExperiment:
    @patch("mcp_google_ads.tools.experiments.get_service")
    @patch("mcp_google_ads.tools.experiments.resolve_customer_id", return_value="123")
    def test_ends_experiment(self, mock_resolve, mock_get_service):
        from mcp_google_ads.tools.experiments import end_experiment

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        result = assert_success(end_experiment("123", "111"))
        assert result["data"]["action"] == "ended"
        mock_service.end_experiment.assert_called_once()

    def test_rejects_invalid_id(self):
        from mcp_google_ads.tools.experiments import end_experiment

        result = assert_error(end_experiment("123", "abc"))
        assert "Failed to end experiment" in result["error"]
