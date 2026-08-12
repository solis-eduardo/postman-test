"""Carrega postman-fern.env (raiz do projeto) pra os scripts Python deste kit.
Não precisa de dependência extra -- parser simples de KEY=value.
"""
from __future__ import annotations

import os
from pathlib import Path


def load_env(root: Path) -> None:
    env_file = root / "postman-fern.env"
    if not env_file.exists():
        raise SystemExit(
            f"postman-fern.env não encontrado em {root}. "
            "Copie postman-fern.env.example pra postman-fern.env e preencha os valores."
        )
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        # Valores com espaço vêm entre aspas duplas no arquivo (exigido pro
        # `source` do bash não quebrar) -- remove as aspas aqui também.
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)

    if not os.environ.get("COLLECTION_NAME"):
        raise SystemExit("COLLECTION_NAME não definido em postman-fern.env")
