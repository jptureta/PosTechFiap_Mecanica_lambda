import os
from datetime import datetime, timedelta, timezone

from jose import jwt


def criar_token_cpf(cpf: str, cliente_id: int, nome: str) -> str:
    """
    Gera um token JWT para um cliente autenticado via CPF.

    O token usa a mesma JWT_SECRET_KEY e JWT_ALGORITHM configurados
    na API principal (app-k8s), garantindo interoperabilidade.

    Claims:
        sub         — CPF normalizado (somente dígitos), identidade do cliente
        cliente_id  — ID do cliente no banco de dados
        nome        — nome do cliente (para exibição no front-end)
        tipo        — "cliente" (distingue de tokens de usuário admin)
        exp         — expiração conforme JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    """
    secret = os.environ["JWT_SECRET_KEY"]
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    expire_minutes = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    payload = {
        "sub": cpf,
        "cliente_id": cliente_id,
        "nome": nome,
        "tipo": "cliente",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expire_minutes),
    }

    return jwt.encode(payload, secret, algorithm=algorithm)

