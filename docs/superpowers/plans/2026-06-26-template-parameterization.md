# Template Parameterization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate hardcoded resource names so multiple sites can be deployed to the same AWS account without collisions, and add a README documenting first-time setup.

**Architecture:** Derive a short slug from the subdomain portion of the existing `SITE_DOMAIN` env var (e.g. `recipes.melvinit.com` → `recipes`). Use that slug inline at each callsite to name the CDK stack (`${slug}-site`), DynamoDB table (`${slug}-table`), and SAM stack (`${slug}-backend`). Rename the CDK class from `TributeSiteStack` to `SiteStack` and strip "Tribute" from all description strings.

**Tech Stack:** AWS CDK 2 (TypeScript), AWS SAM (TOML config), GitHub Actions (YAML), Bash

## Global Constraints

- Branch: `template`
- No new env vars — slug is always derived from the existing `SITE_DOMAIN`
- DynamoDB `removalPolicy: cdk.RemovalPolicy.RETAIN` must be preserved in all edits
- S3 bucket names are unchanged (already domain-derived)
- No changes to frontend, backend API, or test code

---

### Task 1: Rename and parameterize CDK infra

**Files:**
- Modify: `infra/lib/site-stack.ts`
- Modify: `infra/bin/infra.ts`

- [ ] **Step 1: Rewrite `infra/lib/site-stack.ts`**

  Replace the entire file with the following (changes: class/interface renamed, slug derived, table name derived, description/comment strings updated):

  ```typescript
  import * as cdk from 'aws-cdk-lib';
  import { Construct } from 'constructs';
  import * as s3 from 'aws-cdk-lib/aws-s3';
  import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
  import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
  import * as acm from 'aws-cdk-lib/aws-certificatemanager';
  import * as route53 from 'aws-cdk-lib/aws-route53';
  import * as targets from 'aws-cdk-lib/aws-route53-targets';
  import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

  export interface SiteStackProps extends cdk.StackProps {
    readonly domainName: string;
    readonly parentDomainName: string;
    readonly apiGatewayDomain?: string;
  }

  export class SiteStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: SiteStackProps) {
      super(scope, id, {
        ...props,
        env: { ...props.env, region: 'us-east-1' },
        description: `Site infrastructure for ${props.domainName}`,
      });

      const { domainName, parentDomainName, apiGatewayDomain } = props;
      const slug = domainName.split('.')[0];

      const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
        domainName: parentDomainName,
      });

      const table = new dynamodb.Table(this, 'SiteTable', {
        tableName: `${slug}-table`,
        partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
        sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
        timeToLiveAttribute: 'expiresAt',
      });

      const siteBucket = new s3.Bucket(this, 'SiteBucket', {
        bucketName: `${domainName}-site-${this.account}-${this.region}`,
        publicReadAccess: false,
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
        objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
        encryption: s3.BucketEncryption.S3_MANAGED,
      });

      const mediaBucket = new s3.Bucket(this, 'MediaBucket', {
        bucketName: `${domainName}-media-${this.account}-${this.region}`,
        publicReadAccess: false,
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
        objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
        encryption: s3.BucketEncryption.S3_MANAGED,
        cors: [
          {
            allowedMethods: [s3.HttpMethods.PUT],
            allowedOrigins: [`https://${domainName}`],
            allowedHeaders: ['*'],
          },
        ],
      });

      const certificate = new acm.Certificate(this, 'SiteCertificate', {
        domainName: domainName,
        validation: acm.CertificateValidation.fromDns(hostedZone),
      });

      const additionalBehaviors: Record<string, cloudfront.BehaviorOptions> = {
        '/media/*': {
          origin: origins.S3BucketOrigin.withOriginAccessControl(mediaBucket),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
          compress: true,
          cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        },
        '/message-photos/*': {
          origin: origins.S3BucketOrigin.withOriginAccessControl(mediaBucket),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
          compress: true,
          cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        },
      };

      if (apiGatewayDomain) {
        additionalBehaviors['/api/*'] = {
          origin: new origins.HttpOrigin(apiGatewayDomain, {
            originPath: '/Prod',
          }),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        };
      }

      const distribution = new cloudfront.Distribution(this, 'SiteDistribution', {
        comment: `Site: ${domainName}`,
        defaultBehavior: {
          origin: origins.S3BucketOrigin.withOriginAccessControl(siteBucket),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
          compress: true,
          cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        },
        additionalBehaviors,
        priceClass: cloudfront.PriceClass.PRICE_CLASS_100,
        certificate: certificate,
        domainNames: [domainName],
        defaultRootObject: 'index.html',
        errorResponses: [
          {
            httpStatus: 403,
            responseHttpStatus: 200,
            responsePagePath: '/index.html',
            ttl: cdk.Duration.minutes(0),
          },
          {
            httpStatus: 404,
            responseHttpStatus: 200,
            responsePagePath: '/index.html',
            ttl: cdk.Duration.minutes(0),
          },
        ],
        minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
      });

      new route53.ARecord(this, 'SubdomainAliasRecord', {
        zone: hostedZone,
        recordName: domainName,
        target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
      });

      new cdk.CfnOutput(this, 'SiteBucketName', { value: siteBucket.bucketName });
      new cdk.CfnOutput(this, 'MediaBucketName', { value: mediaBucket.bucketName });
      new cdk.CfnOutput(this, 'DistributionId', { value: distribution.distributionId });
      new cdk.CfnOutput(this, 'DistributionDomainName', { value: distribution.distributionDomainName });
      new cdk.CfnOutput(this, 'TableName', { value: table.tableName });
      new cdk.CfnOutput(this, 'WebsiteURL', { value: `https://${domainName}` });
    }
  }
  ```

- [ ] **Step 2: Rewrite `infra/bin/infra.ts`**

  Replace the entire file (changes: import updated, slug derived, stack ID uses slug, Project tag uses slug):

  ```typescript
  #!/usr/bin/env node
  import 'source-map-support/register';
  import * as cdk from 'aws-cdk-lib';
  import { SiteStack } from '../lib/site-stack';

  const app = new cdk.App();

  const account = process.env.CDK_DEFAULT_ACCOUNT;
  const region = 'us-east-1';

  if (!account) {
    throw new Error('Set CDK_DEFAULT_ACCOUNT environment variable.');
  }

  const siteDomain = process.env.SITE_DOMAIN;
  const parentDomain = process.env.PARENT_DOMAIN;

  if (!siteDomain || !parentDomain) {
    throw new Error('Set SITE_DOMAIN and PARENT_DOMAIN environment variables.');
  }

  const slug = siteDomain.split('.')[0];
  const apiGatewayDomain = app.node.tryGetContext('apiGatewayDomain') as string | undefined;

  new SiteStack(app, `${slug}-site`, {
    env: { account, region },
    domainName: siteDomain,
    parentDomainName: parentDomain,
    apiGatewayDomain: apiGatewayDomain || undefined,
    tags: {
      Project: `${slug}-site`,
      Environment: 'Production',
      ManagedBy: 'CDK',
    },
  });

  app.synth();
  ```

- [ ] **Step 3: Verify TypeScript compiles**

  ```bash
  cd infra && npm run build
  ```

  Expected: exits 0, no errors, compiled JS appears in `infra/dist/` (or wherever `tsc` outputs).

- [ ] **Step 4: Commit**

  ```bash
  git add infra/lib/site-stack.ts infra/bin/infra.ts
  git commit -m "refactor: rename TributeSiteStack to SiteStack, derive resource names from domain slug"
  ```

---

### Task 2: Remove hardcoded SAM stack name and update bootstrap script

**Files:**
- Modify: `backend/samconfig.toml`
- Modify: `scripts/bootstrap.sh`

- [ ] **Step 1: Rewrite `backend/samconfig.toml`**

  Remove the `[default.global.parameters]` section (its only entry was the now-removed hardcoded `stack_name`). Replace the entire file with:

  ```toml
  version = 0.1

  [default.build.parameters]
  use_container = false

  [default.deploy.parameters]
  resolve_s3 = true
  region = "us-east-1"
  confirm_changeset = false
  fail_on_empty_changeset = false
  capabilities = "CAPABILITY_IAM"
  ```

- [ ] **Step 2: Update variable declarations in `scripts/bootstrap.sh`**

  Find lines 17–21 (the variable block at the top of the script), which currently read:

  ```bash
  REGION="us-east-1"
  CDK_STACK="TributeSiteStack"
  SAM_STACK="site-backend"
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"

  echo "=== Tribute Site — Bootstrap ==="
  ```

  Replace with:

  ```bash
  REGION="us-east-1"
  SLUG="${SITE_DOMAIN%%.*}"
  CDK_STACK="${SLUG}-site"
  SAM_STACK="${SLUG}-backend"
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"

  echo "=== Site Bootstrap: ${SLUG} ==="
  ```

- [ ] **Step 3: Verify bootstrap.sh with shellcheck**

  ```bash
  shellcheck scripts/bootstrap.sh
  ```

  Expected: exits 0 with no errors. If `shellcheck` is not installed: `sudo apt-get install shellcheck` (Debian/Ubuntu) or `brew install shellcheck` (macOS).

- [ ] **Step 4: Commit**

  ```bash
  git add backend/samconfig.toml scripts/bootstrap.sh
  git commit -m "refactor: derive SAM and CDK stack names from SITE_DOMAIN slug in scripts"
  ```

---

### Task 3: Update GitHub Actions workflow

**Files:**
- Modify: `.github/workflows/deploy.yml`

- [ ] **Step 1: Rename the workflow**

  Change line 1 from:
  ```yaml
  name: Deploy Tribute Site
  ```
  to:
  ```yaml
  name: Deploy Site
  ```

- [ ] **Step 2: Add slug derivation step to the `deploy-infra` job**

  In the `deploy-infra` job, insert a new step immediately before the `CDK deploy` step (before line 106). The new step:

  ```yaml
      - name: Derive site slug
        id: slug
        run: echo "value=$(echo '${{ vars.SITE_DOMAIN }}' | cut -d. -f1)" >> "$GITHUB_OUTPUT"
  ```

- [ ] **Step 3: Replace hardcoded stack name in the CDK deploy step**

  The `run` block of the `CDK deploy` step (currently lines 112–115) reads:

  ```yaml
        run: |
          npx cdk deploy TributeSiteStack \
            --require-approval never \
            -c apiGatewayDomain=${{ secrets.API_GATEWAY_DOMAIN }}
  ```

  Replace with:

  ```yaml
        run: |
          npx cdk deploy ${{ steps.slug.outputs.value }}-site \
            --require-approval never \
            -c apiGatewayDomain=${{ secrets.API_GATEWAY_DOMAIN }}
  ```

- [ ] **Step 4: Replace hardcoded stack name in the Extract stack outputs step**

  The `aws cloudformation describe-stacks` call (currently line 121) reads:

  ```yaml
            --stack-name TributeSiteStack \
  ```

  Replace with:

  ```yaml
            --stack-name ${{ steps.slug.outputs.value }}-site \
  ```

- [ ] **Step 5: Add slug derivation step to the `deploy-backend` job**

  In the `deploy-backend` job, insert a new step immediately before the `SAM build` step (before line 154). The new step:

  ```yaml
      - name: Derive site slug
        id: slug
        run: echo "value=$(echo '${{ vars.SITE_DOMAIN }}' | cut -d. -f1)" >> "$GITHUB_OUTPUT"
  ```

- [ ] **Step 6: Replace hardcoded stack name in the SAM deploy step**

  The `--stack-name` line in the SAM deploy step (currently line 162) reads:

  ```yaml
            --stack-name site-backend \
  ```

  Replace with:

  ```yaml
            --stack-name ${{ steps.slug.outputs.value }}-backend \
  ```

- [ ] **Step 7: Validate YAML syntax**

  ```bash
  python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml')); print('YAML valid')"
  ```

  Expected: prints `YAML valid` and exits 0.

- [ ] **Step 8: Commit**

  ```bash
  git add .github/workflows/deploy.yml
  git commit -m "refactor: derive stack names from SITE_DOMAIN slug in GitHub Actions workflow"
  ```

---

### Task 4: Write README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md` at repo root with the following content**

  ````markdown
  # Site Template

  A reusable template for a password-protected event or content site. Features: access-code auth, media gallery, guest messages, and an admin panel. Deployed to AWS using CloudFront (static frontend + media CDN), API Gateway + Lambda (backend), and DynamoDB.

  Designed to be cloned and customized per-site. Replace the frontend pages for your content; the infrastructure and auth plumbing reuse unchanged.

  ## Prerequisites

  Install these before your first deploy:

  - [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
  - [AWS CDK CLI](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html): `npm install -g aws-cdk`
  - [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
  - Node.js 20+
  - Python 3.13
  - A Route 53 hosted zone for your parent domain (e.g. `melvinit.com`) already created in your AWS account

  ## 1. OIDC IAM Role Setup

  GitHub Actions authenticates to AWS via OIDC — no long-lived credentials needed. Do this once per AWS account.

  ### 1a. Create the OIDC identity provider

  In the [AWS IAM console](https://console.aws.amazon.com/iam/) → **Identity providers** → **Add provider**:

  - Provider type: **OpenID Connect**
  - Provider URL: `https://token.actions.githubusercontent.com`
  - Audience: `sts.amazonaws.com`

  Click **Add provider**.

  ### 1b. Create the IAM role

  In IAM → **Roles** → **Create role**:

  - Trusted entity type: **Web identity**
  - Identity provider: `token.actions.githubusercontent.com`
  - Audience: `sts.amazonaws.com`

  Click **Next**, then on the permissions page attach the **AdministratorAccess** managed policy (this can be tightened later once you know the exact services your stack uses).

  Click **Next**, name the role (e.g. `github-actions-deploy`), then **Create role**.

  ### 1c. Scope the trust policy to your repo

  Open the role you just created → **Trust relationships** → **Edit trust policy**. Replace the policy with:

  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
          "StringEquals": {
            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
          },
          "StringLike": {
            "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/YOUR_REPO_NAME:*"
          }
        }
      }
    ]
  }
  ```

  Replace `YOUR_ACCOUNT_ID`, `YOUR_GITHUB_ORG`, and `YOUR_REPO_NAME` with your values. Save.

  Copy the role ARN (looks like `arn:aws:iam::123456789012:role/github-actions-deploy`) — you'll need it in the next step.

  ## 2. GitHub Secrets & Variables

  In your GitHub repo → **Settings** → **Secrets and variables** → **Actions**, add:

  | Type | Name | Value |
  |------|------|-------|
  | Secret | `AWS_IAM_ROLE_ARN` | The role ARN from step 1c |
  | Secret | `API_GATEWAY_DOMAIN` | Set after first deploy (see step 3) |
  | Secret | `PARTY_CODE` | Access code for guests |
  | Secret | `ADMIN_CODE` | Access code for admin |
  | Secret | `JWT_SECRET` | Random hex string: `openssl rand -hex 32` |
  | Variable | `CDK_DEFAULT_ACCOUNT` | Your AWS account ID (12 digits) |
  | Variable | `SITE_DOMAIN` | Full subdomain, e.g. `recipes.melvinit.com` |
  | Variable | `PARENT_DOMAIN` | Parent hosted zone, e.g. `melvinit.com` |

  ## 3. First Deploy

  Run `scripts/bootstrap.sh` locally. It handles the chicken-and-egg between CDK and SAM (CloudFront needs the API Gateway domain, but API Gateway doesn't exist until SAM deploys).

  ```bash
  export CDK_DEFAULT_ACCOUNT=123456789012
  export SITE_DOMAIN=recipes.melvinit.com
  export PARENT_DOMAIN=melvinit.com
  export PARTY_CODE=your-guest-code
  export ADMIN_CODE=your-admin-code
  export JWT_SECRET=$(openssl rand -hex 32)

  ./scripts/bootstrap.sh
  ```

  The script prints an API domain at the end (e.g. `abc123.execute-api.us-east-1.amazonaws.com`). Copy it and set it as the `API_GATEWAY_DOMAIN` GitHub secret now.

  ## 4. Subsequent Deploys

  Push to `main`. GitHub Actions runs automatically:

  1. Builds and tests frontend + backend
  2. Deploys CDK infrastructure (idempotent)
  3. Deploys SAM backend
  4. Syncs frontend to S3 and invalidates CloudFront cache

  ## 5. Customizing

  - **Content:** Replace the pages in `frontend/src/routes/` with your own (keep `+page.svelte` for login, `+layout.svelte` for auth guard)
  - **Theme:** Edit `frontend/src/app.css` — colors and fonts are CSS variables at the top of the file
  - **Backend:** Add endpoints in `backend/api/app.py`; update `backend/template.yaml` to wire them to API Gateway
  ````

- [ ] **Step 2: Verify the file was created and looks complete**

  ```bash
  wc -l README.md
  ```

  Expected: 100+ lines.

- [ ] **Step 3: Commit**

  ```bash
  git add README.md
  git commit -m "docs: add README with setup guide and OIDC IAM role instructions"
  ```

---

## Final Verification

- [ ] **Check no "Tribute" references remain in infra code**

  ```bash
  grep -r "Tribute\|TributeSite\|tribute" infra/ scripts/ .github/ backend/samconfig.toml
  ```

  Expected: no output.

- [ ] **Check no hardcoded stack names remain**

  ```bash
  grep -r "SiteTable\|site-backend\|TributeSiteStack" infra/ scripts/ .github/ backend/samconfig.toml
  ```

  Expected: no output.
