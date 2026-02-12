"""Monitor CRUD tools."""

import json

from mcp.server.fastmcp import FastMCP

from ..client import KumaClient


def register_monitor_tools(server: FastMCP, client: KumaClient):

    @server.tool()
    async def list_monitors(
        filter_type: str = "",
        filter_tag: str = "",
    ) -> str:
        """List all monitors with current status.

        Args:
            filter_type: Filter by monitor type (http, port, ping, dns, docker, push, etc.)
            filter_tag: Filter by tag name
        """
        try:
            monitors = client.api.get_monitors()
            if filter_type:
                monitors = [
                    m for m in monitors
                    if str(m.get("type", "")).lower() == filter_type.lower()
                ]
            if filter_tag:
                monitors = [
                    m for m in monitors
                    if any(
                        t.get("name", "").lower() == filter_tag.lower()
                        for t in m.get("tags", [])
                    )
                ]
            summary = [
                {
                    "id": m["id"],
                    "name": m["name"],
                    "type": str(m.get("type", "")),
                    "url": m.get("url", ""),
                    "active": m.get("active", True),
                    "interval": m.get("interval"),
                }
                for m in monitors
            ]
            return json.dumps({"monitors": summary, "count": len(summary)})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def get_monitor(id: int) -> str:
        """Get detailed monitor configuration and status.

        Args:
            id: Monitor ID
        """
        try:
            monitor = client.api.get_monitor(id)
            return json.dumps({"monitor": monitor})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def create_monitor(
        type: str,
        name: str,
        url: str = "",
        interval: int = 60,
        retry_interval: int = 60,
        max_retries: int = 0,
        keyword: str = "",
        description: str = "",
        notification_ids: str = "",
        upside_down: bool = False,
        ignore_tls: bool = False,
        accepted_statuscodes: str = "",
        method: str = "GET",
        body: str = "",
        headers: str = "",
        max_redirects: int = 10,
        hostname: str = "",
        port: int = 0,
        dns_resolve_type: str = "",
        docker_host: int = 0,
        docker_container: str = "",
    ) -> str:
        """Create a new monitor.

        Args:
            type: Monitor type (http, port, ping, keyword, dns, docker, push, mqtt, grpc, etc.)
            name: Display name for the monitor
            url: Target URL or hostname (for http, keyword, dns types)
            interval: Check interval in seconds (minimum 20)
            retry_interval: Retry interval in seconds
            max_retries: Number of retries before marking down
            keyword: Keyword to search for in response (for keyword type)
            description: Monitor description
            notification_ids: Comma-separated notification provider IDs to attach
            upside_down: Flip status (DOWN = success, UP = failure)
            ignore_tls: Ignore TLS certificate errors
            accepted_statuscodes: Comma-separated accepted status codes (e.g. "200,301")
            method: HTTP method (GET, POST, PUT, etc.)
            body: HTTP request body
            headers: HTTP request headers as JSON string
            max_redirects: Maximum number of redirects to follow
            hostname: Hostname for ping, port, dns types
            port: Port number for port type monitors
            dns_resolve_type: DNS record type (A, AAAA, CNAME, MX, etc.)
            docker_host: Docker host ID for docker type
            docker_container: Docker container name/ID for docker type
        """
        try:
            params = {
                "type": type,
                "name": name,
                "interval": max(interval, 20),
                "retryInterval": retry_interval,
                "maxretries": max_retries,
                "upsideDown": upside_down,
                "maxredirects": max_redirects,
                "conditions": [],
            }
            if url:
                params["url"] = url
            if keyword:
                params["keyword"] = keyword
            if description:
                params["description"] = description
            if ignore_tls:
                params["ignoreTls"] = True
            if accepted_statuscodes:
                params["accepted_statuscodes"] = [
                    s.strip() for s in accepted_statuscodes.split(",")
                ]
            else:
                params["accepted_statuscodes"] = ["200-299"]
            if method != "GET":
                params["method"] = method
            if body:
                params["body"] = body
            if headers:
                params["headers"] = headers
            if hostname:
                params["hostname"] = hostname
            if port:
                params["port"] = port
            if dns_resolve_type:
                params["dns_resolve_type"] = dns_resolve_type
            if docker_host:
                params["docker_host"] = docker_host
            if docker_container:
                params["docker_container"] = docker_container

            if notification_ids:
                nid_list = [
                    int(x.strip()) for x in notification_ids.split(",")
                ]
                params["notificationIDList"] = {
                    str(nid): True for nid in nid_list
                }
            else:
                params["notificationIDList"] = {}

            result = client.api.add_monitor(**params)
            return json.dumps({"status": "created", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def edit_monitor(
        id: int,
        name: str = "",
        url: str = "",
        interval: int = 0,
        retry_interval: int = 0,
        max_retries: int = -1,
        keyword: str = "",
        description: str = "",
        upside_down: bool = False,
        ignore_tls: bool = False,
        accepted_statuscodes: str = "",
        method: str = "",
        body: str = "",
        headers: str = "",
        max_redirects: int = -1,
    ) -> str:
        """Update an existing monitor's configuration. Only provided fields are changed.

        Args:
            id: Monitor ID
            name: Display name
            url: Target URL or hostname
            interval: Check interval in seconds
            retry_interval: Retry interval in seconds
            max_retries: Number of retries before marking down
            keyword: Keyword to search for
            description: Monitor description
            upside_down: Flip status
            ignore_tls: Ignore TLS certificate errors
            accepted_statuscodes: Comma-separated accepted status codes
            method: HTTP method
            body: HTTP request body
            headers: HTTP request headers as JSON string
            max_redirects: Maximum redirects to follow
        """
        try:
            params = {}
            if name:
                params["name"] = name
            if url:
                params["url"] = url
            if interval > 0:
                params["interval"] = max(interval, 20)
            if retry_interval > 0:
                params["retryInterval"] = retry_interval
            if max_retries >= 0:
                params["maxretries"] = max_retries
            if keyword:
                params["keyword"] = keyword
            if description:
                params["description"] = description
            if upside_down:
                params["upsideDown"] = True
            if ignore_tls:
                params["ignoreTls"] = True
            if accepted_statuscodes:
                params["accepted_statuscodes"] = [
                    s.strip() for s in accepted_statuscodes.split(",")
                ]
            if method:
                params["method"] = method
            if body:
                params["body"] = body
            if headers:
                params["headers"] = headers
            if max_redirects >= 0:
                params["maxredirects"] = max_redirects

            result = client.api.edit_monitor(id, **params)
            return json.dumps({"status": "updated", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def delete_monitor(id: int) -> str:
        """Delete a monitor.

        Args:
            id: Monitor ID
        """
        try:
            result = client.api.delete_monitor(id)
            return json.dumps({"status": "deleted", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def pause_monitor(id: int) -> str:
        """Pause a monitor (stops checking).

        Args:
            id: Monitor ID
        """
        try:
            result = client.api.pause_monitor(id)
            return json.dumps({"status": "paused", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def resume_monitor(id: int) -> str:
        """Resume a paused monitor.

        Args:
            id: Monitor ID
        """
        try:
            result = client.api.resume_monitor(id)
            return json.dumps({"status": "resumed", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})
