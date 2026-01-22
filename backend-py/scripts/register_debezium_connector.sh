#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

CONNECT_URL=${CONNECT_URL:-http://localhost:8083}
CONFIG_FILE=${CONFIG_FILE:-./scripts/debezium-connector.json}

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Connector config not found: $CONFIG_FILE"
  exit 1
fi

echo "Registering Debezium connector at $CONNECT_URL"

curl -s -X POST "$CONNECT_URL/connectors" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  --data "$(envsubst < "$CONFIG_FILE")" | cat

echo ""
