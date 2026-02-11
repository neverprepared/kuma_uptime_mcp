"""Tests for system tools."""

import json

import pytest

from mcp.server.fastmcp import FastMCP
from mcp_uptime_kuma.tools.system import register_system_tools
from conftest import get_tools


@pytest.fixture
def sys_tools(client):
    server = FastMCP("test")
    register_system_tools(server, client)
    return get_tools(server)


@pytest.mark.asyncio
async def test_get_server_info(sys_tools, mock_api):
    result = json.loads(await sys_tools["get_server_info"]())
    assert result["info"]["version"] == "2.0.0"


@pytest.mark.asyncio
async def test_get_monitor_beats(sys_tools, mock_api):
    result = json.loads(await sys_tools["get_monitor_beats"](id=1, hours=24))
    assert result["count"] == 2
    assert result["monitor_id"] == 1


@pytest.mark.asyncio
async def test_get_monitor_avg_ping(sys_tools, mock_api):
    result = json.loads(await sys_tools["get_monitor_avg_ping"](id=1))
    assert result["avg_ping"] == 47.5


@pytest.mark.asyncio
async def test_get_monitor_uptime(sys_tools, mock_api):
    result = json.loads(await sys_tools["get_monitor_uptime"](id=1))
    assert result["monitor_id"] == 1


@pytest.mark.asyncio
async def test_get_monitor_cert_info(sys_tools, mock_api):
    result = json.loads(await sys_tools["get_monitor_cert_info"](id=1))
    assert result["cert_info"]["valid"] is True


@pytest.mark.asyncio
async def test_get_database_size(sys_tools, mock_api):
    result = json.loads(await sys_tools["get_database_size"]())
    assert result["database_size"]["size"] == 1048576
