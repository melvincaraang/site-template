import json
import os
import time
from unittest.mock import MagicMock, patch

import jwt

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
                {
                    "PK": "MEDIA",
                    "SK": "MEDIA#01ABC",
                    "s3Key": "photos/family.jpg",
                    "type": "photo",
                    "caption": "Family photo",
                    "order": 1,
                    "createdAt": "2026-03-01T12:00:00Z",
                },
            ]
        }
        mock_get_table.return_value = mock_table

        event = make_event("GET", "/api/media", headers={"Cookie": _auth_cookie()})
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        data = json.loads(result["body"])
        assert len(data["media"]) == 1
        assert data["media"][0]["caption"] == "Family photo"
        assert "url" in data["media"][0]

    def test_unauthenticated_returns_401(self, make_event):
        event = make_event("GET", "/api/media")
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 401


class TestAdminUploadUrl:
    @patch("boto3.client")
    def test_returns_presigned_url(self, mock_boto_client, make_event):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/presigned"
        mock_boto_client.return_value = mock_s3

        event = make_event(
            "POST",
            "/api/admin/media/upload-url",
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
            "POST",
            "/api/admin/media/upload-url",
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
            "POST",
            "/api/admin/media",
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
            "DELETE",
            "/api/admin/media/01ABC",
            headers={"Cookie": _auth_cookie("admin")},
        )
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        mock_table.delete_item.assert_called_once()
