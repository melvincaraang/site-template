"""Lambda entry point: routes API Gateway events to handler functions."""

import os
import re
import secrets
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import boto3
import ulid as ulid_mod

from api import auth
from api.http import parse_body, response

# Kept importable from here for tests and older call sites.
_parse_body = parse_body
_response = response

Handler = Callable[[dict[str, Any]], dict[str, Any]]


ROUTES: list[tuple[str, str, str]] = [
    ("POST", r"^/api/verify$", "handle_verify"),
    ("GET", r"^/api/session$", "handle_get_session"),
    ("POST", r"^/api/logout$", "handle_logout"),
    ("GET", r"^/api/media$", "handle_get_media"),
    ("GET", r"^/api/messages$", "handle_get_messages"),
    ("POST", r"^/api/messages$", "handle_post_message"),
    ("POST", r"^/api/messages/upload-url$", "handle_message_upload_url"),
    ("DELETE", r"^/api/messages/(?P<id>[^/]+)$", "handle_delete_message"),
    ("GET", r"^/api/admin/tokens$", "handle_get_tokens"),
    ("POST", r"^/api/admin/tokens$", "handle_post_token"),
    ("DELETE", r"^/api/admin/tokens/(?P<uuid>[^/]+)$", "handle_delete_token"),
    ("POST", r"^/api/admin/media/upload-url$", "handle_upload_url"),
    ("POST", r"^/api/admin/media$", "handle_post_media"),
    ("DELETE", r"^/api/admin/media/(?P<id>[^/]+)$", "handle_delete_media"),
    ("PUT", r"^/api/admin/media/(?P<id>[^/]+)$", "handle_put_media"),
]


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Main Lambda entry point — routes requests to handler functions."""
    method = str(event.get("httpMethod", ""))
    path = str(event.get("path", "")).rstrip("/")
    for route_method, pattern, handler_name in ROUTES:
        if route_method != method or not re.match(pattern, path):
            continue
        handler: Handler = globals()[handler_name]
        try:
            return handler(event)
        except Exception as e:
            print(f"Error handling {method} {path}: {type(e).__name__}: {e}")
            return _response(500, {"error": "Internal server error"})
    return _response(404, {"error": "Not found"})


# --- Auth ---


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
            return _response(
                200, {"message": "Authenticated"}, {"Set-Cookie": auth.make_session_cookie(jwt_token)}
            )
        return _response(403, {"error": "Invalid admin code"})

    # Check party code
    if code:
        if code.lower() == os.environ["PARTY_CODE"].lower():
            jwt_token = auth.create_jwt("guest")
            return _response(
                200, {"message": "Authenticated"}, {"Set-Cookie": auth.make_session_cookie(jwt_token)}
            )
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
        return _response(
            200, {"message": "Authenticated"}, {"Set-Cookie": auth.make_session_cookie(jwt_token)}
        )

    return _response(400, {"error": "Provide 'code' or 'token'"})


def handle_get_session(event):
    session = auth.get_session_from_event(event)
    if not session:
        return _response(401, {"error": "Unauthorized"})
    return _response(200, {"role": session.get("role", "guest")})


def handle_logout(event):
    return _response(
        200,
        {"message": "Logged out"},
        {"Set-Cookie": "session=; HttpOnly; Secure; Path=/; Max-Age=0; SameSite=Strict"},
    )


# --- Messages ---


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
    cf_domain = os.environ["CLOUDFRONT_DOMAIN"]
    messages = []
    for item in result.get("Items", []):
        msg = {
            "id": item["SK"].split("#")[1],
            "author": item["author"],
            "text": item["text"],
            "createdAt": item["createdAt"],
        }
        if item.get("photoKey"):
            msg["photoUrl"] = f"https://{cf_domain}/{item['photoKey']}"
        messages.append(msg)
    return _response(200, {"messages": messages})


def handle_post_message(event):
    session = auth.require_auth(event)
    if not session:
        return _response(401, {"error": "Unauthorized"})

    body = _parse_body(event)
    if not body or not body.get("author") or not body.get("text"):
        return _response(400, {"error": "Provide 'author' and 'text'"})

    message_id = str(ulid_mod.new())
    now = datetime.now(UTC).isoformat()

    item = {
        "PK": "MSG",
        "SK": f"MSG#{message_id}",
        "author": body["author"],
        "text": body["text"],
        "createdAt": now,
    }
    if body.get("photoKey"):
        item["photoKey"] = body["photoKey"]

    table = auth.get_dynamodb_table()
    table.put_item(Item=item)
    return _response(201, {"id": message_id, "createdAt": now})


_ALLOWED_UPLOAD_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "video/mp4"}


def handle_message_upload_url(event):
    session = auth.require_auth(event)
    if not session:
        return _response(401, {"error": "Unauthorized"})

    body = _parse_body(event)
    if not body or not body.get("filename") or not body.get("contentType"):
        return _response(400, {"error": "Provide 'filename' and 'contentType'"})

    if body["contentType"] not in _ALLOWED_UPLOAD_TYPES:
        return _response(400, {"error": "Unsupported content type"})

    ext = body["filename"].rsplit(".", 1)[-1] if "." in body["filename"] else ""
    s3_key = f"message-photos/{ulid_mod.new()}.{ext}" if ext else f"message-photos/{ulid_mod.new()}"

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


def handle_delete_message(event):
    session = auth.require_auth(event, role="admin")
    if not session:
        return _response(401, {"error": "Unauthorized"})

    path = event.get("path", "")
    message_id = path.split("/")[-1]

    table = auth.get_dynamodb_table()
    table.delete_item(Key={"PK": "MSG", "SK": f"MSG#{message_id}"})
    return _response(200, {"message": "Deleted"})


# --- Media ---


def handle_get_media(event):
    session = auth.require_auth(event)
    if not session:
        return _response(401, {"error": "Unauthorized"})

    table = auth.get_dynamodb_table()
    result = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": "MEDIA"},
    )
    cf_domain = os.environ["CLOUDFRONT_DOMAIN"]
    media = []
    for item in sorted(result.get("Items", []), key=lambda x: x.get("order", 0)):
        media.append(
            {
                "id": item["SK"].split("#")[1],
                "url": f"https://{cf_domain}/{item['s3Key']}",
                "type": item.get("type", "photo"),
                "caption": item.get("caption", ""),
                "order": item.get("order", 0),
                "createdAt": item.get("createdAt", ""),
            }
        )
    return _response(200, {"media": media})


def handle_upload_url(event):
    session = auth.require_auth(event, role="admin")
    if not session:
        return _response(401, {"error": "Unauthorized"})

    body = _parse_body(event)
    if not body or not body.get("filename") or not body.get("contentType"):
        return _response(400, {"error": "Provide 'filename' and 'contentType'"})

    if body["contentType"] not in _ALLOWED_UPLOAD_TYPES:
        return _response(400, {"error": "Unsupported content type"})

    ext = body["filename"].rsplit(".", 1)[-1] if "." in body["filename"] else ""
    s3_key = f"media/{ulid_mod.new()}.{ext}" if ext else f"media/{ulid_mod.new()}"

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

    media_id = str(ulid_mod.new())
    now = datetime.now(UTC).isoformat()

    table = auth.get_dynamodb_table()
    table.put_item(
        Item={
            "PK": "MEDIA",
            "SK": f"MEDIA#{media_id}",
            "s3Key": body["s3Key"],
            "type": body["type"],
            "caption": body.get("caption", ""),
            "order": body.get("order", 0),
            "createdAt": now,
        }
    )
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


# --- Admin Tokens ---


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

    body = _parse_body(event)
    label = body.get("label", "") if body else ""
    expires_in_days = body.get("expiresInDays", 7) if body else 7

    token_uuid = secrets.token_hex(4)
    now = datetime.now(UTC).isoformat()
    expires_at = int(time.time()) + (expires_in_days * 86400)

    table = auth.get_dynamodb_table()
    table.put_item(
        Item={
            "PK": "TOKEN",
            "SK": f"TOKEN#{token_uuid}",
            "expiresAt": expires_at,
            "label": label,
            "createdAt": now,
        }
    )

    cf_domain = os.environ["CLOUDFRONT_DOMAIN"]
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


# --- Helpers ---
