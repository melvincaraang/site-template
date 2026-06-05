import json
import os
import time

import boto3
import jwt


def get_dynamodb_table():
    endpoint = os.environ.get("DYNAMODB_ENDPOINT")
    if endpoint:
        dynamodb = boto3.resource("dynamodb", endpoint_url=endpoint)
    else:
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
