#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Building SAM application..."
sam build

echo "Starting local API on http://localhost:3000..."
sam local start-api \
  --env-vars env.json \
  --docker-network backend_default
