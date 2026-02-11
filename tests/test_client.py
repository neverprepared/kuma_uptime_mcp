"""Tests for the KumaClient wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_uptime_kuma.client import KumaClient


def test_validate_config_missing_url():
    with patch.dict("os.environ", {}, clear=True):
        client = KumaClient()
        with pytest.raises(ValueError, match="UPTIME_KUMA_URL"):
            client._validate_config()


def test_validate_config_missing_auth():
    with patch.dict("os.environ", {"UPTIME_KUMA_URL": "http://localhost:3001"}, clear=True):
        client = KumaClient()
        with pytest.raises(ValueError, match="UPTIME_KUMA_TOKEN"):
            client._validate_config()


def test_validate_config_with_token():
    with patch.dict("os.environ", {
        "UPTIME_KUMA_URL": "http://localhost:3001",
        "UPTIME_KUMA_TOKEN": "some-token",
    }, clear=True):
        client = KumaClient()
        client._validate_config()  # Should not raise


def test_validate_config_with_user_pass():
    with patch.dict("os.environ", {
        "UPTIME_KUMA_URL": "http://localhost:3001",
        "UPTIME_KUMA_USERNAME": "admin",
        "UPTIME_KUMA_PASSWORD": "secret",
    }, clear=True):
        client = KumaClient()
        client._validate_config()  # Should not raise


def test_disconnect():
    with patch.dict("os.environ", {
        "UPTIME_KUMA_URL": "http://localhost:3001",
        "UPTIME_KUMA_USERNAME": "admin",
        "UPTIME_KUMA_PASSWORD": "secret",
    }):
        client = KumaClient()
        mock_api = MagicMock()
        client._api = mock_api
        client.disconnect()
        mock_api.disconnect.assert_called_once()
        assert client._api is None


def test_disconnect_noop_when_not_connected():
    with patch.dict("os.environ", {
        "UPTIME_KUMA_URL": "http://localhost:3001",
        "UPTIME_KUMA_USERNAME": "admin",
        "UPTIME_KUMA_PASSWORD": "secret",
    }):
        client = KumaClient()
        client.disconnect()  # Should not raise
