# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Overview

`mcp-uptime-kuma` is a Model Context Protocol (MCP) **stdio** server that exposes
[Uptime Kuma](https://github.com/louislam/uptime-kuma) **v2.x** as tools. It provides
full CRUD over monitors, notifications, tags, status pages and maintenance windows,
plus read-only system/heartbeat queries.

Python package: `mcp-uptime-kuma` (src layout, hatchling).
npm wrapper package: `@neverprepared/mcp-uptime-kuma` (thin Node shim that shells out to `uv run`).

## Architecture

```
src/mcp_uptime_kuma/
  __main__.py     # `python -m mcp_uptime_kuma` -> server.run()
  server.py       # create_server(): builds FastMCP("mcp-uptime-kuma") + KumaClient,
                  # registers all six tool groups; run() serves over stdio
  client.py       # KumaClient: env-var config, lazy connect, login-by-token or
                  # username/password (+ optional MFA), disconnect/reconnect
  kuma_api.py     # KumaV2Api: hand-rolled Socket.IO client replacing uptime-kuma-api
                  # (which only supports Kuma v1.21-1.23)
  setup.py        # `mcp-uptime-kuma-setup` console script: installs the bundled
                  # docker-compose.yml to ~/.config/neverprepared-mcp-servers/uptime-kuma/
  tools/          # one module per domain, each exporting register_*_tools(server, client)
    monitors.py notifications.py tags.py status_pages.py maintenance.py system.py
bin/mcp-uptime-kuma.js   # npm bin -> spawns `uv run mcp-uptime-kuma`
docker/uptime-kuma/      # docker-compose.yml for a local Kuma on 127.0.0.1:3001
scripts/install.sh       # copies that compose file into ~/.config (non-destructive)
tests/                   # pytest, fully mocked API — no live Kuma required
```

### Why `kuma_api.py` exists (do not "simplify" it away)

Two Kuma v2 + python-engineio incompatibilities are worked around there:

1. Kuma v2 sends ~70+ packets in one polling response after login; engineio's default
   `max_decode_packets=16` drops the connection. The module sets `Payload.max_decode_packets = 128`.
2. Acks are unreliable/bundled, so `sio.call()` times out. `_call` uses `sio.emit` +
   `threading.Event` and returns `None` when no ack arrives (the operation still succeeds server-side).

## MCP surface

**38 tools, no resources and no prompts** are registered.

- **Monitors (7)** — `list_monitors` (optional `filter_type`, `filter_tag`), `get_monitor`,
  `create_monitor`, `edit_monitor`, `delete_monitor`, `pause_monitor`, `resume_monitor`
- **Notifications (6)** — `list_notifications`, `get_notification`, `create_notification`,
  `edit_notification`, `delete_notification`, `test_notification`
- **Tags (7)** — `list_tags`, `get_tag`, `create_tag`, `edit_tag`, `delete_tag`,
  `add_monitor_tag`, `remove_monitor_tag`
- **Status pages (5)** — `list_status_pages`, `get_status_page`, `create_status_page`,
  `save_status_page`, `delete_status_page`
- **Maintenance (7)** — `list_maintenances`, `get_maintenance`, `create_maintenance`,
  `edit_maintenance`, `delete_maintenance`, `pause_maintenance`, `resume_maintenance`
- **System (6)** — `get_server_info`, `get_monitor_beats`, `get_monitor_avg_ping`,
  `get_monitor_uptime`, `get_monitor_cert_info`, `get_database_size`

## Configuration

All config is environment variables, read in `client.py`:

| Variable | Required | Notes |
|---|---|---|
| `UPTIME_KUMA_URL` | yes | e.g. `http://localhost:3001` |
| `UPTIME_KUMA_USERNAME` | yes* | admin username |
| `UPTIME_KUMA_PASSWORD` | yes* | admin password |
| `UPTIME_KUMA_TOKEN` | no | JWT; alternative to username/password |
| `UPTIME_KUMA_MFA_TOKEN` | no | 2FA code for initial login |

\* Required unless `UPTIME_KUMA_TOKEN` is set. `_validate_config()` raises otherwise.

## Key commands

```bash
uv sync                                  # install deps (also `npm run build`)
uv run mcp-uptime-kuma                   # run the server over stdio (also `npm start`)
uv run python -m mcp_uptime_kuma         # same, via module entry point
uv run mcp-uptime-kuma-setup [--start]   # install/start the bundled Uptime Kuma compose stack

uv run --with pytest --with pytest-asyncio pytest -q   # run the test suite (120 tests)

docker compose -f docker/uptime-kuma/docker-compose.yml up -d   # local Kuma on :3001
```

There is **no lint configuration** in the repo (no ruff/flake8/black config, no Makefile).
There is **no test-runner dependency declared** — `pyproject.toml` sets
`asyncio_mode = "auto"` but neither `pytest` nor `pytest-asyncio` is a declared dependency,
so tests must be run with `--with` (as above) or an externally installed pytest.

## CI

`.github/workflows/publish.yml` is the only workflow. It triggers on `v*` **tags** only
(not on pull requests), runs `npm run build`, then `npm publish --access public` using
`secrets.NPM_TOKEN`. **Pull requests get no CI checks** — verify locally before merging.

## Conventions

- Every tool is an `async def` inside a `register_*_tools(server, client)` factory,
  decorated with `@server.tool()`; the docstring is the tool description and the
  `Args:` block documents parameters (FastMCP surfaces both).
- Tools **return a JSON string** (`json.dumps(...)`), never a dict or object.
- Errors are caught per-tool and returned as `json.dumps({"error": str(e)})` — tools
  should not raise out to the MCP runtime.
- List tools return a summary shape plus a `count` field; get tools return the full record.
- The Kuma connection is lazy: `client.api` connects on first use. Never connect at import time.
- `mcp` is pinned `>=1.0.0,<2` — `mcp.server.fastmcp` was removed in mcp 2.0. Do not unpin.
- Tests mock `KumaClient`/the API entirely (`tests/conftest.py`); no live Uptime Kuma
  instance is required, and none should be needed by new tests.
