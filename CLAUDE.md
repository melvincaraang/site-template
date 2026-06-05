# Tribute Site Template

Monorepo for a Svelte tribute/event site with a Python Lambda backend and AWS CDK infrastructure.

## Project Structure

```
frontend/   # Svelte 5 + SvelteKit 2 + Tailwind CSS 4 (TypeScript)
backend/    # Python 3.13 AWS Lambda (SAM)
infra/      # AWS CDK (TypeScript) — S3 + CloudFront + DynamoDB + Route53
```

## Configuration

Before deploying, set these environment variables (see `scripts/bootstrap.sh`):

| Variable              | Description                              |
|-----------------------|------------------------------------------|
| `CDK_DEFAULT_ACCOUNT` | AWS account ID                           |
| `SITE_DOMAIN`         | Full subdomain, e.g. `event.example.com` |
| `PARENT_DOMAIN`       | Parent hosted zone, e.g. `example.com`  |
| `PARTY_CODE`          | Guest access code                        |
| `ADMIN_CODE`          | Admin access code                        |
| `JWT_SECRET`          | Random hex secret for JWTs              |

## Frontend (`frontend/`)

- **Stack**: Svelte 5, SvelteKit 2, Vite 6, Tailwind CSS 4, TypeScript 5
- **Static adapter** with SPA fallback
- **Theme**: Edit `src/app.css` to customize colors and fonts

### Commands

```bash
npm run dev          # Dev server (localhost:5173)
npm run build        # Production build
npm run check        # Type-check (svelte-check)
npm run lint         # Prettier + ESLint
npm run format       # Auto-format with Prettier
npm run test:unit    # Vitest
npm run test:e2e     # Playwright
npm run test         # Both unit + E2E
```

## Backend (`backend/`)

- **Stack**: Python 3.13, AWS SAM, Lambda + API Gateway
- **Database**: DynamoDB (single table design)

### Key Endpoints

- `POST /api/verify` — validate party code or UUID token
- `GET /api/session` — check current session
- `POST /api/logout` — end session
- `GET /api/media` — list gallery media
- `GET /api/messages` — list messages
- `POST /api/messages` — submit a message
- `POST /api/admin/media/upload-url` — pre-signed S3 upload URL
- `POST /api/admin/tokens` — create expiring access token

### Commands

```bash
sam build --use-container
sam local start-api          # Local API on port 3000
sam deploy --guided          # Deploy to AWS
python -m pytest tests/unit -v
```

## Infrastructure (`infra/`)

- **Stack**: AWS CDK 2 (TypeScript)
- **Resources**: S3 (site + media buckets), CloudFront (3 behaviors), DynamoDB, ACM, Route53

### Commands

```bash
npm run build       # Compile TypeScript
npx cdk synth       # Preview CloudFormation
npx cdk deploy      # Deploy to AWS
npm run test        # Jest tests
```

## CI/CD

GitHub Actions workflow (`deploy.yml`) triggers on push to `main`:
1. Builds frontend, runs lint + type-check + unit tests
2. Runs backend Python unit tests
3. Deploys CDK infrastructure
4. Deploys SAM backend
5. Syncs frontend build to S3, invalidates CloudFront

### Required GitHub Secrets / Vars

| Name                  | Type   | Description                          |
|-----------------------|--------|--------------------------------------|
| `AWS_IAM_ROLE_ARN`    | Secret | OIDC role ARN for AWS auth           |
| `API_GATEWAY_DOMAIN`  | Secret | API Gateway domain (after 1st deploy)|
| `PARTY_CODE`          | Secret | Guest access code                    |
| `ADMIN_CODE`          | Secret | Admin access code                    |
| `JWT_SECRET`          | Secret | JWT signing secret                   |
| `CDK_DEFAULT_ACCOUNT` | Var    | AWS account ID                       |
| `SITE_DOMAIN`         | Var    | Full domain, e.g. `event.example.com`|
| `PARENT_DOMAIN`       | Var    | Parent zone, e.g. `example.com`      |
