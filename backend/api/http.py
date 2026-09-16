"""API Gateway request/response helpers shared by every handler module."""

import json
import os
from decimal import Decimal
from typing import Any


class _DecimalEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return int(o) if o == int(o) else float(o)
        return super().default(o)


def parse_body(event: dict[str, Any]) -> dict[str, Any] | None:
    """Return the JSON object body, {} when absent, or None when malformed."""
    body = event.get("body", "{}")
    if body is None:
        return {}
    if isinstance(body, str):
        try:
            data = json.loads(body or "{}")
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None
    return body if isinstance(body, dict) else None


def response(status_code: int, body: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    """Build an API Gateway proxy response."""
    resp_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": f"https://{os.environ['CLOUDFRONT_DOMAIN']}",
        "Access-Control-Allow-Credentials": "true",
        "Cache-Control": "no-store",
    }
    if headers:
        resp_headers.update(headers)
    return {"statusCode": status_code, "headers": resp_headers, "body": json.dumps(body, cls=_DecimalEncoder)}
