# Dad's 80th Birthday Tribute Site

Monorepo for a Svelte tribute website with a Python Lambda backend and AWS CDK infrastructure.
Cloned from the dakamin portfolio structure.

## Project Structure

```
dad-birthday-frontend/   # Svelte 5 + SvelteKit 2 + Tailwind CSS 4 (TypeScript)
dad-birthday-backend/    # Python 3.13 AWS Lambda (SAM)
infra/                   # AWS CDK (TypeScript) — S3 + CloudFront + DynamoDB + Route53
```

## Design Document

See `docs/plans/2026-03-01-birthday-tribute-design.md` for the full approved design.

## Domain

- **Site**: dad.melvinit.com
- **Parent zone**: melvinit.com (existing Route53 hosted zone)

## Frontend (`dad-birthday-frontend/`)

- **Stack**: Svelte 5, SvelteKit 2, Vite 6, Tailwind CSS 4, TypeScript 5
- **Static adapter** with SPA fallback
- **Design**: Nostalgic & vintage — sepia tones, Playfair Display + Caveat fonts

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

### Testing

- **Unit**: Vitest — jsdom for client, node for server
- **E2E**: Playwright — builds and serves on port 4173

### Linting & Formatting

- ESLint 9 flat config with typescript-eslint + eslint-plugin-svelte
- Prettier with plugins: prettier-plugin-svelte, prettier-plugin-tailwindcss
- TypeScript strict mode enabled

## Backend (`dad-birthday-backend/`)

- **Stack**: Python 3.13, AWS SAM, Lambda + API Gateway
- **Database**: DynamoDB (single table design)
- **Endpoints**: See design doc for full API spec

### Key Endpoints

- `POST /verify` — validate party code or UUID token
- `GET /media` — list gallery media
- `GET /messages` — list birthday messages
- `POST /messages` — submit a birthday message
- `POST /admin/media/upload-url` — pre-signed S3 upload URL
- `POST /admin/tokens` — create expiring access token

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
- **Domain**: dad.melvinit.com

### Commands

```bash
npm run build       # Compile TypeScript
npx cdk synth       # Preview CloudFormation
npx cdk deploy      # Deploy to AWS
npm run test        # Jest tests
```

## CI/CD

GitHub Actions workflow:
- Triggers on push to `main`
- Builds frontend, deploys to S3, invalidates CloudFront
- Builds and deploys SAM backend
- Uses OIDC for AWS auth
