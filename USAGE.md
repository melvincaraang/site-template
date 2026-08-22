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

`frontend/` proxies `/api` → `localhost:3000` (see `vite.config.ts`).
Two options for the backend:

- **SAM local** (needs Docker): `backend/scripts/start-local-api.sh`.
- **No Docker**: write a small Node emulator of the endpoints you actually use
  and persist to a JSON file (see `scripts/dev-api.mjs` in the proxchurch repo
  for a working example). Zero AWS dependencies, instant startup.

```bash
cd frontend && npm install && npm run dev   # localhost:5173
```

Before pushing, run what CI runs: `npm run lint && npm run check && npm run build`
in `frontend/`, `python -m pytest tests/unit` in `backend/`.

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
