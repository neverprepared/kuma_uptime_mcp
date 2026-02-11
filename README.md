# mcp-uptime-kuma

MCP server for [Uptime Kuma](https://github.com/louislam/uptime-kuma) v2 with full CRUD on monitors, notifications, tags, status pages, and maintenance.

## Installation

```bash
uvx mcp-uptime-kuma
```

Or install from PyPI:

```bash
pip install mcp-uptime-kuma
```

## Configuration

Set the following environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `UPTIME_KUMA_URL` | Yes | Uptime Kuma instance URL (e.g., `http://localhost:3001`) |
| `UPTIME_KUMA_USERNAME` | Yes* | Admin username |
| `UPTIME_KUMA_PASSWORD` | Yes* | Admin password |
| `UPTIME_KUMA_TOKEN` | No | JWT token (alternative to username/password) |
| `UPTIME_KUMA_MFA_TOKEN` | No | 2FA code (only for initial login with 2FA enabled) |

\* Required unless `UPTIME_KUMA_TOKEN` is provided.

## Claude Code Integration

```bash
claude mcp add-json uptime-kuma '{
  "command": "uvx",
  "args": ["mcp-uptime-kuma"],
  "env": {
    "UPTIME_KUMA_URL": "http://localhost:3001",
    "UPTIME_KUMA_USERNAME": "admin",
    "UPTIME_KUMA_PASSWORD": "your-password"
  }
}'
```

## Tools

### Monitors (7 tools)
- `list_monitors` — List all monitors with optional filters
- `get_monitor` — Get detailed monitor configuration and status
- `create_monitor` — Create a new monitor (http, tcp, ping, dns, docker, push, etc.)
- `edit_monitor` — Update monitor configuration
- `delete_monitor` — Delete a monitor
- `pause_monitor` — Pause a monitor
- `resume_monitor` — Resume a paused monitor

### Notifications (6 tools)
- `list_notifications` — List all notification providers
- `get_notification` — Get notification provider details
- `create_notification` — Create a notification provider (telegram, slack, discord, email, webhook, etc.)
- `edit_notification` — Update a notification provider
- `delete_notification` — Delete a notification provider
- `test_notification` — Test a notification configuration

### Tags (7 tools)
- `list_tags` — List all tags
- `get_tag` — Get tag details
- `create_tag` — Create a tag
- `edit_tag` — Update a tag
- `delete_tag` — Delete a tag
- `add_monitor_tag` — Add a tag to a monitor
- `remove_monitor_tag` — Remove a tag from a monitor

### Status Pages (5 tools)
- `list_status_pages` — List all status pages
- `get_status_page` — Get status page details
- `create_status_page` — Create a status page
- `save_status_page` — Update a status page
- `delete_status_page` — Delete a status page

### Maintenance (7 tools)
- `list_maintenances` — List all maintenance windows
- `get_maintenance` — Get maintenance details
- `create_maintenance` — Create a maintenance window
- `edit_maintenance` — Update a maintenance window
- `delete_maintenance` — Delete a maintenance window
- `pause_maintenance` — Pause a maintenance window
- `resume_maintenance` — Resume a maintenance window

### System (6 tools)
- `get_server_info` — Get Uptime Kuma server version and settings
- `get_monitor_beats` — Get heartbeat history for a monitor
- `get_monitor_avg_ping` — Get average ping for a monitor
- `get_monitor_uptime` — Get uptime percentage for a monitor
- `get_monitor_cert_info` — Get TLS/SSL certificate info
- `get_database_size` — Get database size

## License

MIT
