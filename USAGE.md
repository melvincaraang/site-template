# How to Use This Template

Start-to-finish guide for turning this template into a new deployed site.
(Deploy mechanics — OIDC role, secrets, bootstrap — live in [README.md](README.md);
this is the workflow around them.)

## What you get

- `frontend/` — Svelte 5 + SvelteKit 2 + Tailwind CSS 4, static adapter with SPA
  fallback. Ships with access-code login, media gallery, guest messages, admin panel.
- `backend/` — Python 3.13 Lambda behind API Gateway (SAM), DynamoDB single-table.
  Auth (guest code / admin code / expiring share links), media, messages.
- `infra/` — CDK stack: S3 (site + media), CloudFront, DynamoDB, ACM cert,
  Route 53 record. Stack names derive from `SITE_DOMAIN`'s first label
  (`recipes.example.com` → `recipes-site`, `recipes-backend`, `recipes-table`).
- `.github/workflows/deploy.yml` — push to `main`: lint + type-check + tests,
  then CDK deploy → SAM deploy → S3 sync + CloudFront invalidation.

## 1. Start a new project

```bash
cp -r site-template/ my-site/
cd my-site
rm -rf .git
git init -b main
```

Create the GitHub repo (`gh repo create my-site --private --source . --push`)
— but read README step 1 first if this is a brand-new repo: newer repos get
ID-suffixed OIDC subjects that the classic trust-policy pattern doesn't match.

## 2. Decide: gated or public?

The template ships **fully gated** — `+layout.svelte` redirects everyone
without a session to the login page. That's right for private event/tribute
sites. For a public site (e.g. a church or business):

- Remove the auth guard from `frontend/src/routes/+layout.svelte` and make the
  landing page real content instead of a login form.
- Keep admin-only auth for an `/admin` route (the `verify` endpoint's
  `admin: true` path and JWT plumbing work unchanged).
- `PARTY_CODE` becomes vestigial but is still required by the stack — set any value.

## 3. Customize

- **Content/pages**: replace `frontend/src/routes/*`. Keep the route/page
  structure conventions (`+page.svelte`, `+layout.svelte`).
- **Theme**: `frontend/src/app.css` — colors and fonts are CSS variables at the
  top. Self-host fonts in `frontend/static/fonts/` rather than hitting Google
  Fonts at runtime.
- **Backend endpoints**: add handlers in `backend/api/app.py`, register the
  route in the `routes` dict *and* in `backend/template.yaml` (API Gateway
  events are enumerated explicitly — a handler without a template.yaml event
  is unreachable in prod). Add unit tests in `backend/tests/unit/`.
- **Content management**: if the site needs admin-editable copy, a pattern that
  works well (see the proxchurch repo): bake default content into a frontend
  module, store admin overrides in DynamoDB under a `CONTENT` partition, merge
  overrides over defaults at load. The site then renders even if the API is
  down, and "restore original" is a delete.

## 4. Local development

No Docker or AWS needed. The backend dev server runs the real Lambda handler
with an in-memory DynamoDB (moto):

```bash
cd backend
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -r api/requirements.txt -r tests/requirements.txt
.venv/bin/python scripts/dev_server.py      # :3000 — codes "party" (guest) and "admin"

cd frontend && npm install && npm run dev   # :5173, proxies /api → :3000
```

Before pushing, run what CI runs:

```bash
cd backend  && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy && .venv/bin/python -m pytest --cov
cd frontend && npm run lint && npm run check && npm run test:unit -- --run && npm run build && npm run check:size
cd frontend && npm run test:e2e             # Playwright + axe; starts both servers itself
```

## 4b. CI gate chain

`.github/workflows/ci.yml` runs on every pull request and push to `main`, and is called by
`deploy.yml` so nothing deploys that did not pass the same checks:

| Job | What it checks | Blocking |
|-----|----------------|----------|
| frontend | prettier, eslint, svelte-check, vitest, build, gzipped bundle budget (`scripts/check-bundle-size.mjs`) | yes |
| backend | ruff lint+format, mypy, pytest with a coverage floor (`pyproject.toml`), Lambda import with prod requirements only, `sam validate --lint` | yes |
| e2e | Playwright against the local stack incl. an axe accessibility pass (serious/critical fail) | yes |
| infra | tsc, jest security assertions + cdk-nag AwsSolutions (suppressions carry reasons), `cdk synth` without AWS lookups | yes |
| security | gitleaks secret scan (blocking); semgrep, pip-audit, npm audit (advisory) | partly |
| workflows | actionlint | yes |
| ci-status | aggregates the above; the one status check to require on `main` | yes |

`backend/tests/unit/test_consistency.py` fails when a route in `api/app.py` has no
`template.yaml` event, when `backend/requirements.txt` drifts from `api/requirements.txt`
(SAM installs from the root one), or when a handler reads an env var the template does not set.

`deploy.yml` (push to `main`) calls ci.yml, then deploys CDK → SAM → S3, and ends with a
smoke test of the live site. Deploy jobs are skipped until the `SITE_DOMAIN` repo variable
exists, so a fresh clone stays green. Actions are pinned to commit SHAs; Dependabot
(`.github/dependabot.yml`) updates npm, pip, and Actions weekly.

Recommended repo settings: a `main` ruleset that requires a pull request and the `ci-status`
check (free on public repos; private repos need GitHub Pro).

## 5. Deploy

Follow README steps 1–4 (OIDC role → GitHub secrets/vars → first deploy →
push-to-deploy). Two first-deploy paths:

- `scripts/bootstrap.sh` locally (needs AWS CLI + CDK + SAM; Docker optional —
  it falls back to a native build), **or**
- entirely in GitHub Actions via the two-pass method in the README
  ("Alternative: first deploy entirely in GitHub Actions").

## Known quirks

- **CloudFront masks API error codes.** The distribution remaps 403/404 to
  `/index.html` (SPA deep-link support), and error responses apply
  distribution-wide — so `/api/*` 403/404s reach the browser as `200` + HTML.
  Clients must treat unparseable JSON as failure (the template frontend does).
  Cleaner long-term fix: drop the error remaps and rewrite extensionless URIs
  to `/index.html` with a CloudFront Function on the default behavior only.
- **New-repo OIDC subjects** and **IAM role propagation delay** — see the
  trust-policy gotcha box in README step 1c.
- **`sam build --use-container` needs Docker**; the native fallback is fine
  while backend deps are pure Python and your Python matches the Lambda runtime.
- **SAM installs from `backend/requirements.txt`**, not `api/requirements.txt`. Keep them
  identical (a unit test enforces it).
