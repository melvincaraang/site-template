import json
import jwt
import os
from unittest.mock import patch, MagicMock

from api import app


class TestVerifyWithPartyCode:
    def test_valid_party_code_returns_200_with_cookie(self, make_event):
        event = make_event("POST", "/api/verify", body={"code": "test-party-code"})
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        assert "Set-Cookie" in result["headers"]

        # Decode JWT from cookie
        cookie = result["headers"]["Set-Cookie"]
        token = cookie.split("=")[1].split(";")[0]
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
        assert payload["role"] == "guest"

    def test_invalid_party_code_returns_403(self, make_event):
        event = make_event("POST", "/api/verify", body={"code": "wrong"})
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 403

    def test_missing_code_returns_400(self, make_event):
        event = make_event("POST", "/api/verify", body={})
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 400


class TestVerifyWithAdminCode:
    def test_admin_code_returns_admin_role(self, make_event):
        event = make_event("POST", "/api/verify", body={"code": "test-admin-code", "admin": True})
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

        event = make_event("POST", "/api/verify", body={"token": "abc-123"})
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 200

    @patch("api.auth.get_dynamodb_table")
    def test_invalid_uuid_token_returns_403(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_get_table.return_value = mock_table

        event = make_event("POST", "/api/verify", body={"token": "nonexistent"})
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 403
