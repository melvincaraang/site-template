# Site Template

A reusable template for a password-protected event or content site. Features: access-code auth, media gallery, guest messages, and an admin panel. Deployed to AWS using CloudFront (static frontend + media CDN), API Gateway + Lambda (backend), and DynamoDB.

Designed to be cloned and customized per-site. Replace the frontend pages for your content; the infrastructure and auth plumbing reuse unchanged.

**New here? Start with [USAGE.md](USAGE.md)** — the start-to-finish guide (cloning, gated vs. public sites, customizing, local dev). This README covers the AWS/GitHub deploy setup.

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
          "token.actions.githubusercontent.com:sub": [
            "repo:YOUR_GITHUB_ORG/YOUR_REPO_NAME:*",
            "repo:YOUR_SUB_CLAIM_PREFIX:*"
          ]
        }
      }
    }
  ]
}
```

Replace `YOUR_ACCOUNT_ID`, `YOUR_GITHUB_ORG`, and `YOUR_REPO_NAME` with your values. Save.

> **Gotcha (newer repos): ID-suffixed OIDC subjects.** GitHub now issues OIDC
> tokens for newly created repos with immutable ID-suffixed subjects, e.g.
> `repo:owner@123456/name@987654:ref:refs/heads/main` — which does **not**
> match the classic `repo:owner/name:*` pattern, and fails with
> `Not authorized to perform sts:AssumeRoleWithWebIdentity`. Find your repo's
> actual prefix with:
>
> ```bash
> gh api repos/OWNER/REPO/actions/oidc/customization/sub -q .sub_claim_prefix
> ```
>
> and use it as `YOUR_SUB_CLAIM_PREFIX` above (keep both patterns; the ID form
> also survives repo renames). Older repos keep the classic prefix, in which
> case the second entry is redundant but harmless.
>
> Also note: a freshly created role can take a few minutes to propagate —
> if the very first workflow run fails to assume it, re-run before debugging.

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

### Alternative: first deploy entirely in GitHub Actions (no local tooling)

The CDK stack treats `apiGatewayDomain` as optional (it only skips the
CloudFront `/api/*` behavior), so the chicken-and-egg can be resolved with two
workflow passes instead of running bootstrap.sh locally:

1. Configure everything from step 2 **except** `API_GATEWAY_DOMAIN`, then push
   to `main`. The workflow deploys infra (no API route yet), the SAM backend
   (which creates the API Gateway), and the frontend.
2. Read the API domain from the backend stack output and set the secret:

   ```bash
   aws cloudformation describe-stacks --stack-name <slug>-backend --region us-east-1 \
     --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text
   gh secret set API_GATEWAY_DOMAIN --body '<host part of that URL>'
   ```

3. Re-run the workflow (`gh run rerun <id>` or push again). CloudFront picks up
   the `/api/*` route and the site is fully live.

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
