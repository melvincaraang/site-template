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

        event = make_event("GET", "/api/admin/tokens", headers={"Cookie": _auth_cookie()})
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        data = json.loads(result["body"])
        assert len(data["tokens"]) == 1

    def test_guest_cannot_list_tokens(self, make_event):
        event = make_event("GET", "/api/admin/tokens", headers={"Cookie": _auth_cookie("guest")})
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 401


class TestPostToken:
    @patch("api.auth.get_dynamodb_table")
    def test_creates_token(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        event = make_event(
            "POST", "/api/admin/tokens",
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
            "DELETE", "/api/admin/tokens/abc-123",
            headers={"Cookie": _auth_cookie()},
        )
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        mock_table.delete_item.assert_called_once()
