"""System info and monitoring data tools."""

import json

from mcp.server.fastmcp import FastMCP

from ..client import KumaClient


def register_system_tools(server: FastMCP, client: KumaClient):

    @server.tool()
    async def get_server_info() -> str:
        """Get Uptime Kuma server version, uptime, and settings."""
        try:
            info = client.api.info()
            return json.dumps({"info": info})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def get_monitor_beats(
        id: int,
        hours: int = 24,
    ) -> str:
        """Get heartbeat history for a monitor.

        Args:
            id: Monitor ID
            hours: Number of hours of history to retrieve (default 24)
        """
        try:
            beats = client.api.get_monitor_beats(id, hours)
            return json.dumps({
                "monitor_id": id,
                "hours": hours,
                "beats": beats,
                "count": len(beats),
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def get_monitor_avg_ping(id: int) -> str:
        """Get the average ping for a monitor.

        Args:
            id: Monitor ID
        """
        try:
            result = client.api.avg_ping(id)
            return json.dumps({"monitor_id": id, "avg_ping": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def get_monitor_uptime(id: int) -> str:
        """Get uptime percentage for a monitor.

        Args:
            id: Monitor ID
        """
        try:
            result = client.api.uptime(id)
            return json.dumps({"monitor_id": id, "uptime": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def get_monitor_cert_info(id: int) -> str:
        """Get TLS/SSL certificate info for a monitor.

        Args:
            id: Monitor ID
        """
        try:
            result = client.api.cert_info(id)
            return json.dumps({"monitor_id": id, "cert_info": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def get_database_size() -> str:
        """Get the Uptime Kuma database size."""
        try:
            result = client.api.get_database_size()
            return json.dumps({"database_size": result})
        except Exception as e:
            return json.dumps({"error": str(e)})
