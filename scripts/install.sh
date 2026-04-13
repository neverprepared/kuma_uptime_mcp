#!/bin/sh
# Copy docker-compose files to ~/.config/neverprepared-mcp-servers/
# Only copies if the target file does not already exist (preserves user modifications)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="${HOME}/.config/neverprepared-mcp-servers"

# Uptime Kuma
KUMA_DIR="${CONFIG_DIR}/uptime-kuma"
KUMA_SOURCE="${SCRIPT_DIR}/../docker/uptime-kuma/docker-compose.yml"
KUMA_TARGET="${KUMA_DIR}/docker-compose.yml"

if [ -f "$KUMA_SOURCE" ]; then
  mkdir -p "$KUMA_DIR"
  if [ ! -f "$KUMA_TARGET" ]; then
    cp "$KUMA_SOURCE" "$KUMA_TARGET"
    echo "mcp-uptime-kuma: Installed Uptime Kuma docker-compose.yml to ${KUMA_TARGET}"
    echo "mcp-uptime-kuma: Run 'docker compose -f ${KUMA_TARGET} up -d' to start Uptime Kuma"
  fi
fi
