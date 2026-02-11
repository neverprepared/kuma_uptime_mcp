"""MCP server setup and tool registration."""

from mcp.server.fastmcp import FastMCP

from .client import KumaClient
from .tools.monitors import register_monitor_tools
from .tools.notifications import register_notification_tools
from .tools.tags import register_tag_tools
from .tools.status_pages import register_status_page_tools
from .tools.maintenance import register_maintenance_tools
from .tools.system import register_system_tools


def create_server() -> tuple[FastMCP, KumaClient]:
    server = FastMCP("mcp-uptime-kuma")
    client = KumaClient()

    register_monitor_tools(server, client)
    register_notification_tools(server, client)
    register_tag_tools(server, client)
    register_status_page_tools(server, client)
    register_maintenance_tools(server, client)
    register_system_tools(server, client)

    return server, client


def run():
    server, _client = create_server()
    server.run(transport="stdio")
