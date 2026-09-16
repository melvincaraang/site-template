#!/usr/bin/env python3
"""Local API server — runs the real Lambda handler without Docker or AWS.

* DynamoDB is mocked in-process with moto (data lives for the process
  lifetime, or persists to a JSON snapshot when DEV_DATA is set).
* Access codes default to PARTY_CODE=party and ADMIN_CODE=admin.

Usage:  .venv/bin/python scripts/dev_server.py   (listens on http://localhost:3000)
"""

import json
import os
import sys
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault("TABLE_NAME", "site-dev")
os.environ.setdefault("MEDIA_BUCKET", "site-dev-media")
os.environ.setdefault("PARTY_CODE", "party")
os.environ.setdefault("ADMIN_CODE", "admin")
os.environ.setdefault("JWT_SECRET", "dev-jwt-secret-not-for-production-32-bytes-min")
os.environ.setdefault("CLOUDFRONT_DOMAIN", "localhost:5173")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.pop("DYNAMODB_ENDPOINT", None)

import boto3  # noqa: E402
from moto import mock_aws  # noqa: E402

from api.app import lambda_handler  # noqa: E402

PORT = int(os.environ.get("PORT", "3000"))
DATA_FILE = os.environ.get("DEV_DATA")


class Handler(BaseHTTPRequestHandler):
    server_version = "SiteDevAPI/0.1"

    def _handle(self) -> None:
        url = urlsplit(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode() if length else None
        event = {
            "httpMethod": self.command,
            "path": url.path,
            "queryStringParameters": None,
            "headers": dict(self.headers.items()),
            "body": body,
            "requestContext": {"httpMethod": self.command, "stage": "dev"},
        }
        result = lambda_handler(event, None)
        self.send_response(int(result["statusCode"]))
        for k, raw_value in result.get("headers", {}).items():
            # Browsers ignore Secure cookies over plain http://localhost in
            # some configurations; strip it for local dev only.
            v = raw_value.replace("; Secure", "") if k.lower() == "set-cookie" else raw_value
            self.send_header(k, v)
        payload = str(result["body"]).encode()
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        if DATA_FILE:
            snapshot()

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _handle

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("[dev-api] " + (fmt % args) + "\n")


def create_table() -> None:
    boto3.resource("dynamodb").create_table(
        TableName=os.environ["TABLE_NAME"],
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}, {"AttributeName": "SK", "KeyType": "RANGE"}],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


def snapshot() -> None:
    assert DATA_FILE
    table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    items: list[dict] = []
    kwargs: dict[str, object] = {}
    while True:
        r = table.scan(**kwargs)
        items.extend(r["Items"])
        if "LastEvaluatedKey" not in r:
            break
        kwargs["ExclusiveStartKey"] = r["LastEvaluatedKey"]
    with open(DATA_FILE, "w") as f:
        json.dump(items, f, default=lambda o: int(o) if isinstance(o, Decimal) else str(o))


def restore() -> None:
    if not DATA_FILE or not os.path.exists(DATA_FILE):
        return
    table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    with open(DATA_FILE) as f:
        for item in json.load(f):
            table.put_item(Item=item)


def main() -> None:
    with mock_aws():
        create_table()
        restore()
        print(f"[dev-api] listening on http://localhost:{PORT}  (codes: party / admin)")
        ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
