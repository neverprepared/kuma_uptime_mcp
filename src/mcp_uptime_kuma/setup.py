"""Setup script: installs the Uptime Kuma docker-compose.yml to
~/.config/neverprepared-mcp-servers/uptime-kuma/ and optionally starts the container.

Run once after installation:
  mcp-uptime-kuma-setup
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


COMPOSE_SOURCE = Path(__file__).parent.parent.parent.parent / "docker" / "uptime-kuma" / "docker-compose.yml"
CONFIG_DIR = Path.home() / ".config" / "neverprepared-mcp-servers" / "uptime-kuma"
COMPOSE_TARGET = CONFIG_DIR / "docker-compose.yml"


def main() -> None:
    # Locate compose source — works from the repo or a dist install
    source = COMPOSE_SOURCE
    if not source.exists():
        # When installed via pip/uvx the docker dir isn't packaged; skip silently
        print("mcp-uptime-kuma-setup: docker-compose source not found, skipping install")
        return

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not COMPOSE_TARGET.exists():
        shutil.copy2(source, COMPOSE_TARGET)
        print(f"mcp-uptime-kuma: Installed docker-compose.yml to {COMPOSE_TARGET}")
    else:
        print(f"mcp-uptime-kuma: docker-compose.yml already present at {COMPOSE_TARGET}")

    # Offer to start the container
    if len(sys.argv) > 1 and sys.argv[1] == "--start":
        _start()
    else:
        print(f"mcp-uptime-kuma: Start with: docker compose -f {COMPOSE_TARGET} up -d")


def _start() -> None:
    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_TARGET), "up", "-d"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("mcp-uptime-kuma: Uptime Kuma started")
    else:
        print(f"mcp-uptime-kuma: Failed to start: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
