"""Notification provider CRUD tools."""

import json

from mcp.server.fastmcp import FastMCP

from ..client import KumaClient


def register_notification_tools(server: FastMCP, client: KumaClient):

    @server.tool()
    async def list_notifications() -> str:
        """List all notification providers."""
        try:
            notifications = client.api.get_notifications()
            summary = [
                {
                    "id": n["id"],
                    "name": n["name"],
                    "type": str(n.get("type", "")),
                    "active": n.get("active", True),
                    "isDefault": n.get("isDefault", False),
                }
                for n in notifications
            ]
            return json.dumps({
                "notifications": summary,
                "count": len(summary),
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def get_notification(id: int) -> str:
        """Get notification provider details.

        Args:
            id: Notification provider ID
        """
        try:
            notification = client.api.get_notification(id)
            return json.dumps({"notification": notification})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def create_notification(
        name: str,
        type: str,
        config: str = "{}",
        is_default: bool = False,
        apply_existing: bool = False,
    ) -> str:
        """Create a notification provider.

        Args:
            name: Display name for the notification provider
            type: Notification type (e.g. telegram, slack, discord, email, webhook,
                  pushover, gotify, ntfy, apprise, teams, etc.)
            config: JSON string with type-specific configuration.
                    Examples:
                    - telegram: {"telegramBotToken": "...", "telegramChatID": "..."}
                    - slack: {"slackwebhookURL": "..."}
                    - discord: {"discordWebhookURL": "..."}
                    - email/smtp: {"smtpHost": "...", "smtpPort": 587, "smtpFrom": "...", "smtpTo": "..."}
                    - webhook: {"webhookURL": "...", "webhookContentType": "application/json"}
                    - ntfy: {"ntfyserverurl": "...", "ntfytopic": "..."}
                    - gotify: {"gotifyserverurl": "...", "gotifyapplicationToken": "..."}
                    - pushover: {"pushoveruserkey": "...", "pushoverapptoken": "..."}
            is_default: Apply this notification to all new monitors by default
            apply_existing: Apply this notification to all existing monitors
        """
        try:
            parsed_config = json.loads(config) if isinstance(config, str) else config
            params = {
                "name": name,
                "type": type,
                "isDefault": is_default,
                "applyExisting": apply_existing,
                **parsed_config,
            }
            result = client.api.add_notification(**params)
            return json.dumps({"status": "created", "result": result})
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid config JSON: {e}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def edit_notification(
        id: int,
        name: str = "",
        config: str = "",
        is_default: bool = False,
    ) -> str:
        """Update a notification provider. Only provided fields are changed.

        Args:
            id: Notification provider ID
            name: Display name
            config: JSON string with type-specific configuration (see create_notification)
            is_default: Apply to all new monitors by default
        """
        try:
            params = {}
            if name:
                params["name"] = name
            if is_default:
                params["isDefault"] = True
            if config:
                parsed = json.loads(config) if isinstance(config, str) else config
                params.update(parsed)

            result = client.api.edit_notification(id, **params)
            return json.dumps({"status": "updated", "result": result})
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid config JSON: {e}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def delete_notification(id: int) -> str:
        """Delete a notification provider.

        Args:
            id: Notification provider ID
        """
        try:
            result = client.api.delete_notification(id)
            return json.dumps({"status": "deleted", "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.tool()
    async def test_notification(
        type: str,
        name: str,
        config: str = "{}",
    ) -> str:
        """Test a notification provider configuration without saving it.

        Args:
            type: Notification type (telegram, slack, discord, etc.)
            name: Display name for the test
            config: JSON string with type-specific configuration
        """
        try:
            parsed_config = json.loads(config) if isinstance(config, str) else config
            params = {
                "name": name,
                "type": type,
                **parsed_config,
            }
            result = client.api.test_notification(**params)
            return json.dumps({"status": "tested", "result": result})
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid config JSON: {e}"})
        except Exception as e:
            return json.dumps({"error": str(e)})
