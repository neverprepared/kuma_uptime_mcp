"""Tests for status page tools."""

import json

import pytest

from mcp.server.fastmcp import FastMCP
from mcp_uptime_kuma.tools.status_pages import register_status_page_tools
from conftest import get_tools


@pytest.fixture
def sp_tools(client):
    server = FastMCP("test")
    register_status_page_tools(server, client)
    return get_tools(server)


@pytest.mark.asyncio
async def test_list_status_pages(sp_tools, mock_api):
    result = json.loads(await sp_tools["list_status_pages"]())
    assert result["count"] == 1
    assert result["status_pages"][0]["slug"] == "main"


@pytest.mark.asyncio
async def test_get_status_page(sp_tools, mock_api):
    result = json.loads(await sp_tools["get_status_page"](slug="main"))
    assert result["status_page"]["title"] == "Main Status"


@pytest.mark.asyncio
async def test_create_status_page(sp_tools, mock_api):
    result = json.loads(
        await sp_tools["create_status_page"](title="New Page", slug="new-page")
    )
    assert result["status"] == "created"
    mock_api.add_status_page.assert_called_once_with(title="New Page", slug="new-page")


@pytest.mark.asyncio
async def test_create_status_page_with_monitors(sp_tools, mock_api):
    result = json.loads(
        await sp_tools["create_status_page"](
            title="New Page", slug="new-page", monitor_ids="1,2"
        )
    )
    assert result["status"] == "created"
    save_kwargs = mock_api.save_status_page.call_args[1]
    assert len(save_kwargs["publicGroupList"]) == 1
    assert len(save_kwargs["publicGroupList"][0]["monitorList"]) == 2


@pytest.mark.asyncio
async def test_save_status_page(sp_tools, mock_api):
    result = json.loads(
        await sp_tools["save_status_page"](slug="main", title="Updated Title")
    )
    assert result["status"] == "updated"


@pytest.mark.asyncio
async def test_delete_status_page(sp_tools, mock_api):
    result = json.loads(await sp_tools["delete_status_page"](slug="main"))
    assert result["status"] == "deleted"
