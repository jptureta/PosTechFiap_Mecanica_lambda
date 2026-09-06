import json

from src.handler import lambda_handler


def test_lambda_handler_returns_healthcheck_response(monkeypatch):
    monkeypatch.setenv("AWS_REQUEST_ID", "request-123")

    response = lambda_handler({}, None)
    payload = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["X-Request-ID"] == "request-123"
    assert payload["event"] == "lambda_healthcheck"
    assert payload["service"] == "oficina-mecanica-lambda"
    assert payload["status"] == "ok"