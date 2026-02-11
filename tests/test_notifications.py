"""Tests for notification tools."""

import json

import pytest

from mcp.server.fastmcp import FastMCP
from mcp_uptime_kuma.tools.notifications import register_notification_tools
from conftest import get_tools


@pytest.fixture
def notification_tools(client):
    server = FastMCP("test")
    register_notification_tools(server, client)
    return get_tools(server)


@pytest.mark.asyncio
async def test_list_notifications(notification_tools, mock_api):
    result = json.loads(await notification_tools["list_notifications"]())
    assert result["count"] == 1
    assert result["notifications"][0]["name"] == "Slack"


@pytest.mark.asyncio
async def test_get_notification(notification_tools, mock_api):
    result = json.loads(await notification_tools["get_notification"](id=1))
    assert result["notification"]["name"] == "Slack"


@pytest.mark.asyncio
async def test_create_notification(notification_tools, mock_api):
    config = json.dumps({"slackwebhookURL": "https://hooks.slack.com/test"})
    result = json.loads(
        await notification_tools["create_notification"](
            name="Test Slack", type="slack", config=config
        )
    )
    assert result["status"] == "created"
    call_kwargs = mock_api.add_notification.call_args[1]
    assert call_kwargs["name"] == "Test Slack"
    assert call_kwargs["type"] == "slack"
    assert call_kwargs["slackwebhookURL"] == "https://hooks.slack.com/test"


@pytest.mark.asyncio
async def test_create_notification_invalid_json(notification_tools):
    result = json.loads(
        await notification_tools["create_notification"](
            name="Bad", type="slack", config="not json"
        )
    )
    assert "error" in result
    assert "Invalid config JSON" in result["error"]


@pytest.mark.asyncio
async def test_edit_notification(notification_tools, mock_api):
    result = json.loads(
        await notification_tools["edit_notification"](id=1, name="Updated Slack")
    )
    assert result["status"] == "updated"


@pytest.mark.asyncio
async def test_delete_notification(notification_tools, mock_api):
    result = json.loads(await notification_tools["delete_notification"](id=1))
    assert result["status"] == "deleted"


@pytest.mark.asyncio
async def test_test_notification(notification_tools, mock_api):
    config = json.dumps({"slackwebhookURL": "https://hooks.slack.com/test"})
    result = json.loads(
        await notification_tools["test_notification"](
            type="slack", name="Test", config=config
        )
    )
    assert result["status"] == "tested"
