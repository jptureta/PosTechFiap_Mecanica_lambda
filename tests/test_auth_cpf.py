import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from handler import lambda_handler

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

_CPF_VALIDO = "529.982.247-25"  # CPF matematicamente válido para testes


def _event_auth(cpf: str) -> dict:
    """Monta um evento de API Gateway HTTP para POST /auth/cpf."""
    return {
        "rawPath": "/auth/cpf",
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps({"cpf": cpf}),
    }


def _event_health() -> dict:
    return {
        "rawPath": "/health",
        "requestContext": {"http": {"method": "GET"}},
    }


# ─────────────────────────────────────────────────────────────
# Healthcheck (mantido do comportamento original)
# ─────────────────────────────────────────────────────────────

def test_healthcheck_retorna_ok():
    response = lambda_handler(_event_health(), None)
    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert payload["status"] == "ok"
    assert payload["service"] == "oficina-mecanica-lambda"


# ─────────────────────────────────────────────────────────────
# Autenticação por CPF — cenários de erro
# ─────────────────────────────────────────────────────────────

def test_cpf_ausente_retorna_400():
    event = {
        "rawPath": "/auth/cpf",
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps({}),
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400


def test_corpo_invalido_retorna_400():
    event = {
        "rawPath": "/auth/cpf",
        "requestContext": {"http": {"method": "POST"}},
        "body": "not-json",
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400


def test_cpf_invalido_retorna_422():
    response = lambda_handler(_event_auth("11111111111"), None)
    assert response["statusCode"] == 422
    assert "inválido" in json.loads(response["body"])["detail"]


def test_cpf_nao_encontrado_retorna_404():
    with patch("handler.buscar_cliente_por_cpf", return_value=None):
        response = lambda_handler(_event_auth(_CPF_VALIDO), None)
    assert response["statusCode"] == 404


def test_cliente_inativo_retorna_403():
    cliente_inativo = {"id": 1, "nome": "João Silva", "ativo": False}
    with patch("handler.buscar_cliente_por_cpf", return_value=cliente_inativo):
        response = lambda_handler(_event_auth(_CPF_VALIDO), None)
    assert response["statusCode"] == 403


def test_erro_banco_retorna_503():
    with patch("handler.buscar_cliente_por_cpf", side_effect=Exception("connection refused")):
        response = lambda_handler(_event_auth(_CPF_VALIDO), None)
    assert response["statusCode"] == 503


# ─────────────────────────────────────────────────────────────
# Autenticação por CPF — cenário de sucesso
# ─────────────────────────────────────────────────────────────

def test_autenticacao_sucesso_retorna_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-pytest")
    cliente_ativo = {"id": 42, "nome": "Maria Souza", "ativo": True}

    with patch("handler.buscar_cliente_por_cpf", return_value=cliente_ativo):
        response = lambda_handler(_event_auth(_CPF_VALIDO), None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20  # token JWT não é vazio


def test_token_gerado_contem_claims_corretos(monkeypatch):
    """Verifica que o JWT contém o CPF e o tipo 'cliente'."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-pytest")
    cliente_ativo = {"id": 42, "nome": "Maria Souza", "ativo": True}

    with patch("handler.buscar_cliente_por_cpf", return_value=cliente_ativo):
        response = lambda_handler(_event_auth(_CPF_VALIDO), None)

    token = json.loads(response["body"])["access_token"]

    from jose import jwt
    payload = jwt.decode(token, "test-secret-key-for-pytest", algorithms=["HS256"])
    assert payload["sub"] == "52998224725"   # CPF normalizado
    assert payload["tipo"] == "cliente"
    assert payload["cliente_id"] == 42
    assert payload["nome"] == "Maria Souza"


def test_cpf_com_formatacao_e_aceito(monkeypatch):
    """CPF com pontos e traço deve ser aceito e normalizado."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-pytest")
    cliente_ativo = {"id": 1, "nome": "Pedro", "ativo": True}

    with patch("handler.buscar_cliente_por_cpf", return_value=cliente_ativo) as mock_db:
        response = lambda_handler(_event_auth("529.982.247-25"), None)
        # confirma que o CPF foi normalizado antes de consultar o BD
        mock_db.assert_called_once_with("52998224725")

    assert response["statusCode"] == 200

