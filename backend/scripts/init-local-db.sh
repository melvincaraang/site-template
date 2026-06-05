#!/usr/bin/env bash
set -euo pipefail

ENDPOINT="http://localhost:8000"
TABLE_NAME="SiteTable"

# Override any SSO/profile config — DynamoDB Local doesn't check credentials
unset AWS_PROFILE 2>/dev/null || true
export AWS_ACCESS_KEY_ID="local"
export AWS_SECRET_ACCESS_KEY="local"
export AWS_DEFAULT_REGION="us-east-1"

echo "Checking for existing table '$TABLE_NAME'..."

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
