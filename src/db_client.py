import os
from typing import Optional

import psycopg


def _get_connection() -> psycopg.Connection:
    """Abre uma conexão com o PostgreSQL usando variáveis de ambiente."""
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )


def buscar_cliente_por_cpf(cpf_normalizado: str) -> Optional[dict]:
    """
    Consulta a tabela `clientes` pelo CPF (apenas dígitos).

    Retorna um dict com {"id", "nome", "ativo"} ou None se não encontrado.
    """
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nome, ativo FROM clientes WHERE cpf_cnpj = %s LIMIT 1",
                (cpf_normalizado,),
            )
            row = cur.fetchone()

    if row is None:
        return None

    return {"id": row[0], "nome": row[1], "ativo": row[2]}

