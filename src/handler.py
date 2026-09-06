import json
import os
import time
from datetime import datetime, timezone

try:
    from datadog import statsd
except Exception:  # pragma: no cover - opcional em ambientes sem Datadog
    statsd = None


def _emit_metric(name: str, value: float = 1, tags=None):
    if statsd is None:
        return
    try:
        statsd.increment(name, value=value, tags=tags or [])
    except Exception:
        pass


def lambda_handler(event, context):
    started_at = time.time()
    status_code = 200

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
    return {
        "statusCode": status_code,
        "body": json.dumps(payload),
        "headers": {"Content-Type": "application/json", "X-Request-ID": os.getenv("AWS_REQUEST_ID", "lambda-local")},
    }
