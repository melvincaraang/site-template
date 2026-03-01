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
