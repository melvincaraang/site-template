#!/usr/bin/env bash
set -euo pipefail

# One-time bootstrap for the Tribute Site.
#
# Prerequisites: AWS CLI, CDK CLI, SAM CLI, Node.js 20+, Python 3.13
#
# Usage:
#   export CDK_DEFAULT_ACCOUNT=123456789012
#   export SITE_DOMAIN=event.example.com
#   export PARENT_DOMAIN=example.com
#   export PARTY_CODE=your-party-code
#   export ADMIN_CODE=your-admin-code
#   export JWT_SECRET=$(openssl rand -hex 32)
#   ./scripts/bootstrap.sh

REGION="us-east-1"
SLUG="${SITE_DOMAIN%%.*}"
CDK_STACK="${SLUG}-site"
SAM_STACK="${SLUG}-backend"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Site Bootstrap: ${SLUG} ==="

for var in CDK_DEFAULT_ACCOUNT SITE_DOMAIN PARENT_DOMAIN PARTY_CODE ADMIN_CODE JWT_SECRET; do
  if [ -z "${!var:-}" ]; then
    echo "ERROR: $var is not set." >&2
    exit 1
  fi
done

echo "Account: $CDK_DEFAULT_ACCOUNT"
echo "Domain:  $SITE_DOMAIN"
echo "Region:  $REGION"
echo ""

# --- Step 1: CDK Bootstrap ---
echo "--- 1/7: CDK Bootstrap ---"
cd "$ROOT/infra"
npm ci
npx cdk bootstrap "aws://$CDK_DEFAULT_ACCOUNT/$REGION"

# --- Step 2: CDK Deploy (without API Gateway) ---
echo "--- 2/7: CDK Deploy (Phase 1) ---"
npx cdk deploy "$CDK_STACK" --require-approval never

# --- Step 3: Extract CDK Outputs ---
echo "--- 3/7: Reading CDK outputs ---"
get_output() {
  aws cloudformation describe-stacks \
    --stack-name "$CDK_STACK" --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" \
    --output text
}

TABLE_NAME=$(get_output TableName)
MEDIA_BUCKET=$(get_output MediaBucketName)
SITE_BUCKET=$(get_output SiteBucketName)
DIST_ID=$(get_output DistributionId)

echo "  TableName:      $TABLE_NAME"
echo "  MediaBucket:    $MEDIA_BUCKET"
echo "  SiteBucket:     $SITE_BUCKET"
echo "  DistributionId: $DIST_ID"

# --- Step 4: SAM Deploy ---
echo "--- 4/7: SAM Build & Deploy ---"
cd "$ROOT/backend"
sam build --use-container
sam deploy \
  --stack-name "$SAM_STACK" \
  --resolve-s3 \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --capabilities CAPABILITY_IAM \
  --region "$REGION" \
  --parameter-overrides \
    "TableName=$TABLE_NAME" \
    "MediaBucket=$MEDIA_BUCKET" \
    "PartyCode=$PARTY_CODE" \
    "AdminCode=$ADMIN_CODE" \
    "JwtSecret=$JWT_SECRET" \
    "CloudFrontDomain=$SITE_DOMAIN"

# --- Step 5: Extract API Gateway Domain ---
echo "--- 5/7: Reading API Gateway domain ---"
API_URL=$(aws cloudformation describe-stacks \
  --stack-name "$SAM_STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)
API_DOMAIN=$(echo "$API_URL" | sed -E 's|https://([^/]+)/.*|\1|')
echo "  API Domain: $API_DOMAIN"

# --- Step 6: CDK Deploy (with API Gateway) ---
echo "--- 6/7: CDK Deploy (Phase 2 — wiring API Gateway) ---"
cd "$ROOT/infra"
npx cdk deploy "$CDK_STACK" --require-approval never \
  -c "apiGatewayDomain=$API_DOMAIN"

# --- Step 7: Deploy Frontend ---
echo "--- 7/7: Build & Deploy Frontend ---"
cd "$ROOT/frontend"
npm ci
npm run build
aws s3 sync build/ "s3://$SITE_BUCKET" --delete
aws cloudfront create-invalidation \
  --distribution-id "$DIST_ID" --paths "/*"

echo ""
echo "=== Bootstrap complete! ==="
echo ""
echo "Site: https://$SITE_DOMAIN"
echo "API:  $API_URL"
echo ""
echo "Set these GitHub secrets/vars:"
echo "  Secrets:"
echo "    AWS_IAM_ROLE_ARN       = <your OIDC role ARN>"
echo "    API_GATEWAY_DOMAIN     = $API_DOMAIN"
echo "    PARTY_CODE             = $PARTY_CODE"
echo "    ADMIN_CODE             = $ADMIN_CODE"
echo "    JWT_SECRET             = $JWT_SECRET"
echo "  Variables:"
echo "    CDK_DEFAULT_ACCOUNT    = $CDK_DEFAULT_ACCOUNT"
echo "    SITE_DOMAIN            = $SITE_DOMAIN"
echo "    PARENT_DOMAIN          = $PARENT_DOMAIN"
