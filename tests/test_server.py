"""Tests for server.py entry point."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch


class TestMain:
    @patch("mcp_google_ads.server.mcp")
    @patch("mcp_google_ads.server.logging")
    def test_main_calls_mcp_run(self, mock_logging, mock_mcp):
        """main() deve configurar logging e chamar mcp.run()."""
        mock_logging.getLogger.return_value = MagicMock()
        mock_logging.INFO = logging.INFO

        from mcp_google_ads.server import main

        main()

        mock_mcp.run.assert_called_once()

    @patch("mcp_google_ads.server.mcp")
    @patch("mcp_google_ads.server.os")
    @patch("mcp_google_ads.server.logging")
    def test_log_level_from_env(self, mock_logging, mock_os, mock_mcp):
        """LOG_LEVEL env var deve ser respeitada na configuração de logging."""
        mock_os.getenv.return_value = "DEBUG"
        mock_logging.DEBUG = logging.DEBUG
        mock_logging.INFO = logging.INFO
        mock_logging.getLogger.return_value = MagicMock()

        from mcp_google_ads.server import main

        main()

        mock_os.getenv.assert_called_with("LOG_LEVEL", "INFO")
        mock_logging.basicConfig.assert_called_once()
        call_kwargs = mock_logging.basicConfig.call_args[1]
        assert call_kwargs["level"] == logging.DEBUG
