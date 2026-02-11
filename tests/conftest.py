"""Shared test fixtures with mocked Uptime Kuma API client."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_uptime_kuma.client import KumaClient


@pytest.fixture
def mock_api():
    """Create a mock UptimeKumaApi instance with common return values."""
    api = MagicMock()

    # Monitor methods
    api.get_monitors.return_value = [
        {
            "id": 1,
            "name": "Google",
            "type": "http",
            "url": "https://google.com",
            "active": True,
            "interval": 60,
            "tags": [{"name": "prod", "value": ""}],
        },
        {
            "id": 2,
            "name": "GitHub",
            "type": "http",
            "url": "https://github.com",
            "active": True,
            "interval": 60,
            "tags": [],
        },
    ]
    api.get_monitor.return_value = {
        "id": 1,
        "name": "Google",
        "type": "http",
        "url": "https://google.com",
        "active": True,
        "interval": 60,
    }
    api.add_monitor.return_value = {"monitorID": 3, "msg": "Added Successfully."}
    api.edit_monitor.return_value = {"monitorID": 1, "msg": "Saved."}
    api.delete_monitor.return_value = {"msg": "Deleted Successfully."}
    api.pause_monitor.return_value = {"msg": "Paused Successfully."}
    api.resume_monitor.return_value = {"msg": "Resumed Successfully."}

    # Notification methods
    api.get_notifications.return_value = [
        {"id": 1, "name": "Slack", "type": "slack", "active": True, "isDefault": False},
    ]
    api.get_notification.return_value = {
        "id": 1,
        "name": "Slack",
        "type": "slack",
        "slackwebhookURL": "https://hooks.slack.com/...",
    }
    api.add_notification.return_value = {"id": 2, "msg": "Saved"}
    api.edit_notification.return_value = {"id": 1, "msg": "Saved"}
    api.delete_notification.return_value = {"msg": "Deleted"}
    api.test_notification.return_value = {"ok": True, "msg": "Sent Successfully."}

    # Tag methods
    api.get_tags.return_value = [
        {"id": 1, "name": "prod", "color": "#dc2626"},
        {"id": 2, "name": "staging", "color": "#2563eb"},
    ]
    api.get_tag.return_value = {"id": 1, "name": "prod", "color": "#dc2626"}
    api.add_tag.return_value = {"id": 3, "msg": "Added Successfully."}
    api.edit_tag.return_value = {"msg": "Saved."}
    api.delete_tag.return_value = {"msg": "Deleted Successfully."}
    api.add_monitor_tag.return_value = {"msg": "Added Successfully."}
    api.delete_monitor_tag.return_value = {"msg": "Deleted Successfully."}

    # Status page methods
    api.get_status_pages.return_value = [
        {"id": 1, "slug": "main", "title": "Main Status", "published": True},
    ]
    api.get_status_page.return_value = {
        "id": 1,
        "slug": "main",
        "title": "Main Status",
        "published": True,
    }
    api.add_status_page.return_value = {"msg": "OK"}
    api.save_status_page.return_value = {"msg": "OK"}
    api.delete_status_page.return_value = {"msg": "Deleted"}

    # Maintenance methods
    api.get_maintenances.return_value = [
        {
            "id": 1,
            "title": "Weekly DB Maintenance",
            "strategy": "recurring-weekday",
            "active": True,
            "description": "",
        },
    ]
    api.get_maintenance.return_value = {
        "id": 1,
        "title": "Weekly DB Maintenance",
        "strategy": "recurring-weekday",
        "active": True,
    }
    api.add_maintenance.return_value = {"maintenanceID": 2, "msg": "Added"}
    api.edit_maintenance.return_value = {"msg": "Saved"}
    api.delete_maintenance.return_value = {"msg": "Deleted"}
    api.pause_maintenance.return_value = {"msg": "Paused"}
    api.resume_maintenance.return_value = {"msg": "Resumed"}
    api.add_monitor_maintenance.return_value = {"msg": "OK"}
    api.add_status_page_maintenance.return_value = {"msg": "OK"}

    # System methods
    api.info.return_value = {"version": "2.0.0", "latestVersion": "2.0.0"}
    api.get_monitor_beats.return_value = [
        {"status": 1, "time": "2025-01-01 00:00:00", "ping": 50},
        {"status": 1, "time": "2025-01-01 00:01:00", "ping": 45},
    ]
    api.avg_ping.return_value = 47.5
    api.uptime.return_value = {24: 0.998, 720: 0.995}
    api.cert_info.return_value = {"valid": True, "daysRemaining": 45}
    api.get_database_size.return_value = {"size": 1048576}

    return api


@pytest.fixture
def client(mock_api):
    """Create a KumaClient with a mocked API."""
    with patch.dict("os.environ", {
        "UPTIME_KUMA_URL": "http://localhost:3001",
        "UPTIME_KUMA_USERNAME": "admin",
        "UPTIME_KUMA_PASSWORD": "secret",
    }):
        kc = KumaClient()
        kc._api = mock_api
        return kc


def get_tools(server):
    """Extract tool functions from a FastMCP server instance."""
    return {name: tool.fn for name, tool in server._tool_manager._tools.items()}
