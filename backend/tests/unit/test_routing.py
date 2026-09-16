from api import app


def test_unknown_route_returns_404(make_event):
    event = make_event("GET", "/api/unknown")
    result = app.lambda_handler(event, None)
    assert result["statusCode"] == 404


def test_verify_route_exists(make_event):
    event = make_event("POST", "/api/verify", body={"code": "test"})
    result = app.lambda_handler(event, None)
    # Route exists — returns 403 for invalid code (not 404)
    assert result["statusCode"] == 403
