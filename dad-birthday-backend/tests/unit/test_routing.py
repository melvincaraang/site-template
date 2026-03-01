import json
from api import app


def test_unknown_route_returns_404(make_event):
    event = make_event("GET", "/unknown")
    result = app.lambda_handler(event, None)
    assert result["statusCode"] == 404


def test_verify_route_exists(make_event):
    event = make_event("POST", "/verify", body={"code": "test"})
    result = app.lambda_handler(event, None)
    # 501 means routed correctly but not implemented yet
    assert result["statusCode"] == 501
