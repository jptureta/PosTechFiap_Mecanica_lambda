import json
import os
import time
from datetime import datetime, timezone

try:
    from datadog import statsd
except Exception:  # pragma: no cover - opcional em ambientes sem Datadog
    statsd = None

from cpf_validator import validar_cpf, normalizar_cpf
from db_client import buscar_cliente_por_cpf
from token_service import criar_token_cpf


# ─────────────────────────────────────────────────────────────
# Utilitários internos
# ─────────────────────────────────────────────────────────────

def _emit_metric(name: str, value: float = 1, tags=None):
    if statsd is None:
        return
    try:
        statsd.increment(name, value=value, tags=tags or [])
    except Exception:
        pass


def _json_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "body": json.dumps(body, ensure_ascii=False),
        "headers": {
            "Content-Type": "application/json",
            "X-Request-ID": os.getenv("AWS_REQUEST_ID", "lambda-local"),
        },
    }


def _error(status_code: int, detail: str) -> dict:
    return _json_response(status_code, {"detail": detail})


# ─────────────────────────────────────────────────────────────
# Handler: Healthcheck (rota GET /health)
# ─────────────────────────────────────────────────────────────

def _healthcheck_handler(event, context) -> dict:
    started_at = time.time()

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "lambda_healthcheck",
        "service": "oficina-mecanica-lambda",
        "status": "ok",
        "message": "Oficina Mecânica Lambda funcionando",
    }

    _emit_metric("oficina.lambda.requests", tags=["service:oficina-mecanica-lambda", "status:200"])
    _emit_metric(
        "oficina.lambda.latency_ms",
        value=max(0, round((time.time() - started_at) * 1000, 2)),
        tags=["service:oficina-mecanica-lambda"],
    )

    print(json.dumps(payload, separators=(",", ":")))
    return _json_response(200, payload)


# ─────────────────────────────────────────────────────────────
# Handler: Autenticação por CPF (rota POST /auth/cpf)
# ─────────────────────────────────────────────────────────────

def _auth_cpf_handler(event, context) -> dict:
    # 1. Extrair CPF do corpo da requisição
    try:
        body = json.loads(event.get("body") or "{}")
        cpf_raw = body.get("cpf", "")
    except (json.JSONDecodeError, AttributeError):
        return _error(400, "Corpo da requisição inválido — esperado JSON com campo 'cpf'")

    if not cpf_raw:
        return _error(400, "Campo 'cpf' é obrigatório")

    # 2. Normalizar e validar o CPF
    cpf = normalizar_cpf(cpf_raw)
    if not validar_cpf(cpf):
        return _error(422, "CPF inválido")

    # 3. Consultar o cliente na base de dados
    try:
        cliente = buscar_cliente_por_cpf(cpf)
    except Exception as exc:
        print(json.dumps({"event": "db_error", "error": str(exc)}))
        return _error(503, "Serviço temporariamente indisponível")

    if cliente is None:
        return _error(404, "Cliente não encontrado")

    if not cliente["ativo"]:
        return _error(403, "Cliente inativo — entre em contato com a oficina")

    # 4. Gerar token JWT
    try:
        token = criar_token_cpf(cpf, cliente["id"], cliente["nome"])
    except Exception as exc:
        print(json.dumps({"event": "token_error", "error": str(exc)}))
        return _error(500, "Erro ao gerar token de acesso")

    _emit_metric("oficina.lambda.auth.sucesso", tags=["service:oficina-mecanica-lambda"])
    return _json_response(200, {"access_token": token, "token_type": "bearer"})


# ─────────────────────────────────────────────────────────────
# Dispatcher principal
# ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    """
    Entry point da Lambda. Despacha para o handler correto com base no path.

    Rotas:
        GET  /health    → healthcheck (pública)
        POST /auth/cpf  → autenticação por CPF (pública, retorna JWT)
    """
    path = (event.get("rawPath") or event.get("path") or "/health").rstrip("/")
    method = (event.get("requestContext", {}).get("http", {}).get("method") or
              event.get("httpMethod") or "GET").upper()

    if path.endswith("/auth/cpf") and method == "POST":
        return _auth_cpf_handler(event, context)

    return _healthcheck_handler(event, context)
