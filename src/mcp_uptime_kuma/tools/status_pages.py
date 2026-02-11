"""Status page CRUD tools."""

import json

from mcp.server.fastmcp import FastMCP

from ..client import KumaClient


def register_status_page_tools(server: FastMCP, client: KumaClient):

    @server.tool()
    async def list_status_pages() -> str:
        """List all status pages."""
        try:
            pages = client.api.get_status_pages()
            summary = [
                {
                    "id": p.get("id"),
                    "slug": p.get("slug", ""),
                    "title": p.get("title", ""),
                    "published": p.get("published", True),
                }
                for p in pages
            ]
            return json.dumps({
                "status_pages": summary,
                "count": len(summary),
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def get_status_page(slug: str) -> str:
        """Get status page details.

        Args:
            slug: Status page slug (URL-friendly identifier)
        """
        try:
            page = client.api.get_status_page(slug)
            return json.dumps({"status_page": page})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def create_status_page(
        title: str,
        slug: str,
        description: str = "",
        published: bool = True,
        show_tags: bool = False,
        monitor_ids: str = "",
    ) -> str:
        """Create a status page.

        Args:
            title: Status page title
            slug: URL-friendly slug (e.g. "my-status-page")
            description: Page description
            published: Whether the page is publicly visible
            show_tags: Show monitor tags on the page
            monitor_ids: Comma-separated monitor IDs to include in a default group
        """
        try:
            result = client.api.add_status_page(title=title, slug=slug)

            save_params = {}
            if description:
                save_params["description"] = description
            save_params["published"] = published
            save_params["showTags"] = show_tags

            if monitor_ids:
                ids = [int(x.strip()) for x in monitor_ids.split(",")]
                save_params["publicGroupList"] = [
                    {
                        "name": "Services",
                        "weight": 1,
                        "monitorList": [{"id": mid} for mid in ids],
                    }
                ]

            if save_params:
                client.api.save_status_page(slug, **save_params)

            return json.dumps({"status": "created", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def save_status_page(
        slug: str,
        title: str = "",
        description: str = "",
        published: bool = True,
        show_tags: bool = False,
        monitor_ids: str = "",
    ) -> str:
        """Update a status page's configuration.

        Args:
            slug: Status page slug
            title: Page title
            description: Page description
            published: Whether the page is publicly visible
            show_tags: Show monitor tags on the page
            monitor_ids: Comma-separated monitor IDs (replaces current monitors in default group)
        """
        try:
            params = {"published": published, "showTags": show_tags}
            if title:
                params["title"] = title
            if description:
                params["description"] = description
            if monitor_ids:
                ids = [int(x.strip()) for x in monitor_ids.split(",")]
                params["publicGroupList"] = [
                    {
                        "name": "Services",
                        "weight": 1,
                        "monitorList": [{"id": mid} for mid in ids],
                    }
                ]

            result = client.api.save_status_page(slug, **params)
            return json.dumps({"status": "updated", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def delete_status_page(slug: str) -> str:
        """Delete a status page.

        Args:
            slug: Status page slug
        """
        try:
            result = client.api.delete_status_page(slug)
            return json.dumps({"status": "deleted", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})
