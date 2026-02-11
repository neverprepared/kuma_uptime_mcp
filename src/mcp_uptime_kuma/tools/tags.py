"""Tag CRUD tools."""

import json

from mcp.server.fastmcp import FastMCP

from ..client import KumaClient


def register_tag_tools(server: FastMCP, client: KumaClient):

    @server.tool()
    async def list_tags() -> str:
        """List all tags."""
        try:
            tags = client.api.get_tags()
            summary = [
                {
                    "id": t["id"],
                    "name": t.get("name", ""),
                    "color": t.get("color", ""),
                }
                for t in tags
            ]
            return json.dumps({"tags": summary, "count": len(summary)})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def get_tag(id: int) -> str:
        """Get tag details.

        Args:
            id: Tag ID
        """
        try:
            tag = client.api.get_tag(id)
            return json.dumps({"tag": tag})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def create_tag(
        name: str,
        color: str = "#2563eb",
    ) -> str:
        """Create a tag.

        Args:
            name: Tag name
            color: Tag color as hex code (e.g. #2563eb)
        """
        try:
            result = client.api.add_tag(name=name, color=color)
            return json.dumps({"status": "created", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def edit_tag(
        id: int,
        name: str = "",
        color: str = "",
    ) -> str:
        """Update a tag. Only provided fields are changed.

        Args:
            id: Tag ID
            name: Tag name
            color: Tag color as hex code
        """
        try:
            params = {}
            if name:
                params["name"] = name
            if color:
                params["color"] = color
            result = client.api.edit_tag(id, **params)
            return json.dumps({"status": "updated", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def delete_tag(id: int) -> str:
        """Delete a tag.

        Args:
            id: Tag ID
        """
        try:
            result = client.api.delete_tag(id)
            return json.dumps({"status": "deleted", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def add_monitor_tag(
        tag_id: int,
        monitor_id: int,
        value: str = "",
    ) -> str:
        """Add a tag to a monitor.

        Args:
            tag_id: Tag ID
            monitor_id: Monitor ID
            value: Optional tag value for this monitor
        """
        try:
            result = client.api.add_monitor_tag(
                tag_id=tag_id, monitor_id=monitor_id, value=value
            )
            return json.dumps({"status": "added", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def remove_monitor_tag(
        tag_id: int,
        monitor_id: int,
        value: str = "",
    ) -> str:
        """Remove a tag from a monitor.

        Args:
            tag_id: Tag ID
            monitor_id: Monitor ID
            value: Tag value to remove
        """
        try:
            result = client.api.delete_monitor_tag(
                tag_id=tag_id, monitor_id=monitor_id, value=value
            )
            return json.dumps({"status": "removed", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})
