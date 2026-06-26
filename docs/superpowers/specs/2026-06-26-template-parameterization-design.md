# Template Parameterization Design

**Date:** 2026-06-26
**Status:** Approved
**Goal:** Make the repo a clean, reusable template for multiple sites (e.g. recipe book, tribute site) deployable to the same AWS account under `*.melvinit.com` without resource name collisions.

---

## Problem

Three resource names are hardcoded, causing collisions if two sites are deployed to the same AWS account:

| Resource | Hardcoded value |
|---|---|
| CDK / CloudFormation stack | `TributeSiteStack` |
| DynamoDB table | `SiteTable` |
| SAM / Lambda stack | `site-backend` |

Additionally, "Tribute" branding is baked into class names, descriptions, and comments, and there is no README documenting the OIDC IAM role prerequisite.

---

## Approach

**Option A — Inline derivation, flat rename.** No new env vars. Derive a short slug from the already-required `SITE_DOMAIN` env var by taking everything before the first dot. Use that slug to construct all resource names inline at each callsite.

---

## Slug Derivation

Source: `SITE_DOMAIN` (already required, e.g. `recipes.melvinit.com`)

| Context | Expression | Example |
|---|---|---|
| TypeScript | `siteDomain.split('.')[0]` | `recipes` |
| Bash | `${SITE_DOMAIN%%.*}` | `dad-birthday` |
| GitHub Actions | `echo "$SITE_DOMAIN" \| cut -d. -f1` | same |

---

## Naming Conventions

| Resource | Old (hardcoded) | New (derived) |
|---|---|---|
| CDK / CloudFormation stack | `TributeSiteStack` | `${slug}-site` |
| DynamoDB table | `SiteTable` | `${slug}-table` |
| SAM / Lambda stack | `site-backend` | `${slug}-backend` |

S3 bucket names are unchanged — they are already derived from `domainName`.

---

## File Changes

### `infra/lib/site-stack.ts`
- Rename class `TributeSiteStack` → `SiteStack`
- Rename interface `TributeSiteStackProps` → `SiteStackProps`
- Derive `slug` inside constructor: `const slug = domainName.split('.')[0]`
- Change `tableName: 'SiteTable'` → `tableName: \`${slug}-table\``
- Update stack description: `"Tribute site infrastructure for..."` → `"Site infrastructure for..."`
- Update CloudFront comment: `"Tribute site for ${domainName}"` → `"Site: ${domainName}"`

### `infra/bin/infra.ts`
- Update import: `TributeSiteStack` → `SiteStack`
- Derive `slug = siteDomain.split('.')[0]`
- Pass `\`${slug}-site\`` as the CDK stack construct ID — in CDK, the construct ID of a `Stack` directly becomes the CloudFormation stack name
- Update `Project` tag: `'TributeSite'` → `` `${slug}-site` ``

### `backend/samconfig.toml`
- Remove `stack_name = "site-backend"` — stack name is always passed via `--stack-name` on the CLI

### `.github/workflows/deploy.yml`
- Rename workflow: `"Deploy Tribute Site"` → `"Deploy Site"`
- Add slug-derivation step in each deploy job, outputting `SITE_SLUG`
- Replace all hardcoded `TributeSiteStack` references with `${SITE_SLUG}-site`
- Replace all hardcoded `site-backend` references with `${SITE_SLUG}-backend`

### `scripts/bootstrap.sh`
- Derive `SLUG="${SITE_DOMAIN%%.*}"` near the top
- Replace `CDK_STACK="TributeSiteStack"` → `CDK_STACK="${SLUG}-site"`
- Replace `SAM_STACK="site-backend"` → `SAM_STACK="${SLUG}-backend"`
- Update display strings: `"Tribute Site"` → `"Site"`

### `README.md` (new)
Sections:
1. **What this is** — template description
2. **Prerequisites** — AWS CLI, CDK CLI, SAM CLI, Node 20+, Python 3.13, Route53 hosted zone
3. **OIDC IAM role setup** — step-by-step with trust policy JSON and minimum IAM permissions
4. **GitHub secrets & variables** — full table
5. **First deploy** — set env vars, run `scripts/bootstrap.sh`, set `API_GATEWAY_DOMAIN` secret from output
6. **Subsequent deploys** — push to `main`
7. **Customizing** — frontend pages, `src/app.css` for theme

---

## What Does Not Change

- All env var names (`SITE_DOMAIN`, `PARENT_DOMAIN`, `CDK_DEFAULT_ACCOUNT`, `PARTY_CODE`, `ADMIN_CODE`, `JWT_SECRET`)
- All GitHub secrets/vars names
- S3 bucket naming (already domain-derived)
- Backend API structure and endpoints
- Frontend structure and components
- The two-phase bootstrap sequence (CDK first without API Gateway, then SAM, then CDK again with API Gateway domain)

---

## Success Criteria

- Two different sites (e.g. `recipes.melvinit.com` and `dad-birthday.melvinit.com`) can be deployed to the same AWS account with no CloudFormation, DynamoDB, or SAM stack name collisions
- A developer cloning the repo sees no "Tribute" references in infrastructure code or CloudFormation outputs
- A developer following the README can complete a first deploy without needing to consult external documentation for the OIDC role setup
