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

        event = make_event("GET", "/api/messages", headers={"Cookie": _auth_cookie()})
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        data = json.loads(result["body"])
        assert len(data["messages"]) == 1
        assert data["messages"][0]["author"] == "Alice"

    def test_unauthenticated_returns_401(self, make_event):
        event = make_event("GET", "/api/messages")
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 401


class TestPostMessage:
    @patch("api.auth.get_dynamodb_table")
    def test_creates_message(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        event = make_event(
            "POST", "/api/messages",
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
            "POST", "/api/messages",
            body={"author": "Bob"},
            headers={"Cookie": _auth_cookie()},
        )
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 400
