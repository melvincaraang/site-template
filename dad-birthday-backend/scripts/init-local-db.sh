#!/usr/bin/env bash
set -euo pipefail

ENDPOINT="http://localhost:8000"
TABLE_NAME="DadBirthdayTable"

# Check if table already exists
if aws dynamodb describe-table \
    --table-name "$TABLE_NAME" \
    --endpoint-url "$ENDPOINT" \
    --no-cli-pager >/dev/null 2>&1; then
  echo "Table '$TABLE_NAME' already exists — skipping."
  exit 0
fi

echo "Creating table '$TABLE_NAME'..."
aws dynamodb create-table \
  --table-name "$TABLE_NAME" \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url "$ENDPOINT" \
  --no-cli-pager

echo "Table '$TABLE_NAME' created."
