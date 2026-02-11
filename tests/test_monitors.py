"""Tests for monitor tools."""

import json

import pytest

from mcp.server.fastmcp import FastMCP
from mcp_uptime_kuma.tools.monitors import register_monitor_tools
from conftest import get_tools


@pytest.fixture
def monitor_tools(client):
    server = FastMCP("test")
    register_monitor_tools(server, client)
    return get_tools(server)


@pytest.mark.asyncio
async def test_list_monitors(monitor_tools, mock_api):
    result = json.loads(await monitor_tools["list_monitors"]())
    assert result["count"] == 2
    assert result["monitors"][0]["name"] == "Google"


@pytest.mark.asyncio
async def test_list_monitors_filter_tag(monitor_tools, mock_api):
    result = json.loads(await monitor_tools["list_monitors"](filter_tag="prod"))
    assert result["count"] == 1
    assert result["monitors"][0]["name"] == "Google"


@pytest.mark.asyncio
async def test_get_monitor(monitor_tools, mock_api):
    result = json.loads(await monitor_tools["get_monitor"](id=1))
    assert result["monitor"]["name"] == "Google"
    mock_api.get_monitor.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_create_monitor(monitor_tools, mock_api):
    result = json.loads(
        await monitor_tools["create_monitor"](type="http", name="Test", url="https://test.com")
    )
    assert result["status"] == "created"
    mock_api.add_monitor.assert_called_once()
    call_kwargs = mock_api.add_monitor.call_args[1]
    assert call_kwargs["name"] == "Test"
    assert call_kwargs["type"] == "http"
    assert call_kwargs["url"] == "https://test.com"


@pytest.mark.asyncio
async def test_create_monitor_with_notifications(monitor_tools, mock_api):
    result = json.loads(
        await monitor_tools["create_monitor"](
            type="http", name="Test", url="https://test.com", notification_ids="1,2"
        )
    )
    assert result["status"] == "created"
    call_kwargs = mock_api.add_monitor.call_args[1]
    assert call_kwargs["notificationIDList"] == {"1": True, "2": True}


@pytest.mark.asyncio
async def test_create_monitor_min_interval(monitor_tools, mock_api):
    await monitor_tools["create_monitor"](type="http", name="Test", interval=5)
    call_kwargs = mock_api.add_monitor.call_args[1]
    assert call_kwargs["interval"] == 20


@pytest.mark.asyncio
async def test_edit_monitor(monitor_tools, mock_api):
    result = json.loads(
        await monitor_tools["edit_monitor"](id=1, name="Updated")
    )
    assert result["status"] == "updated"
    mock_api.edit_monitor.assert_called_once_with(1, name="Updated")


@pytest.mark.asyncio
async def test_delete_monitor(monitor_tools, mock_api):
    result = json.loads(await monitor_tools["delete_monitor"](id=1))
    assert result["status"] == "deleted"
    mock_api.delete_monitor.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_pause_monitor(monitor_tools, mock_api):
    result = json.loads(await monitor_tools["pause_monitor"](id=1))
    assert result["status"] == "paused"


@pytest.mark.asyncio
async def test_resume_monitor(monitor_tools, mock_api):
    result = json.loads(await monitor_tools["resume_monitor"](id=1))
    assert result["status"] == "resumed"


@pytest.mark.asyncio
async def test_monitor_error_handling(monitor_tools, mock_api):
    mock_api.get_monitors.side_effect = Exception("Connection lost")
    result = json.loads(await monitor_tools["list_monitors"]())
    assert "error" in result
    assert "Connection lost" in result["error"]
