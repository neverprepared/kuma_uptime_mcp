"""Tests for tag tools."""

import json

import pytest

from mcp.server.fastmcp import FastMCP
from mcp_uptime_kuma.tools.tags import register_tag_tools
from conftest import get_tools


@pytest.fixture
def tag_tools(client):
    server = FastMCP("test")
    register_tag_tools(server, client)
    return get_tools(server)


@pytest.mark.asyncio
async def test_list_tags(tag_tools, mock_api):
    result = json.loads(await tag_tools["list_tags"]())
    assert result["count"] == 2
    assert result["tags"][0]["name"] == "prod"


@pytest.mark.asyncio
async def test_get_tag(tag_tools, mock_api):
    result = json.loads(await tag_tools["get_tag"](id=1))
    assert result["tag"]["name"] == "prod"


@pytest.mark.asyncio
async def test_create_tag(tag_tools, mock_api):
    result = json.loads(await tag_tools["create_tag"](name="critical", color="#ef4444"))
    assert result["status"] == "created"
    mock_api.add_tag.assert_called_once_with(name="critical", color="#ef4444")


@pytest.mark.asyncio
async def test_edit_tag(tag_tools, mock_api):
    result = json.loads(await tag_tools["edit_tag"](id=1, name="production"))
    assert result["status"] == "updated"
    mock_api.edit_tag.assert_called_once_with(1, name="production")


@pytest.mark.asyncio
async def test_delete_tag(tag_tools, mock_api):
    result = json.loads(await tag_tools["delete_tag"](id=1))
    assert result["status"] == "deleted"


@pytest.mark.asyncio
async def test_add_monitor_tag(tag_tools, mock_api):
    result = json.loads(
        await tag_tools["add_monitor_tag"](tag_id=1, monitor_id=1, value="primary")
    )
    assert result["status"] == "added"
    mock_api.add_monitor_tag.assert_called_once_with(
        tag_id=1, monitor_id=1, value="primary"
    )


@pytest.mark.asyncio
async def test_remove_monitor_tag(tag_tools, mock_api):
    result = json.loads(
        await tag_tools["remove_monitor_tag"](tag_id=1, monitor_id=1)
    )
    assert result["status"] == "removed"
