"""Maintenance window CRUD tools."""

import json

from mcp.server.fastmcp import FastMCP

from ..client import KumaClient


def register_maintenance_tools(server: FastMCP, client: KumaClient):

    @server.tool()
    async def list_maintenances() -> str:
        """List all maintenance windows."""
        try:
            maintenances = client.api.get_maintenances()
            summary = [
                {
                    "id": m["id"],
                    "title": m.get("title", ""),
                    "strategy": str(m.get("strategy", "")),
                    "active": m.get("active", True),
                    "description": m.get("description", ""),
                }
                for m in maintenances
            ]
            return json.dumps({
                "maintenances": summary,
                "count": len(summary),
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def get_maintenance(id: int) -> str:
        """Get maintenance window details.

        Args:
            id: Maintenance window ID
        """
        try:
            maintenance = client.api.get_maintenance(id)
            return json.dumps({"maintenance": maintenance})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def create_maintenance(
        title: str,
        strategy: str = "manual",
        description: str = "",
        date_range: str = "",
        cron: str = "",
        duration: int = 0,
        timezone: str = "",
        monitor_ids: str = "",
        status_page_ids: str = "",
    ) -> str:
        """Create a maintenance window.

        Args:
            title: Maintenance window title
            strategy: Strategy type (manual, single, recurring-interval, recurring-weekday, recurring-day-of-month, cron)
            description: Description of the maintenance
            date_range: JSON array of [start, end] datetime strings for single strategy
                        e.g. '["2025-01-01 00:00:00", "2025-01-01 06:00:00"]'
            cron: Cron expression for cron strategy (e.g. "0 2 * * *")
            duration: Duration in seconds for recurring strategies
            timezone: Timezone string (e.g. "America/New_York")
            monitor_ids: Comma-separated monitor IDs to include
            status_page_ids: Comma-separated status page IDs to include
        """
        try:
            params = {
                "title": title,
                "strategy": strategy,
                "active": True,
            }
            if description:
                params["description"] = description
            if date_range:
                params["dateRange"] = json.loads(date_range)
            if cron:
                params["cron"] = cron
            if duration:
                params["durationMinutes"] = duration // 60 or 1
            if timezone:
                params["timezone"] = timezone

            result = client.api.add_maintenance(**params)

            maintenance_id = result.get("maintenanceID") or result.get("id")
            if maintenance_id and monitor_ids:
                ids = [int(x.strip()) for x in monitor_ids.split(",")]
                client.api.add_monitor_maintenance(
                    maintenance_id, [{"id": mid} for mid in ids]
                )
            if maintenance_id and status_page_ids:
                ids = [int(x.strip()) for x in status_page_ids.split(",")]
                client.api.add_status_page_maintenance(
                    maintenance_id, [{"id": sid} for sid in ids]
                )

            return json.dumps({"status": "created", "result": result})
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid date_range JSON: {e}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def edit_maintenance(
        id: int,
        title: str = "",
        description: str = "",
        strategy: str = "",
        date_range: str = "",
        cron: str = "",
        duration: int = 0,
        timezone: str = "",
    ) -> str:
        """Update a maintenance window. Only provided fields are changed.

        Args:
            id: Maintenance window ID
            title: Maintenance window title
            description: Description
            strategy: Strategy type
            date_range: JSON array of [start, end] datetime strings
            cron: Cron expression
            duration: Duration in seconds
            timezone: Timezone string
        """
        try:
            params = {}
            if title:
                params["title"] = title
            if description:
                params["description"] = description
            if strategy:
                params["strategy"] = strategy
            if date_range:
                params["dateRange"] = json.loads(date_range)
            if cron:
                params["cron"] = cron
            if duration:
                params["durationMinutes"] = duration // 60 or 1
            if timezone:
                params["timezone"] = timezone

            result = client.api.edit_maintenance(id, **params)
            return json.dumps({"status": "updated", "result": result})
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid date_range JSON: {e}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def delete_maintenance(id: int) -> str:
        """Delete a maintenance window.

        Args:
            id: Maintenance window ID
        """
        try:
            result = client.api.delete_maintenance(id)
            return json.dumps({"status": "deleted", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def pause_maintenance(id: int) -> str:
        """Pause a maintenance window.

        Args:
            id: Maintenance window ID
        """
        try:
            result = client.api.pause_maintenance(id)
            return json.dumps({"status": "paused", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def resume_maintenance(id: int) -> str:
        """Resume a paused maintenance window.

        Args:
            id: Maintenance window ID
        """
        try:
            result = client.api.resume_maintenance(id)
            return json.dumps({"status": "resumed", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})
