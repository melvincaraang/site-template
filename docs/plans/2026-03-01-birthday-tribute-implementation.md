# Dad's 80th Birthday Tribute Site — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a nostalgic, vintage-themed tribute website at dad.melvinit.com where guests can browse a curated photo/video gallery and leave birthday messages.

**Architecture:** Svelte 5 + SvelteKit 2 static SPA frontend, Python 3.13 Lambda backend with DynamoDB (single-table design), AWS CDK infrastructure with CloudFront serving the site bucket, media bucket, and API Gateway under one domain. Auth via party code or expiring UUID tokens, using signed JWT cookies.

**Tech Stack:** Svelte 5, SvelteKit 2, Tailwind CSS 4, TypeScript 5, Python 3.13, AWS SAM, DynamoDB, AWS CDK 2, S3, CloudFront, Route53

**Source codebase to reference:** `~/Development/dakamin` (clone structure from here)
**New project directory:** `~/Development/dad-birthday`

---

## Task 1: Scaffold the Frontend Project

Copy the dakamin-frontend structure and strip it down to a clean starting point.

**Files:**
- Create: `dad-birthday-frontend/package.json`
- Create: `dad-birthday-frontend/svelte.config.js`
- Create: `dad-birthday-frontend/vite.config.ts`
- Create: `dad-birthday-frontend/tsconfig.json`
- Create: `dad-birthday-frontend/eslint.config.js`
- Create: `dad-birthday-frontend/.prettierrc`
- Create: `dad-birthday-frontend/.prettierignore`
- Create: `dad-birthday-frontend/.gitignore`
- Create: `dad-birthday-frontend/playwright.config.ts`
- Create: `dad-birthday-frontend/vitest-setup-client.ts`
- Create: `dad-birthday-frontend/src/app.html`
- Create: `dad-birthday-frontend/src/app.d.ts`
- Create: `dad-birthday-frontend/src/routes/+layout.ts`

**Step 1: Copy config files from dakamin**

Copy these files verbatim from `~/Development/dakamin/dakamin-frontend/`:
- `svelte.config.js` (no changes needed — same static adapter + SPA fallback)
- `vite.config.ts` (no changes needed)
- `tsconfig.json` (no changes needed)
- `eslint.config.js` (no changes needed)
- `.prettierrc` (no changes needed)
- `playwright.config.ts` (no changes needed)

**Step 2: Create package.json**

Copy from dakamin and change the name:

```json
{
	"name": "dad-birthday-frontend",
	"private": true,
	"version": "0.0.1",
	"type": "module",
	"scripts": {
		"dev": "vite dev",
		"build": "vite build",
		"preview": "vite preview",
		"prepare": "svelte-kit sync || echo ''",
		"check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
		"check:watch": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --watch",
		"format": "prettier --write .",
		"lint": "prettier --check . && eslint .",
		"test:unit": "vitest",
		"test": "npm run test:unit -- --run && npm run test:e2e",
		"test:e2e": "playwright test"
	},
	"devDependencies": {
		"@eslint/compat": "^1.2.5",
		"@eslint/js": "^9.18.0",
		"@playwright/test": "^1.49.1",
		"@sveltejs/adapter-static": "^3.0.8",
		"@sveltejs/kit": "^2.16.0",
		"@sveltejs/vite-plugin-svelte": "^5.0.0",
		"@tailwindcss/forms": "^0.5.9",
		"@tailwindcss/typography": "^0.5.15",
		"@tailwindcss/vite": "^4.0.0",
		"@testing-library/jest-dom": "^6.6.3",
		"@testing-library/svelte": "^5.2.4",
		"eslint": "^9.18.0",
		"eslint-config-prettier": "^10.0.1",
		"eslint-plugin-svelte": "^3.0.0",
		"globals": "^16.0.0",
		"jsdom": "^26.0.0",
		"prettier": "^3.4.2",
		"prettier-plugin-svelte": "^3.3.3",
		"prettier-plugin-tailwindcss": "^0.6.11",
		"svelte": "^5.0.0",
		"svelte-check": "^4.0.0",
		"tailwindcss": "^4.0.0",
		"typescript": "^5.0.0",
		"typescript-eslint": "^8.20.0",
		"vite": "^6.2.6",
		"vitest": "^3.0.0"
	},
	"dependencies": {
		"@iconify/svelte": "^4.2.0"
	}
}
```

**Step 3: Create app.html (stripped of reCAPTCHA)**

```html
<!doctype html>
<html lang="en">
	<head>
		<meta charset="utf-8" />
		<link rel="icon" href="%sveltekit.assets%/favicon.png" />
		<meta name="viewport" content="width=device-width, initial-scale=1" />
		%sveltekit.head%
	</head>
	<body data-sveltekit-preload-data="hover">
		<div style="display: contents">%sveltekit.body%</div>
	</body>
</html>
```

**Step 4: Create app.d.ts and +layout.ts**

`app.d.ts` — copy verbatim from dakamin.

`+layout.ts`:
```typescript
export const ssr = false;
export const csr = true;
export const prerender = false;
```

**Step 5: Create vitest-setup-client.ts**

```typescript
import '@testing-library/jest-dom/vitest';
```

Also create `.prettierignore`:
```
build
.svelte-kit
node_modules
```

**Step 6: Install dependencies and verify**

```bash
cd ~/Development/dad-birthday/dad-birthday-frontend
npm install
npm run check
```

Expected: Clean install, no type errors.

**Step 7: Commit**

```bash
git add dad-birthday-frontend/
git commit -m "feat: scaffold frontend from dakamin template"
```

---

## Task 2: Frontend Design System + Layout

Set up the vintage theme: fonts, colors, textures, global CSS, and the root layout.

**Files:**
- Create: `dad-birthday-frontend/src/app.css`
- Create: `dad-birthday-frontend/src/routes/+layout.svelte`
- Create: `dad-birthday-frontend/src/lib/stores/auth.svelte.ts`
- Create: `dad-birthday-frontend/src/routes/+page.svelte` (temporary gate placeholder)
- Create: `dad-birthday-frontend/static/images/` (paper texture background)

**Step 1: Create app.css with vintage theme**

```css
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Caveat:wght@400..700&display=swap');
@import 'tailwindcss';
@plugin '@tailwindcss/forms';
@plugin '@tailwindcss/typography';

@theme {
	--color-cream: #FFF8F0;
	--color-cream-dark: #F5EDE0;
	--color-brown: #3E2723;
	--color-brown-light: #5D4037;
	--color-gold: #C8A96E;
	--color-gold-light: #D4BC8B;
	--color-sepia: #704214;
	--font-display: 'Playfair Display', serif;
	--font-handwriting: 'Caveat', cursive;
}

body {
	font-family: var(--font-display);
	background-color: var(--color-cream);
	color: var(--color-brown);
}

h1, h2, h3 {
	font-family: var(--font-display);
}
```

**Step 2: Create auth store**

```typescript
// src/lib/stores/auth.svelte.ts
export type AuthRole = 'guest' | 'admin' | null;

export const authState = $state<{ role: AuthRole }>({
	role: null
});
```

**Step 3: Create root layout**

```svelte
<!-- src/routes/+layout.svelte -->
<script lang="ts">
	import '../app.css';

	let { children } = $props();
</script>

<div class="min-h-screen bg-cream">
	{@render children?.()}
</div>
```

**Step 4: Create placeholder home page**

```svelte
<!-- src/routes/+page.svelte -->
<h1 class="p-8 text-center text-4xl text-brown">Happy 80th Birthday!</h1>
```

**Step 5: Verify dev server runs**

```bash
cd ~/Development/dad-birthday/dad-birthday-frontend
npm run dev
```

Open `http://localhost:5173` — should see the heading with Playfair Display font on a cream background.

**Step 6: Commit**

```bash
git add dad-birthday-frontend/src/
git commit -m "feat: add vintage design system with fonts, colors, and layout"
```

---

## Task 3: Scaffold the Backend Project

Create the SAM project structure for the Python Lambda backend.

**Files:**
- Create: `dad-birthday-backend/template.yaml`
- Create: `dad-birthday-backend/samconfig.toml`
- Create: `dad-birthday-backend/api/__init__.py`
- Create: `dad-birthday-backend/api/app.py`
- Create: `dad-birthday-backend/api/requirements.txt`
- Create: `dad-birthday-backend/tests/__init__.py`
- Create: `dad-birthday-backend/tests/unit/__init__.py`
- Create: `dad-birthday-backend/tests/unit/conftest.py`
- Create: `dad-birthday-backend/tests/requirements.txt`

**Step 1: Create SAM template**

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Dad's 80th Birthday Tribute Site — API Backend

Parameters:
  TableName:
    Type: String
    Default: DadBirthdayTable
  MediaBucket:
    Type: String
  PartyCode:
    Type: String
  AdminCode:
    Type: String
  JwtSecret:
    Type: String
    NoEcho: true
  CloudFrontDomain:
    Type: String
    Default: dad.melvinit.com

Globals:
  Function:
    Timeout: 10
    Runtime: python3.13
    Architectures:
      - x86_64
    Environment:
      Variables:
        TABLE_NAME: !Ref TableName
        MEDIA_BUCKET: !Ref MediaBucket
        PARTY_CODE: !Ref PartyCode
        ADMIN_CODE: !Ref AdminCode
        JWT_SECRET: !Ref JwtSecret
        CLOUDFRONT_DOMAIN: !Ref CloudFrontDomain
    LoggingConfig:
      LogFormat: JSON

Resources:
  BirthdayApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: api/
      Handler: app.lambda_handler
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref TableName
        - S3CrudPolicy:
            BucketName: !Ref MediaBucket
      Events:
        Verify:
          Type: Api
          Properties:
            Path: /verify
            Method: post
        GetMedia:
          Type: Api
          Properties:
            Path: /media
            Method: get
        GetMessages:
          Type: Api
          Properties:
            Path: /messages
            Method: get
        PostMessage:
          Type: Api
          Properties:
            Path: /messages
            Method: post
        AdminGetTokens:
          Type: Api
          Properties:
            Path: /admin/tokens
            Method: get
        AdminPostToken:
          Type: Api
          Properties:
            Path: /admin/tokens
            Method: post
        AdminDeleteToken:
          Type: Api
          Properties:
            Path: /admin/tokens/{uuid}
            Method: delete
        AdminUploadUrl:
          Type: Api
          Properties:
            Path: /admin/media/upload-url
            Method: post
        AdminPostMedia:
          Type: Api
          Properties:
            Path: /admin/media
            Method: post
        AdminDeleteMedia:
          Type: Api
          Properties:
            Path: /admin/media/{id}
            Method: delete
        AdminPutMedia:
          Type: Api
          Properties:
            Path: /admin/media/{id}
            Method: put

Outputs:
  ApiUrl:
    Description: API Gateway endpoint URL
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
  BirthdayApiFunction:
    Description: Lambda Function ARN
    Value: !GetAtt BirthdayApiFunction.Arn
```

**Step 2: Create requirements.txt files**

`api/requirements.txt`:
```
boto3
PyJWT
ulid-py
```

`tests/requirements.txt`:
```
pytest
boto3
moto
PyJWT
ulid-py
```

**Step 3: Create the Lambda handler skeleton**

`api/__init__.py` — empty file.

`api/app.py`:

```python
import json
import os
from collections.abc import Mapping

# Route table: (method, path_pattern) -> handler_function
# Path patterns use {param} for path parameters


def lambda_handler(event: Mapping[str, object], context: object) -> dict[str, object]:
    """Main Lambda entry point — routes requests to handler functions."""
    method = event.get("httpMethod", "")
    path = event.get("path", "")

    # Route to appropriate handler
    routes = {
        ("POST", "/verify"): handle_verify,
        ("GET", "/media"): handle_get_media,
        ("GET", "/messages"): handle_get_messages,
        ("POST", "/messages"): handle_post_message,
        ("GET", "/admin/tokens"): handle_get_tokens,
        ("POST", "/admin/tokens"): handle_post_token,
        ("DELETE", "/admin/tokens"): handle_delete_token,
        ("POST", "/admin/media/upload-url"): handle_upload_url,
        ("POST", "/admin/media"): handle_post_media,
        ("DELETE", "/admin/media"): handle_delete_media,
        ("PUT", "/admin/media"): handle_put_media,
    }

    # Normalize path: strip trailing slash, handle path parameters
    normalized = path.rstrip("/")

    # Check for path-parameter routes
    if normalized.startswith("/admin/tokens/") and method == "DELETE":
        handler = handle_delete_token
    elif normalized.startswith("/admin/media/") and method == "DELETE":
        handler = handle_delete_media
    elif normalized.startswith("/admin/media/") and method == "PUT":
        handler = handle_put_media
    else:
        handler = routes.get((method, normalized))

    if not handler:
        return _response(404, {"error": "Not found"})

    try:
        return handler(event)
    except Exception as e:
        print(f"Error handling {method} {path}: {e}")
        return _response(500, {"error": "Internal server error"})


def handle_verify(event):
    return _response(501, {"error": "Not implemented"})


def handle_get_media(event):
    return _response(501, {"error": "Not implemented"})


def handle_get_messages(event):
    return _response(501, {"error": "Not implemented"})


def handle_post_message(event):
    return _response(501, {"error": "Not implemented"})


def handle_get_tokens(event):
    return _response(501, {"error": "Not implemented"})


def handle_post_token(event):
    return _response(501, {"error": "Not implemented"})


def handle_delete_token(event):
    return _response(501, {"error": "Not implemented"})


def handle_upload_url(event):
    return _response(501, {"error": "Not implemented"})


def handle_post_media(event):
    return _response(501, {"error": "Not implemented"})


def handle_delete_media(event):
    return _response(501, {"error": "Not implemented"})


def handle_put_media(event):
    return _response(501, {"error": "Not implemented"})


def _response(status_code: int, body: dict, headers: dict | None = None) -> dict:
    """Build an API Gateway response."""
    resp_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": f"https://{os.environ.get('CLOUDFRONT_DOMAIN', 'dad.melvinit.com')}",
        "Access-Control-Allow-Credentials": "true",
    }
    if headers:
        resp_headers.update(headers)
    return {
        "statusCode": status_code,
        "headers": resp_headers,
        "body": json.dumps(body),
    }
```

**Step 4: Create test fixtures**

`tests/__init__.py` and `tests/unit/__init__.py` — empty files.

`tests/unit/conftest.py`:

```python
import json
import os

import pytest

# Set env vars before importing app
os.environ["TABLE_NAME"] = "TestTable"
os.environ["MEDIA_BUCKET"] = "test-media-bucket"
os.environ["PARTY_CODE"] = "dad80"
os.environ["ADMIN_CODE"] = "admin-secret"
os.environ["JWT_SECRET"] = "test-jwt-secret-key"
os.environ["CLOUDFRONT_DOMAIN"] = "dad.melvinit.com"


@pytest.fixture()
def make_event():
    """Creates an API Gateway event."""
    def _make_event(method="GET", path="/", body=None, headers=None, path_parameters=None):
        return {
            "httpMethod": method,
            "path": path,
            "body": json.dumps(body) if isinstance(body, dict) else body,
            "headers": headers or {},
            "pathParameters": path_parameters,
            "requestContext": {
                "resourceId": "123456",
                "apiId": "1234567890",
                "httpMethod": method,
                "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
                "accountId": "123456789012",
                "identity": {"sourceIp": "127.0.0.1"},
                "stage": "prod",
            },
        }
    return _make_event
```

**Step 5: Write a routing smoke test**

Create `tests/unit/test_routing.py`:

```python
import json
from api import app


def test_unknown_route_returns_404(make_event):
    event = make_event("GET", "/unknown")
    result = app.lambda_handler(event, None)
    assert result["statusCode"] == 404


def test_verify_route_exists(make_event):
    event = make_event("POST", "/verify", body={"code": "test"})
    result = app.lambda_handler(event, None)
    # 501 means routed correctly but not implemented yet
    assert result["statusCode"] == 501
```

**Step 6: Run tests**

```bash
cd ~/Development/dad-birthday/dad-birthday-backend
pip install -r api/requirements.txt -r tests/requirements.txt
python -m pytest tests/unit -v
```

Expected: 2 tests pass.

**Step 7: Commit**

```bash
git add dad-birthday-backend/
git commit -m "feat: scaffold backend with SAM template and route skeleton"
```

---

## Task 4: Backend — Auth (verify endpoint + JWT)

Implement the `POST /verify` endpoint with party code, UUID token, and admin code validation. Returns a signed JWT cookie.

**Files:**
- Modify: `dad-birthday-backend/api/app.py`
- Create: `dad-birthday-backend/api/auth.py`
- Create: `dad-birthday-backend/tests/unit/test_verify.py`

**Step 1: Write failing tests for verify endpoint**

`tests/unit/test_verify.py`:

```python
import json
import jwt
import os
from unittest.mock import patch, MagicMock

from api import app


class TestVerifyWithPartyCode:
    def test_valid_party_code_returns_200_with_cookie(self, make_event):
        event = make_event("POST", "/verify", body={"code": "dad80"})
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        assert "Set-Cookie" in result["headers"]

        # Decode JWT from cookie
        cookie = result["headers"]["Set-Cookie"]
        token = cookie.split("=")[1].split(";")[0]
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
        assert payload["role"] == "guest"

    def test_invalid_party_code_returns_403(self, make_event):
        event = make_event("POST", "/verify", body={"code": "wrong"})
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 403

    def test_missing_code_returns_400(self, make_event):
        event = make_event("POST", "/verify", body={})
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 400


class TestVerifyWithAdminCode:
    def test_admin_code_returns_admin_role(self, make_event):
        event = make_event("POST", "/verify", body={"code": "admin-secret", "admin": True})
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        cookie = result["headers"]["Set-Cookie"]
        token = cookie.split("=")[1].split(";")[0]
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
        assert payload["role"] == "admin"


class TestVerifyWithUuidToken:
    @patch("api.auth.get_dynamodb_table")
    def test_valid_uuid_token_returns_200(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {"PK": "TOKEN", "SK": "TOKEN#abc-123", "expiresAt": 9999999999}
        }
        mock_get_table.return_value = mock_table

        event = make_event("POST", "/verify", body={"token": "abc-123"})
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 200

    @patch("api.auth.get_dynamodb_table")
    def test_invalid_uuid_token_returns_403(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_get_table.return_value = mock_table

        event = make_event("POST", "/verify", body={"token": "nonexistent"})
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 403
```

**Step 2: Run tests to verify they fail**

```bash
cd ~/Development/dad-birthday/dad-birthday-backend
python -m pytest tests/unit/test_verify.py -v
```

Expected: All tests FAIL.

**Step 3: Implement auth module**

`api/auth.py`:

```python
import json
import os
import time

import boto3
import jwt


def get_dynamodb_table():
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(os.environ["TABLE_NAME"])


def create_jwt(role: str) -> str:
    payload = {
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,  # 24 hours
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")


def verify_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def make_session_cookie(jwt_token: str) -> str:
    return f"session={jwt_token}; HttpOnly; Secure; Path=/; Max-Age=86400; SameSite=Strict"


def get_session_from_event(event: dict) -> dict | None:
    headers = event.get("headers") or {}
    cookie_header = headers.get("Cookie") or headers.get("cookie") or ""
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith("session="):
            token = part[len("session="):]
            return verify_jwt(token)
    return None


def require_auth(event: dict, role: str = "guest") -> dict | None:
    """Returns the JWT payload if authorized, None otherwise."""
    session = get_session_from_event(event)
    if not session:
        return None
    if role == "admin" and session.get("role") != "admin":
        return None
    return session
```

**Step 4: Implement handle_verify in app.py**

Replace the `handle_verify` stub in `api/app.py`:

```python
def handle_verify(event):
    body = _parse_body(event)
    if body is None:
        return _response(400, {"error": "Invalid JSON"})

    code = body.get("code")
    token = body.get("token")
    is_admin = body.get("admin", False)

    if not code and not token:
        return _response(400, {"error": "Provide 'code' or 'token'"})

    # Check admin code
    if code and is_admin:
        if code == os.environ["ADMIN_CODE"]:
            jwt_token = auth.create_jwt("admin")
            return _response(200, {"message": "Authenticated"}, {
                "Set-Cookie": auth.make_session_cookie(jwt_token)
            })
        return _response(403, {"error": "Invalid admin code"})

    # Check party code
    if code:
        if code == os.environ["PARTY_CODE"]:
            jwt_token = auth.create_jwt("guest")
            return _response(200, {"message": "Authenticated"}, {
                "Set-Cookie": auth.make_session_cookie(jwt_token)
            })
        return _response(403, {"error": "Invalid code"})

    # Check UUID token
    if token:
        table = auth.get_dynamodb_table()
        result = table.get_item(Key={"PK": "TOKEN", "SK": f"TOKEN#{token}"})
        item = result.get("Item")
        if not item:
            return _response(403, {"error": "Invalid token"})
        if item.get("expiresAt", 0) < int(time.time()):
            return _response(403, {"error": "Token expired"})
        jwt_token = auth.create_jwt("guest")
        return _response(200, {"message": "Authenticated"}, {
            "Set-Cookie": auth.make_session_cookie(jwt_token)
        })

    return _response(400, {"error": "Provide 'code' or 'token'"})
```

Also add these imports and helper to the top of `app.py`:

```python
import time
from api import auth


def _parse_body(event) -> dict | None:
    body = event.get("body", "{}")
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    return body if isinstance(body, dict) else None
```

**Step 5: Run tests**

```bash
python -m pytest tests/unit/test_verify.py -v
```

Expected: All tests PASS.

**Step 6: Commit**

```bash
git add dad-birthday-backend/
git commit -m "feat: implement auth with party code, UUID token, and JWT sessions"
```

---

## Task 5: Backend — Messages API

Implement GET and POST for birthday messages.

**Files:**
- Modify: `dad-birthday-backend/api/app.py`
- Create: `dad-birthday-backend/tests/unit/test_messages.py`

**Step 1: Write failing tests**

`tests/unit/test_messages.py`:

```python
import json
import os
import jwt
import time
from unittest.mock import patch, MagicMock

from api import app


def _auth_cookie(role="guest"):
    token = jwt.encode(
        {"role": role, "iat": int(time.time()), "exp": int(time.time()) + 3600},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    return f"session={token}"


class TestGetMessages:
    @patch("api.auth.get_dynamodb_table")
    def test_returns_messages(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_table.query.return_value = {
            "Items": [
                {"PK": "MSG", "SK": "MSG#01ABC", "author": "Alice", "text": "Happy birthday!", "createdAt": "2026-03-01T12:00:00Z"},
            ]
        }
        mock_get_table.return_value = mock_table

        event = make_event("GET", "/messages", headers={"Cookie": _auth_cookie()})
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        data = json.loads(result["body"])
        assert len(data["messages"]) == 1
        assert data["messages"][0]["author"] == "Alice"

    def test_unauthenticated_returns_401(self, make_event):
        event = make_event("GET", "/messages")
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 401


class TestPostMessage:
    @patch("api.auth.get_dynamodb_table")
    def test_creates_message(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        event = make_event(
            "POST", "/messages",
            body={"author": "Bob", "text": "Many happy returns!"},
            headers={"Cookie": _auth_cookie()},
        )
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 201
        mock_table.put_item.assert_called_once()
        item = mock_table.put_item.call_args[1]["Item"]
        assert item["author"] == "Bob"
        assert item["text"] == "Many happy returns!"
        assert item["PK"] == "MSG"
        assert item["SK"].startswith("MSG#")

    def test_missing_fields_returns_400(self, make_event):
        event = make_event(
            "POST", "/messages",
            body={"author": "Bob"},
            headers={"Cookie": _auth_cookie()},
        )
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 400
```

**Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/unit/test_messages.py -v
```

Expected: FAIL.

**Step 3: Implement message handlers in app.py**

Replace `handle_get_messages` and `handle_post_message` stubs:

```python
def handle_get_messages(event):
    session = auth.require_auth(event)
    if not session:
        return _response(401, {"error": "Unauthorized"})

    table = auth.get_dynamodb_table()
    result = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": "MSG"},
        ScanIndexForward=False,  # newest first
    )
    messages = [
        {"id": item["SK"].split("#")[1], "author": item["author"], "text": item["text"], "createdAt": item["createdAt"]}
        for item in result.get("Items", [])
    ]
    return _response(200, {"messages": messages})


def handle_post_message(event):
    session = auth.require_auth(event)
    if not session:
        return _response(401, {"error": "Unauthorized"})

    body = _parse_body(event)
    if not body or not body.get("author") or not body.get("text"):
        return _response(400, {"error": "Provide 'author' and 'text'"})

    import ulid as ulid_mod
    from datetime import datetime, timezone

    message_id = str(ulid_mod.new())
    now = datetime.now(timezone.utc).isoformat()

    table = auth.get_dynamodb_table()
    table.put_item(Item={
        "PK": "MSG",
        "SK": f"MSG#{message_id}",
        "author": body["author"],
        "text": body["text"],
        "createdAt": now,
    })
    return _response(201, {"id": message_id, "createdAt": now})
```

**Step 4: Run tests**

```bash
python -m pytest tests/unit/test_messages.py -v
```

Expected: All PASS.

**Step 5: Commit**

```bash
git add dad-birthday-backend/
git commit -m "feat: implement messages API (GET list, POST create)"
```

---

## Task 6: Backend — Media API

Implement media listing for guests and CRUD + pre-signed uploads for admin.

**Files:**
- Modify: `dad-birthday-backend/api/app.py`
- Create: `dad-birthday-backend/tests/unit/test_media.py`

**Step 1: Write failing tests**

`tests/unit/test_media.py`:

```python
import json
import os
import jwt
import time
from unittest.mock import patch, MagicMock

from api import app


def _auth_cookie(role="guest"):
    token = jwt.encode(
        {"role": role, "iat": int(time.time()), "exp": int(time.time()) + 3600},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    return f"session={token}"


class TestGetMedia:
    @patch("api.auth.get_dynamodb_table")
    def test_returns_media_list(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_table.query.return_value = {
            "Items": [
                {"PK": "MEDIA", "SK": "MEDIA#01ABC", "s3Key": "photos/family.jpg", "type": "photo", "caption": "Family photo", "order": 1, "createdAt": "2026-03-01T12:00:00Z"},
            ]
        }
        mock_get_table.return_value = mock_table

        event = make_event("GET", "/media", headers={"Cookie": _auth_cookie()})
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        data = json.loads(result["body"])
        assert len(data["media"]) == 1
        assert data["media"][0]["caption"] == "Family photo"
        assert "url" in data["media"][0]

    def test_unauthenticated_returns_401(self, make_event):
        event = make_event("GET", "/media")
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 401


class TestAdminUploadUrl:
    @patch("boto3.client")
    def test_returns_presigned_url(self, mock_boto_client, make_event):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/presigned"
        mock_boto_client.return_value = mock_s3

        event = make_event(
            "POST", "/admin/media/upload-url",
            body={"filename": "photo.jpg", "contentType": "image/jpeg"},
            headers={"Cookie": _auth_cookie("admin")},
        )
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        data = json.loads(result["body"])
        assert "uploadUrl" in data
        assert "s3Key" in data

    def test_guest_cannot_upload(self, make_event):
        event = make_event(
            "POST", "/admin/media/upload-url",
            body={"filename": "photo.jpg", "contentType": "image/jpeg"},
            headers={"Cookie": _auth_cookie("guest")},
        )
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 401


class TestAdminPostMedia:
    @patch("api.auth.get_dynamodb_table")
    def test_saves_media_metadata(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        event = make_event(
            "POST", "/admin/media",
            body={"s3Key": "photos/family.jpg", "type": "photo", "caption": "Family photo"},
            headers={"Cookie": _auth_cookie("admin")},
        )
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 201
        mock_table.put_item.assert_called_once()


class TestAdminDeleteMedia:
    @patch("boto3.client")
    @patch("api.auth.get_dynamodb_table")
    def test_deletes_media(self, mock_get_table, mock_boto_client, make_event):
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {"PK": "MEDIA", "SK": "MEDIA#01ABC", "s3Key": "photos/family.jpg"}
        }
        mock_get_table.return_value = mock_table
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        event = make_event(
            "DELETE", "/admin/media/01ABC",
            headers={"Cookie": _auth_cookie("admin")},
        )
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        mock_table.delete_item.assert_called_once()
```

**Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/unit/test_media.py -v
```

Expected: FAIL.

**Step 3: Implement media handlers in app.py**

Replace the media handler stubs:

```python
def handle_get_media(event):
    session = auth.require_auth(event)
    if not session:
        return _response(401, {"error": "Unauthorized"})

    table = auth.get_dynamodb_table()
    result = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": "MEDIA"},
    )
    cf_domain = os.environ.get("CLOUDFRONT_DOMAIN", "dad.melvinit.com")
    media = []
    for item in sorted(result.get("Items", []), key=lambda x: x.get("order", 0)):
        media.append({
            "id": item["SK"].split("#")[1],
            "url": f"https://{cf_domain}/media/{item['s3Key']}",
            "type": item.get("type", "photo"),
            "caption": item.get("caption", ""),
            "order": item.get("order", 0),
            "createdAt": item.get("createdAt", ""),
        })
    return _response(200, {"media": media})


def handle_upload_url(event):
    session = auth.require_auth(event, role="admin")
    if not session:
        return _response(401, {"error": "Unauthorized"})

    body = _parse_body(event)
    if not body or not body.get("filename") or not body.get("contentType"):
        return _response(400, {"error": "Provide 'filename' and 'contentType'"})

    import ulid as ulid_mod

    ext = body["filename"].rsplit(".", 1)[-1] if "." in body["filename"] else ""
    s3_key = f"uploads/{ulid_mod.new()}.{ext}" if ext else f"uploads/{ulid_mod.new()}"

    s3_client = boto3.client("s3")
    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": os.environ["MEDIA_BUCKET"],
            "Key": s3_key,
            "ContentType": body["contentType"],
        },
        ExpiresIn=3600,
    )
    return _response(200, {"uploadUrl": presigned_url, "s3Key": s3_key})


def handle_post_media(event):
    session = auth.require_auth(event, role="admin")
    if not session:
        return _response(401, {"error": "Unauthorized"})

    body = _parse_body(event)
    if not body or not body.get("s3Key") or not body.get("type"):
        return _response(400, {"error": "Provide 's3Key' and 'type'"})

    import ulid as ulid_mod
    from datetime import datetime, timezone

    media_id = str(ulid_mod.new())
    now = datetime.now(timezone.utc).isoformat()

    table = auth.get_dynamodb_table()
    table.put_item(Item={
        "PK": "MEDIA",
        "SK": f"MEDIA#{media_id}",
        "s3Key": body["s3Key"],
        "type": body["type"],
        "caption": body.get("caption", ""),
        "order": body.get("order", 0),
        "createdAt": now,
    })
    return _response(201, {"id": media_id, "createdAt": now})


def handle_delete_media(event):
    session = auth.require_auth(event, role="admin")
    if not session:
        return _response(401, {"error": "Unauthorized"})

    path = event.get("path", "")
    media_id = path.split("/")[-1]

    table = auth.get_dynamodb_table()
    result = table.get_item(Key={"PK": "MEDIA", "SK": f"MEDIA#{media_id}"})
    item = result.get("Item")
    if not item:
        return _response(404, {"error": "Media not found"})

    # Delete from S3
    s3_client = boto3.client("s3")
    s3_client.delete_object(Bucket=os.environ["MEDIA_BUCKET"], Key=item["s3Key"])

    # Delete from DynamoDB
    table.delete_item(Key={"PK": "MEDIA", "SK": f"MEDIA#{media_id}"})
    return _response(200, {"message": "Deleted"})


def handle_put_media(event):
    session = auth.require_auth(event, role="admin")
    if not session:
        return _response(401, {"error": "Unauthorized"})

    path = event.get("path", "")
    media_id = path.split("/")[-1]
    body = _parse_body(event)
    if not body:
        return _response(400, {"error": "Invalid body"})

    update_parts = []
    values = {}
    if "caption" in body:
        update_parts.append("caption = :caption")
        values[":caption"] = body["caption"]
    if "order" in body:
        update_parts.append("#ord = :order")
        values[":order"] = body["order"]

    if not update_parts:
        return _response(400, {"error": "Nothing to update"})

    table = auth.get_dynamodb_table()
    kwargs = {
        "Key": {"PK": "MEDIA", "SK": f"MEDIA#{media_id}"},
        "UpdateExpression": "SET " + ", ".join(update_parts),
        "ExpressionAttributeValues": values,
    }
    if "#ord" in str(update_parts):
        kwargs["ExpressionAttributeNames"] = {"#ord": "order"}
    table.update_item(**kwargs)
    return _response(200, {"message": "Updated"})
```

Also add `import boto3` at the top of `app.py`.

**Step 4: Run tests**

```bash
python -m pytest tests/unit/test_media.py -v
```

Expected: All PASS.

**Step 5: Commit**

```bash
git add dad-birthday-backend/
git commit -m "feat: implement media API (list, upload, CRUD for admin)"
```

---

## Task 7: Backend — Admin Token API

Implement token management for admins (create, list, revoke access tokens).

**Files:**
- Modify: `dad-birthday-backend/api/app.py`
- Create: `dad-birthday-backend/tests/unit/test_tokens.py`

**Step 1: Write failing tests**

`tests/unit/test_tokens.py`:

```python
import json
import os
import jwt
import time
from unittest.mock import patch, MagicMock

from api import app


def _auth_cookie(role="admin"):
    token = jwt.encode(
        {"role": role, "iat": int(time.time()), "exp": int(time.time()) + 3600},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    return f"session={token}"


class TestGetTokens:
    @patch("api.auth.get_dynamodb_table")
    def test_lists_tokens(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_table.query.return_value = {
            "Items": [
                {"PK": "TOKEN", "SK": "TOKEN#abc-123", "expiresAt": 9999999999, "label": "Family link", "createdAt": "2026-03-01T12:00:00Z"},
            ]
        }
        mock_get_table.return_value = mock_table

        event = make_event("GET", "/admin/tokens", headers={"Cookie": _auth_cookie()})
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        data = json.loads(result["body"])
        assert len(data["tokens"]) == 1

    def test_guest_cannot_list_tokens(self, make_event):
        event = make_event("GET", "/admin/tokens", headers={"Cookie": _auth_cookie("guest")})
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 401


class TestPostToken:
    @patch("api.auth.get_dynamodb_table")
    def test_creates_token(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        event = make_event(
            "POST", "/admin/tokens",
            body={"label": "For uncle Bob", "expiresInDays": 7},
            headers={"Cookie": _auth_cookie()},
        )
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 201
        data = json.loads(result["body"])
        assert "uuid" in data
        assert "url" in data
        mock_table.put_item.assert_called_once()


class TestDeleteToken:
    @patch("api.auth.get_dynamodb_table")
    def test_deletes_token(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        event = make_event(
            "DELETE", "/admin/tokens/abc-123",
            headers={"Cookie": _auth_cookie()},
        )
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        mock_table.delete_item.assert_called_once()
```

**Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/unit/test_tokens.py -v
```

Expected: FAIL.

**Step 3: Implement token handlers in app.py**

Replace token handler stubs:

```python
def handle_get_tokens(event):
    session = auth.require_auth(event, role="admin")
    if not session:
        return _response(401, {"error": "Unauthorized"})

    table = auth.get_dynamodb_table()
    result = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": "TOKEN"},
    )
    tokens = [
        {
            "uuid": item["SK"].split("#")[1],
            "label": item.get("label", ""),
            "expiresAt": item.get("expiresAt"),
            "createdAt": item.get("createdAt", ""),
        }
        for item in result.get("Items", [])
    ]
    return _response(200, {"tokens": tokens})


def handle_post_token(event):
    session = auth.require_auth(event, role="admin")
    if not session:
        return _response(401, {"error": "Unauthorized"})

    import uuid
    from datetime import datetime, timezone

    body = _parse_body(event)
    label = body.get("label", "") if body else ""
    expires_in_days = body.get("expiresInDays", 7) if body else 7

    token_uuid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    expires_at = int(time.time()) + (expires_in_days * 86400)

    table = auth.get_dynamodb_table()
    table.put_item(Item={
        "PK": "TOKEN",
        "SK": f"TOKEN#{token_uuid}",
        "expiresAt": expires_at,
        "label": label,
        "createdAt": now,
    })

    cf_domain = os.environ.get("CLOUDFRONT_DOMAIN", "dad.melvinit.com")
    url = f"https://{cf_domain}/?token={token_uuid}"

    return _response(201, {"uuid": token_uuid, "url": url, "expiresAt": expires_at})


def handle_delete_token(event):
    session = auth.require_auth(event, role="admin")
    if not session:
        return _response(401, {"error": "Unauthorized"})

    path = event.get("path", "")
    token_uuid = path.split("/")[-1]

    table = auth.get_dynamodb_table()
    table.delete_item(Key={"PK": "TOKEN", "SK": f"TOKEN#{token_uuid}"})
    return _response(200, {"message": "Token revoked"})
```

**Step 4: Run tests**

```bash
python -m pytest tests/unit/ -v
```

Expected: All tests across all test files PASS.

**Step 5: Commit**

```bash
git add dad-birthday-backend/
git commit -m "feat: implement admin token management API"
```

---

## Task 8: Frontend — Gate Page (Auth)

Build the landing page where guests enter the party code or auto-authenticate via URL token.

**Files:**
- Create: `dad-birthday-frontend/src/lib/api.ts`
- Modify: `dad-birthday-frontend/src/lib/stores/auth.svelte.ts`
- Modify: `dad-birthday-frontend/src/routes/+page.svelte`
- Create: `dad-birthday-frontend/src/routes/+page.svelte.test.ts` (optional, time permitting)

**Step 1: Create API client**

`src/lib/api.ts`:

```typescript
const API_BASE = '/api';

async function request(path: string, options: RequestInit = {}) {
	const res = await fetch(`${API_BASE}${path}`, {
		credentials: 'include',
		headers: { 'Content-Type': 'application/json', ...options.headers },
		...options
	});
	const data = await res.json();
	if (!res.ok) throw { status: res.status, ...data };
	return data;
}

export const api = {
	verify: (body: { code?: string; token?: string; admin?: boolean }) =>
		request('/verify', { method: 'POST', body: JSON.stringify(body) }),

	getMedia: () => request('/media'),

	getMessages: () => request('/messages'),

	postMessage: (author: string, text: string) =>
		request('/messages', { method: 'POST', body: JSON.stringify({ author, text }) }),

	getTokens: () => request('/admin/tokens'),

	createToken: (label: string, expiresInDays: number) =>
		request('/admin/tokens', {
			method: 'POST',
			body: JSON.stringify({ label, expiresInDays })
		}),

	deleteToken: (uuid: string) => request(`/admin/tokens/${uuid}`, { method: 'DELETE' }),

	getUploadUrl: (filename: string, contentType: string) =>
		request('/admin/media/upload-url', {
			method: 'POST',
			body: JSON.stringify({ filename, contentType })
		}),

	saveMedia: (s3Key: string, type: string, caption: string) =>
		request('/admin/media', {
			method: 'POST',
			body: JSON.stringify({ s3Key, type, caption })
		}),

	deleteMedia: (id: string) => request(`/admin/media/${id}`, { method: 'DELETE' }),

	updateMedia: (id: string, updates: { caption?: string; order?: number }) =>
		request(`/admin/media/${id}`, { method: 'PUT', body: JSON.stringify(updates) })
};
```

**Step 2: Update auth store**

`src/lib/stores/auth.svelte.ts`:

```typescript
export type AuthRole = 'guest' | 'admin' | null;

export const authState = $state<{ role: AuthRole; checking: boolean }>({
	role: null,
	checking: true
});
```

**Step 3: Build the gate page**

Replace `src/routes/+page.svelte`:

```svelte
<script lang="ts">
	import { api } from '$lib/api';
	import { authState } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	let code = $state('');
	let error = $state('');
	let loading = $state(false);

	// Check for token in URL on mount
	$effect(() => {
		const token = $page.url.searchParams.get('token');
		if (token) {
			verifyToken(token);
		} else {
			authState.checking = false;
		}
	});

	async function verifyToken(token: string) {
		try {
			await api.verify({ token });
			authState.role = 'guest';
			goto('/gallery');
		} catch {
			authState.checking = false;
			error = 'This link has expired or is invalid.';
		}
	}

	async function handleSubmit() {
		if (!code.trim()) return;
		loading = true;
		error = '';
		try {
			await api.verify({ code: code.trim() });
			authState.role = 'guest';
			goto('/gallery');
		} catch {
			error = 'Invalid code. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Dad's 80th Birthday</title>
</svelte:head>

{#if authState.checking}
	<div class="flex min-h-screen items-center justify-center">
		<p class="text-brown-light text-xl italic">Checking your invitation...</p>
	</div>
{:else}
	<div class="flex min-h-screen flex-col items-center justify-center px-4">
		<div class="w-full max-w-md text-center">
			<h1 class="font-display text-gold mb-2 text-6xl font-bold">80</h1>
			<p class="font-display text-brown mb-8 text-2xl">Years of Love & Memories</p>

			<div class="rounded-lg border border-gold/30 bg-white/80 p-8 shadow-lg backdrop-blur-sm">
				<p class="text-brown-light mb-6 text-lg">
					Enter the party code to view the celebration
				</p>

				<form onsubmit={handleSubmit} class="space-y-4">
					<input
						type="text"
						bind:value={code}
						placeholder="Enter party code"
						class="border-gold/40 text-brown placeholder:text-brown-light/50 focus:border-gold focus:ring-gold w-full rounded-md border bg-cream/50 px-4 py-3 text-center text-lg"
					/>

					{#if error}
						<p class="text-sm text-red-600">{error}</p>
					{/if}

					<button
						type="submit"
						disabled={loading || !code.trim()}
						class="bg-brown hover:bg-brown-light w-full rounded-md px-6 py-3 text-lg text-cream transition-colors disabled:opacity-50"
					>
						{loading ? 'Verifying...' : 'Enter'}
					</button>
				</form>
			</div>
		</div>
	</div>
{/if}
```

**Step 4: Verify dev server**

```bash
cd ~/Development/dad-birthday/dad-birthday-frontend
npm run dev
```

Open `http://localhost:5173` — should see the gate page with vintage styling.

**Step 5: Commit**

```bash
git add dad-birthday-frontend/src/
git commit -m "feat: add gate page with party code and token auth"
```

---

## Task 9: Frontend — Navigation + Layout Shell

Add shared navigation that appears after authentication.

**Files:**
- Create: `dad-birthday-frontend/src/lib/components/Nav.svelte`
- Modify: `dad-birthday-frontend/src/routes/+layout.svelte`
- Create: `dad-birthday-frontend/src/routes/gallery/+page.svelte` (placeholder)
- Create: `dad-birthday-frontend/src/routes/messages/+page.svelte` (placeholder)
- Create: `dad-birthday-frontend/src/routes/admin/+page.svelte` (placeholder)

**Step 1: Create Nav component**

`src/lib/components/Nav.svelte`:

```svelte
<script lang="ts">
	import { authState } from '$lib/stores/auth.svelte';
	import { page } from '$app/stores';

	let menuOpen = $state(false);

	function isActive(path: string) {
		return $page.url.pathname === path;
	}
</script>

<nav class="border-gold/20 bg-cream/90 border-b backdrop-blur-sm">
	<div class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
		<a href="/gallery" class="font-display text-brown text-xl font-bold">
			Dad's 80th
		</a>

		<!-- Desktop nav -->
		<div class="hidden gap-6 sm:flex">
			<a
				href="/gallery"
				class="text-brown hover:text-gold transition-colors"
				class:font-bold={isActive('/gallery')}
			>Gallery</a>
			<a
				href="/messages"
				class="text-brown hover:text-gold transition-colors"
				class:font-bold={isActive('/messages')}
			>Messages</a>
			{#if authState.role === 'admin'}
				<a
					href="/admin"
					class="text-gold hover:text-gold-light transition-colors"
					class:font-bold={isActive('/admin')}
				>Admin</a>
			{/if}
		</div>

		<!-- Mobile hamburger -->
		<button class="text-brown sm:hidden" onclick={() => (menuOpen = !menuOpen)}>
			<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				{#if menuOpen}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				{:else}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
				{/if}
			</svg>
		</button>
	</div>

	<!-- Mobile menu -->
	{#if menuOpen}
		<div class="border-gold/20 border-t px-4 pb-3 sm:hidden">
			<a href="/gallery" class="text-brown block py-2" onclick={() => (menuOpen = false)}>Gallery</a>
			<a href="/messages" class="text-brown block py-2" onclick={() => (menuOpen = false)}>Messages</a>
			{#if authState.role === 'admin'}
				<a href="/admin" class="text-gold block py-2" onclick={() => (menuOpen = false)}>Admin</a>
			{/if}
		</div>
	{/if}
</nav>
```

**Step 2: Update root layout to show nav when authenticated**

`src/routes/+layout.svelte`:

```svelte
<script lang="ts">
	import '../app.css';
	import { authState } from '$lib/stores/auth.svelte';
	import Nav from '$lib/components/Nav.svelte';

	let { children } = $props();
</script>

<div class="min-h-screen bg-cream">
	{#if authState.role}
		<Nav />
	{/if}
	{@render children?.()}
</div>
```

**Step 3: Create placeholder route pages**

`src/routes/gallery/+page.svelte`:
```svelte
<div class="p-8">
	<h1 class="font-display text-brown text-3xl">Gallery</h1>
	<p class="text-brown-light mt-2">Coming soon...</p>
</div>
```

`src/routes/messages/+page.svelte`:
```svelte
<div class="p-8">
	<h1 class="font-display text-brown text-3xl">Messages</h1>
	<p class="text-brown-light mt-2">Coming soon...</p>
</div>
```

`src/routes/admin/+page.svelte`:
```svelte
<div class="p-8">
	<h1 class="font-display text-brown text-3xl">Admin</h1>
	<p class="text-brown-light mt-2">Coming soon...</p>
</div>
```

**Step 4: Verify navigation works**

```bash
npm run dev
```

Manually set `authState.role = 'guest'` in the store or temporarily bypass the gate to test navigation.

**Step 5: Commit**

```bash
git add dad-birthday-frontend/src/
git commit -m "feat: add navigation bar and route placeholders"
```

---

## Task 10: Frontend — Gallery Page

Build the photo/video gallery with masonry grid and lightbox.

**Files:**
- Modify: `dad-birthday-frontend/src/routes/gallery/+page.svelte`
- Create: `dad-birthday-frontend/src/lib/components/Lightbox.svelte`
- Create: `dad-birthday-frontend/src/lib/components/VideoPlayer.svelte`

**Step 1: Create VideoPlayer component**

`src/lib/components/VideoPlayer.svelte`:

```svelte
<script lang="ts">
	let { src, class: className = '' }: { src: string; class?: string } = $props();
</script>

<!-- svelte-ignore a11y_media_has_caption -->
<video
	controls
	preload="metadata"
	class={className}
	{src}
>
	Your browser does not support the video tag.
</video>
```

**Step 2: Create Lightbox component**

`src/lib/components/Lightbox.svelte`:

```svelte
<script lang="ts">
	import VideoPlayer from './VideoPlayer.svelte';

	type MediaItem = { id: string; url: string; type: string; caption: string };

	let {
		item,
		onclose
	}: {
		item: MediaItem;
		onclose: () => void;
	} = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onclose();
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div
	class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
	onclick={onclose}
>
	<div
		class="relative max-h-[90vh] max-w-4xl"
		onclick={(e) => e.stopPropagation()}
	>
		<button
			class="absolute -top-10 right-0 text-2xl text-white hover:text-gold"
			onclick={onclose}
		>
			&times; Close
		</button>

		{#if item.type === 'video'}
			<VideoPlayer src={item.url} class="max-h-[80vh] rounded-lg" />
		{:else}
			<img
				src={item.url}
				alt={item.caption}
				class="max-h-[80vh] rounded-lg object-contain"
			/>
		{/if}

		{#if item.caption}
			<p class="font-handwriting mt-3 text-center text-xl text-white">
				{item.caption}
			</p>
		{/if}
	</div>
</div>
```

**Step 3: Build the gallery page**

Replace `src/routes/gallery/+page.svelte`:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import Lightbox from '$lib/components/Lightbox.svelte';

	type MediaItem = { id: string; url: string; type: string; caption: string; order: number };

	let media = $state<MediaItem[]>([]);
	let loading = $state(true);
	let selectedItem = $state<MediaItem | null>(null);

	onMount(async () => {
		try {
			const data = await api.getMedia();
			media = data.media;
		} catch (e) {
			console.error('Failed to load media', e);
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Gallery - Dad's 80th Birthday</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8">
	<h1 class="font-display text-brown mb-8 text-center text-4xl">Memories</h1>

	{#if loading}
		<p class="text-brown-light text-center text-lg italic">Loading memories...</p>
	{:else if media.length === 0}
		<p class="text-brown-light text-center text-lg">No photos yet. Check back soon!</p>
	{:else}
		<div class="columns-1 gap-4 sm:columns-2 lg:columns-3">
			{#each media as item (item.id)}
				<button
					class="group mb-4 block w-full overflow-hidden rounded-lg border-4 border-white bg-white shadow-md transition-transform hover:scale-[1.02]"
					onclick={() => (selectedItem = item)}
				>
					{#if item.type === 'video'}
						<div class="relative">
							<!-- svelte-ignore a11y_media_has_caption -->
							<video
								preload="metadata"
								class="w-full sepia-[.3] transition-all group-hover:sepia-0"
								src={item.url}
							/>
							<div class="absolute inset-0 flex items-center justify-center">
								<div class="rounded-full bg-black/50 p-3 text-white">
									<svg class="h-8 w-8" fill="currentColor" viewBox="0 0 24 24">
										<path d="M8 5v14l11-7z" />
									</svg>
								</div>
							</div>
						</div>
					{:else}
						<img
							src={item.url}
							alt={item.caption}
							class="w-full sepia-[.3] transition-all group-hover:sepia-0"
							loading="lazy"
						/>
					{/if}
					{#if item.caption}
						<p class="font-handwriting text-brown px-3 py-2 text-lg">{item.caption}</p>
					{/if}
				</button>
			{/each}
		</div>
	{/if}
</div>

{#if selectedItem}
	<Lightbox item={selectedItem} onclose={() => (selectedItem = null)} />
{/if}
```

**Step 4: Verify**

```bash
npm run dev
```

Navigate to `/gallery` — should render the grid (empty state if no API running).

**Step 5: Run type check**

```bash
npm run check
```

Expected: No errors.

**Step 6: Commit**

```bash
git add dad-birthday-frontend/src/
git commit -m "feat: add gallery page with masonry grid and lightbox"
```

---

## Task 11: Frontend — Messages Page

Build the message wall and submission form.

**Files:**
- Modify: `dad-birthday-frontend/src/routes/messages/+page.svelte`

**Step 1: Build the messages page**

Replace `src/routes/messages/+page.svelte`:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	type Message = { id: string; author: string; text: string; createdAt: string };

	let messages = $state<Message[]>([]);
	let loading = $state(true);
	let author = $state('');
	let text = $state('');
	let submitting = $state(false);
	let submitted = $state(false);

	onMount(async () => {
		try {
			const data = await api.getMessages();
			messages = data.messages;
		} catch (e) {
			console.error('Failed to load messages', e);
		} finally {
			loading = false;
		}
	});

	async function handleSubmit() {
		if (!author.trim() || !text.trim()) return;
		submitting = true;
		try {
			await api.postMessage(author.trim(), text.trim());
			// Refresh messages
			const data = await api.getMessages();
			messages = data.messages;
			author = '';
			text = '';
			submitted = true;
			setTimeout(() => (submitted = false), 3000);
		} catch (e) {
			console.error('Failed to post message', e);
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head>
	<title>Messages - Dad's 80th Birthday</title>
</svelte:head>

<div class="mx-auto max-w-3xl px-4 py-8">
	<h1 class="font-display text-brown mb-8 text-center text-4xl">Birthday Wishes</h1>

	<!-- Message form -->
	<div class="mb-10 rounded-lg border border-gold/30 bg-white/80 p-6 shadow-md">
		<h2 class="font-display text-brown mb-4 text-2xl">Leave a Message</h2>
		<form onsubmit={handleSubmit} class="space-y-4">
			<input
				type="text"
				bind:value={author}
				placeholder="Your name"
				class="border-gold/40 text-brown placeholder:text-brown-light/50 focus:border-gold focus:ring-gold w-full rounded-md border bg-cream/50 px-4 py-2"
				maxlength="100"
			/>
			<textarea
				bind:value={text}
				placeholder="Write your birthday message..."
				rows="4"
				class="border-gold/40 text-brown placeholder:text-brown-light/50 focus:border-gold focus:ring-gold w-full rounded-md border bg-cream/50 px-4 py-2"
				maxlength="1000"
			></textarea>
			<button
				type="submit"
				disabled={submitting || !author.trim() || !text.trim()}
				class="bg-brown hover:bg-brown-light rounded-md px-6 py-2 text-cream transition-colors disabled:opacity-50"
			>
				{submitting ? 'Sending...' : 'Send Birthday Wish'}
			</button>
			{#if submitted}
				<p class="text-gold text-sm">Thank you for your message!</p>
			{/if}
		</form>
	</div>

	<!-- Message wall -->
	{#if loading}
		<p class="text-brown-light text-center italic">Loading messages...</p>
	{:else if messages.length === 0}
		<p class="text-brown-light text-center">No messages yet. Be the first!</p>
	{:else}
		<div class="space-y-4">
			{#each messages as msg (msg.id)}
				<div class="rounded-lg border border-gold/20 bg-white/70 p-5 shadow-sm">
					<p class="font-handwriting text-brown text-xl leading-relaxed">{msg.text}</p>
					<p class="text-brown-light mt-3 text-sm">
						&mdash; {msg.author}
					</p>
				</div>
			{/each}
		</div>
	{/if}
</div>
```

**Step 2: Verify**

```bash
npm run dev
```

Navigate to `/messages` — should render the form and empty message list.

**Step 3: Run type check**

```bash
npm run check
```

**Step 4: Commit**

```bash
git add dad-birthday-frontend/src/
git commit -m "feat: add messages page with submission form and message wall"
```

---

## Task 12: Frontend — Admin Dashboard

Build the admin page with media upload and token management.

**Files:**
- Modify: `dad-birthday-frontend/src/routes/admin/+page.svelte`

**Step 1: Build the admin dashboard**

Replace `src/routes/admin/+page.svelte`:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { authState } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';

	type Token = { uuid: string; label: string; expiresAt: number; createdAt: string };
	type MediaItem = { id: string; url: string; type: string; caption: string; order: number };

	let activeTab = $state<'media' | 'tokens'>('media');
	let tokens = $state<Token[]>([]);
	let media = $state<MediaItem[]>([]);
	let loading = $state(true);

	// Upload state
	let uploadFiles = $state<FileList | null>(null);
	let uploadCaption = $state('');
	let uploading = $state(false);

	// Token creation state
	let tokenLabel = $state('');
	let tokenDays = $state(7);
	let creatingToken = $state(false);

	onMount(async () => {
		if (authState.role !== 'admin') {
			goto('/');
			return;
		}
		await loadData();
	});

	async function loadData() {
		loading = true;
		try {
			const [mediaData, tokenData] = await Promise.all([api.getMedia(), api.getTokens()]);
			media = mediaData.media;
			tokens = tokenData.tokens;
		} catch (e) {
			console.error('Failed to load admin data', e);
		} finally {
			loading = false;
		}
	}

	async function handleUpload() {
		if (!uploadFiles || uploadFiles.length === 0) return;
		uploading = true;
		try {
			for (const file of uploadFiles) {
				const isVideo = file.type.startsWith('video/');
				// Get pre-signed URL
				const { uploadUrl, s3Key } = await api.getUploadUrl(file.name, file.type);
				// Upload directly to S3
				await fetch(uploadUrl, {
					method: 'PUT',
					body: file,
					headers: { 'Content-Type': file.type }
				});
				// Save metadata
				await api.saveMedia(s3Key, isVideo ? 'video' : 'photo', uploadCaption);
			}
			uploadCaption = '';
			uploadFiles = null;
			await loadData();
		} catch (e) {
			console.error('Upload failed', e);
		} finally {
			uploading = false;
		}
	}

	async function handleDeleteMedia(id: string) {
		try {
			await api.deleteMedia(id);
			await loadData();
		} catch (e) {
			console.error('Delete failed', e);
		}
	}

	async function handleCreateToken() {
		if (!tokenLabel.trim()) return;
		creatingToken = true;
		try {
			await api.createToken(tokenLabel.trim(), tokenDays);
			tokenLabel = '';
			await loadData();
		} catch (e) {
			console.error('Token creation failed', e);
		} finally {
			creatingToken = false;
		}
	}

	async function handleDeleteToken(uuid: string) {
		try {
			await api.deleteToken(uuid);
			await loadData();
		} catch (e) {
			console.error('Token deletion failed', e);
		}
	}
</script>

<svelte:head>
	<title>Admin - Dad's 80th Birthday</title>
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-8">
	<h1 class="font-display text-brown mb-6 text-3xl">Admin Dashboard</h1>

	<!-- Tabs -->
	<div class="border-gold/30 mb-6 flex gap-4 border-b">
		<button
			class="pb-2 transition-colors"
			class:border-b-2={activeTab === 'media'}
			class:border-gold={activeTab === 'media'}
			class:text-brown={activeTab === 'media'}
			class:text-brown-light={activeTab !== 'media'}
			onclick={() => (activeTab = 'media')}
		>Upload Media</button>
		<button
			class="pb-2 transition-colors"
			class:border-b-2={activeTab === 'tokens'}
			class:border-gold={activeTab === 'tokens'}
			class:text-brown={activeTab === 'tokens'}
			class:text-brown-light={activeTab !== 'tokens'}
			onclick={() => (activeTab = 'tokens')}
		>Access Tokens</button>
	</div>

	{#if loading}
		<p class="text-brown-light italic">Loading...</p>
	{:else if activeTab === 'media'}
		<!-- Upload form -->
		<div class="mb-8 rounded-lg border border-gold/30 bg-white/80 p-6">
			<h2 class="font-display text-brown mb-4 text-xl">Upload Photos & Videos</h2>
			<form onsubmit={handleUpload} class="space-y-4">
				<input
					type="file"
					accept="image/*,video/*"
					multiple
					onchange={(e) => (uploadFiles = e.currentTarget.files)}
					class="text-brown w-full"
				/>
				<input
					type="text"
					bind:value={uploadCaption}
					placeholder="Caption (optional)"
					class="border-gold/40 w-full rounded-md border px-4 py-2"
				/>
				<button
					type="submit"
					disabled={uploading || !uploadFiles?.length}
					class="bg-brown hover:bg-brown-light rounded-md px-6 py-2 text-cream disabled:opacity-50"
				>
					{uploading ? 'Uploading...' : 'Upload'}
				</button>
			</form>
		</div>

		<!-- Media list -->
		<div class="space-y-3">
			{#each media as item (item.id)}
				<div class="flex items-center gap-4 rounded-lg border border-gold/20 bg-white/70 p-3">
					{#if item.type === 'video'}
						<div class="bg-brown-light/20 flex h-16 w-16 flex-shrink-0 items-center justify-center rounded">
							<span class="text-sm">Video</span>
						</div>
					{:else}
						<img src={item.url} alt={item.caption} class="h-16 w-16 flex-shrink-0 rounded object-cover" />
					{/if}
					<div class="flex-1">
						<p class="text-brown text-sm">{item.caption || '(no caption)'}</p>
					</div>
					<button
						class="text-sm text-red-600 hover:text-red-800"
						onclick={() => handleDeleteMedia(item.id)}
					>Delete</button>
				</div>
			{/each}
		</div>
	{:else}
		<!-- Token creation -->
		<div class="mb-8 rounded-lg border border-gold/30 bg-white/80 p-6">
			<h2 class="font-display text-brown mb-4 text-xl">Create Access Link</h2>
			<form onsubmit={handleCreateToken} class="space-y-4">
				<input
					type="text"
					bind:value={tokenLabel}
					placeholder="Label (e.g., 'For Uncle Bob')"
					class="border-gold/40 w-full rounded-md border px-4 py-2"
				/>
				<div class="flex items-center gap-2">
					<label for="days" class="text-brown text-sm">Expires in:</label>
					<select
						id="days"
						bind:value={tokenDays}
						class="border-gold/40 rounded-md border px-3 py-2"
					>
						<option value={1}>1 day</option>
						<option value={3}>3 days</option>
						<option value={7}>7 days</option>
						<option value={14}>14 days</option>
						<option value={30}>30 days</option>
					</select>
				</div>
				<button
					type="submit"
					disabled={creatingToken || !tokenLabel.trim()}
					class="bg-brown hover:bg-brown-light rounded-md px-6 py-2 text-cream disabled:opacity-50"
				>
					{creatingToken ? 'Creating...' : 'Create Link'}
				</button>
			</form>
		</div>

		<!-- Token list -->
		<div class="space-y-3">
			{#each tokens as token (token.uuid)}
				<div class="rounded-lg border border-gold/20 bg-white/70 p-4">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-brown font-medium">{token.label || '(no label)'}</p>
							<p class="text-brown-light text-xs">
								Expires: {new Date(token.expiresAt * 1000).toLocaleDateString()}
							</p>
						</div>
						<button
							class="text-sm text-red-600 hover:text-red-800"
							onclick={() => handleDeleteToken(token.uuid)}
						>Revoke</button>
					</div>
					<p class="mt-2 rounded bg-cream/50 p-2 text-xs break-all">
						https://dad.melvinit.com/?token={token.uuid}
					</p>
				</div>
			{/each}
		</div>
	{/if}
</div>
```

**Step 2: Verify**

```bash
npm run check
npm run dev
```

**Step 3: Commit**

```bash
git add dad-birthday-frontend/src/
git commit -m "feat: add admin dashboard with media upload and token management"
```

---

## Task 13: Infrastructure — CDK Stack

Create the CDK infrastructure: S3 buckets, CloudFront, DynamoDB, Route53, API Gateway integration.

**Files:**
- Create: `infra/package.json`
- Create: `infra/tsconfig.json`
- Create: `infra/cdk.json`
- Create: `infra/bin/infra.ts`
- Create: `infra/lib/birthday-stack.ts`

**Step 1: Copy CDK scaffolding from dakamin**

Copy `infra/package.json`, `infra/tsconfig.json` from dakamin verbatim.

Create `infra/cdk.json`:
```json
{
  "app": "npx ts-node --prefer-ts-exts bin/infra.ts",
  "watch": {
    "include": ["**"],
    "exclude": ["node_modules", "cdk.out", "**/*.js", "**/*.d.ts"]
  },
  "context": {}
}
```

**Step 2: Create CDK app entry point**

`infra/bin/infra.ts`:

```typescript
#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BirthdayTributeSiteStack } from '../lib/birthday-stack';

const app = new cdk.App();

const account = process.env.CDK_DEFAULT_ACCOUNT;
const region = 'us-east-1';

if (!account) {
  throw new Error('Set CDK_DEFAULT_ACCOUNT environment variable.');
}

new BirthdayTributeSiteStack(app, 'DadBirthdayStack', {
  env: { account, region },
  domainName: 'dad.melvinit.com',
  parentDomainName: 'melvinit.com',
  tags: {
    Project: 'DadBirthday',
    Environment: 'Production',
    ManagedBy: 'CDK',
  },
});

app.synth();
```

**Step 3: Create the CDK stack**

`infra/lib/birthday-stack.ts`:

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

export interface BirthdayTributeSiteStackProps extends cdk.StackProps {
  readonly domainName: string;       // e.g. dad.melvinit.com
  readonly parentDomainName: string; // e.g. melvinit.com
  readonly websiteDistPath?: string;
}

export class BirthdayTributeSiteStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BirthdayTributeSiteStackProps) {
    super(scope, id, {
      ...props,
      env: { ...props.env, region: 'us-east-1' },
      description: `Birthday tribute site infrastructure for ${props.domainName}`,
    });

    const { domainName, parentDomainName } = props;

    // --- Route 53: Look up parent hosted zone ---
    const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
      domainName: parentDomainName,
    });

    // --- DynamoDB Table ---
    const table = new dynamodb.Table(this, 'BirthdayTable', {
      tableName: 'DadBirthdayTable',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      timeToLiveAttribute: 'expiresAt',
    });

    // --- S3: Site Bucket ---
    const siteBucket = new s3.Bucket(this, 'SiteBucket', {
      bucketName: `${domainName}-site-${this.account}-${this.region}`,
      publicReadAccess: false,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    // --- S3: Media Bucket ---
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

    // --- ACM Certificate ---
    const certificate = new acm.Certificate(this, 'SiteCertificate', {
      domainName: domainName,
      validation: acm.CertificateValidation.fromDns(hostedZone),
    });

    // --- CloudFront Distribution ---
    // Note: The API Gateway origin will be added after SAM deployment.
    // For now, set up site + media origins.
    const distribution = new cloudfront.Distribution(this, 'SiteDistribution', {
      comment: `Birthday tribute site for ${domainName}`,
      defaultBehavior: {
        origin: new origins.S3Origin(siteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        compress: true,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
      },
      additionalBehaviors: {
        '/media/*': {
          origin: new origins.S3Origin(mediaBucket),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
          compress: true,
          cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        },
        // API behavior will be added post-SAM deploy with the API Gateway URL
      },
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

    // --- Route 53: A Record for subdomain ---
    new route53.ARecord(this, 'SubdomainAliasRecord', {
      zone: hostedZone,
      recordName: domainName,
      target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
    });

    // --- Outputs ---
    new cdk.CfnOutput(this, 'SiteBucketName', { value: siteBucket.bucketName });
    new cdk.CfnOutput(this, 'MediaBucketName', { value: mediaBucket.bucketName });
    new cdk.CfnOutput(this, 'DistributionId', { value: distribution.distributionId });
    new cdk.CfnOutput(this, 'DistributionDomainName', { value: distribution.distributionDomainName });
    new cdk.CfnOutput(this, 'TableName', { value: table.tableName });
    new cdk.CfnOutput(this, 'WebsiteURL', { value: `https://${domainName}` });
  }
}
```

**Step 4: Install dependencies and verify**

```bash
cd ~/Development/dad-birthday/infra
npm install
npm run build
```

Expected: TypeScript compiles without errors.

**Step 5: Synthesize CloudFormation**

```bash
npx cdk synth
```

Expected: Generates CloudFormation template in `cdk.out/`. (May need AWS credentials configured for hosted zone lookup.)

**Step 6: Commit**

```bash
git add infra/
git commit -m "feat: add CDK infrastructure stack with S3, CloudFront, DynamoDB, Route53"
```

---

## Task 14: CI/CD — GitHub Actions Workflow

Create the deployment workflow.

**Files:**
- Create: `.github/workflows/deploy.yml`

**Step 1: Create workflow file**

`.github/workflows/deploy.yml`:

```yaml
name: Deploy Birthday Tribute Site

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        working-directory: ./dad-birthday-frontend
        run: npm install

      - name: Build frontend
        working-directory: ./dad-birthday-frontend
        run: npm run build

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_IAM_ROLE_ARN }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Deploy to S3
        uses: reggionick/s3-deploy@v4
        with:
          folder: ./dad-birthday-frontend/build
          bucket: ${{ secrets.DAD_S3_BUCKET_NAME }}
          bucket-region: ${{ secrets.AWS_REGION }}
          dist-id: ${{ secrets.DAD_CLOUDFRONT_DISTRIBUTION_ID }}
          invalidation: /
          delete-removed: true
          private: true

  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - uses: aws-actions/setup-sam@v2

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_IAM_ROLE_ARN }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: SAM build
        working-directory: ./dad-birthday-backend
        run: sam build --use-container

      - name: SAM deploy
        working-directory: ./dad-birthday-backend
        run: |
          sam deploy --no-confirm-changeset --no-fail-on-empty-changeset \
            --parameter-overrides \
              TableName=${{ secrets.DAD_TABLE_NAME }} \
              MediaBucket=${{ secrets.DAD_MEDIA_BUCKET }} \
              PartyCode=${{ secrets.DAD_PARTY_CODE }} \
              AdminCode=${{ secrets.DAD_ADMIN_CODE }} \
              JwtSecret=${{ secrets.DAD_JWT_SECRET }} \
              CloudFrontDomain=dad.melvinit.com
```

**Step 2: Commit**

```bash
git add .github/
git commit -m "feat: add GitHub Actions CI/CD workflow for frontend and backend"
```

---

## Task 15: Integration — Connect API Gateway to CloudFront

After the SAM backend is deployed, add the API Gateway as a CloudFront origin.

**Files:**
- Modify: `infra/lib/birthday-stack.ts`

**Step 1: Add API Gateway origin to CloudFront**

Add a `apiGatewayDomain` prop to the stack and add an `/api/*` behavior to the CloudFront distribution. This can also be done manually after first SAM deploy by updating the CDK stack with the API Gateway domain.

Add to the `additionalBehaviors` in the distribution:

```typescript
'/api/*': {
  origin: new origins.HttpOrigin(apiGatewayDomain, {
    originPath: '/Prod',
  }),
  viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
  allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
  cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
  originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
},
```

**Step 2: Verify**

```bash
cd ~/Development/dad-birthday/infra
npm run build
```

**Step 3: Commit**

```bash
git add infra/
git commit -m "feat: add API Gateway origin to CloudFront distribution"
```

---

## Task 16: Final Polish — Run All Checks

**Step 1: Frontend checks**

```bash
cd ~/Development/dad-birthday/dad-birthday-frontend
npm run check
npm run lint
```

Fix any issues.

**Step 2: Backend tests**

```bash
cd ~/Development/dad-birthday/dad-birthday-backend
python -m pytest tests/unit/ -v
```

All tests should pass.

**Step 3: Infrastructure build**

```bash
cd ~/Development/dad-birthday/infra
npm run build
```

Should compile cleanly.

**Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: address lint and type-check issues"
```

---

## Deployment Order

Once all code is committed:

1. **CDK Deploy** (infra) — creates S3 buckets, CloudFront, DynamoDB, Route53 record
2. **SAM Deploy** (backend) — creates Lambda + API Gateway, note the API Gateway URL
3. **Update CDK** with API Gateway domain → redeploy CDK to add `/api/*` CloudFront behavior
4. **Frontend Deploy** — build and upload to S3, invalidate CloudFront
5. **Create admin session** — hit `POST /verify` with admin code to get admin access
6. **Upload initial photos** — use admin dashboard to upload photos/videos
7. **Create access tokens** — generate shareable links for party guests
8. **Test end-to-end** — verify gate → gallery → messages flow works

---

## GitHub Secrets to Configure

| Secret | Value |
|--------|-------|
| `AWS_REGION` | `us-east-1` |
| `AWS_IAM_ROLE_ARN` | Your IAM role ARN (with S3, CloudFront, Lambda, DynamoDB permissions) |
| `DAD_S3_BUCKET_NAME` | Output from CDK deploy (SiteBucketName) |
| `DAD_CLOUDFRONT_DISTRIBUTION_ID` | Output from CDK deploy (DistributionId) |
| `DAD_TABLE_NAME` | `DadBirthdayTable` |
| `DAD_MEDIA_BUCKET` | Output from CDK deploy (MediaBucketName) |
| `DAD_PARTY_CODE` | Your chosen party code (e.g., `dad80`) |
| `DAD_ADMIN_CODE` | Your chosen admin code |
| `DAD_JWT_SECRET` | A random secret string for JWT signing |
