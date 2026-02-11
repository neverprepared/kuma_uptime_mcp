"""Tests for maintenance tools."""

import json

import pytest

from mcp.server.fastmcp import FastMCP
from mcp_uptime_kuma.tools.maintenance import register_maintenance_tools
from conftest import get_tools


@pytest.fixture
def maint_tools(client):
    server = FastMCP("test")
    register_maintenance_tools(server, client)
    return get_tools(server)


@pytest.mark.asyncio
async def test_list_maintenances(maint_tools, mock_api):
    result = json.loads(await maint_tools["list_maintenances"]())
    assert result["count"] == 1
    assert result["maintenances"][0]["title"] == "Weekly DB Maintenance"


@pytest.mark.asyncio
async def test_get_maintenance(maint_tools, mock_api):
    result = json.loads(await maint_tools["get_maintenance"](id=1))
    assert result["maintenance"]["title"] == "Weekly DB Maintenance"


@pytest.mark.asyncio
async def test_create_maintenance(maint_tools, mock_api):
    result = json.loads(
        await maint_tools["create_maintenance"](title="Deploy Window", strategy="manual")
    )
    assert result["status"] == "created"
    call_kwargs = mock_api.add_maintenance.call_args[1]
    assert call_kwargs["title"] == "Deploy Window"
    assert call_kwargs["strategy"] == "manual"


@pytest.mark.asyncio
async def test_create_maintenance_with_monitors(maint_tools, mock_api):
    result = json.loads(
        await maint_tools["create_maintenance"](
            title="Deploy", strategy="manual", monitor_ids="1,2"
        )
    )
    assert result["status"] == "created"
    mock_api.add_monitor_maintenance.assert_called_once()


@pytest.mark.asyncio
async def test_edit_maintenance(maint_tools, mock_api):
    result = json.loads(
        await maint_tools["edit_maintenance"](id=1, title="Updated Window")
    )
    assert result["status"] == "updated"
    mock_api.edit_maintenance.assert_called_once_with(1, title="Updated Window")


@pytest.mark.asyncio
async def test_delete_maintenance(maint_tools, mock_api):
    result = json.loads(await maint_tools["delete_maintenance"](id=1))
    assert result["status"] == "deleted"


@pytest.mark.asyncio
async def test_pause_maintenance(maint_tools, mock_api):
    result = json.loads(await maint_tools["pause_maintenance"](id=1))
    assert result["status"] == "paused"


@pytest.mark.asyncio
async def test_resume_maintenance(maint_tools, mock_api):
    result = json.loads(await maint_tools["resume_maintenance"](id=1))
    assert result["status"] == "resumed"
