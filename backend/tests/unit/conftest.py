import json
import os

import pytest

# Set env vars before importing app
os.environ["TABLE_NAME"] = "TestTable"
os.environ["MEDIA_BUCKET"] = "test-media-bucket"
os.environ["PARTY_CODE"] = "test-party-code"
os.environ["ADMIN_CODE"] = "test-admin-code"
os.environ["JWT_SECRET"] = "test-jwt-secret-key"
os.environ["CLOUDFRONT_DOMAIN"] = "example.com"


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
