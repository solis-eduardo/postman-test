#!/usr/bin/env python3
"""
Verifica que a especificação OpenAPI (postman/specs/openapi.yaml) e a collection
Postman v3 (postman/collections/PetVerse API/**/*.request.yaml) descrevem os
mesmos endpoints — nem a mais, nem a menos.

Por quê: nada impede alguém de editar só a collection (adicionar uma requisição
nova pela UI do Postman) ou só a spec (adicionar um path no OpenAPI) e esquecer
do outro lado. Esse script fecha esse gap localmente, sem depender de nenhuma
feature de nuvem do Postman — dá pra rodar no CI (ver .github/workflows/api-tests.yml).

Requer: PyYAML (`pip install pyyaml`).

Uso:
    python3 scripts/check_spec_alignment.py
    (exit code 0 = alinhado, 1 = divergências encontradas)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "postman" / "specs" / "openapi.yaml"
COLLECTION_DIR = ROOT / "postman" / "collections" / "PetVerse API"

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}

# Variáveis de collection que resolvem para valores fixos conhecidos, usadas
# para normalizar a URL de cada requisição para o mesmo formato dos paths da
# spec (que não usam {{base_url}}/{{api_version}}, só o path puro).
KNOWN_COLLECTION_VARS = {
    "base_url": "",       # removido: a spec não inclui host
    "api_version": "v1",  # spec usa "v1" literal no path
}


def load_spec_endpoints(spec_path: Path) -> set[tuple[str, str]]:
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    endpoints = set()
    for path, path_item in (spec.get("paths") or {}).items():
        for key, operation in path_item.items():
            if key.lower() in HTTP_METHODS:
                endpoints.add((key.upper(), normalize_path(path)))
    return endpoints


def normalize_path(raw: str) -> str:
    """Normaliza um path para comparação: remove barra final, mantém {param}."""
    path = raw.strip()
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


def resolve_request_url(url_field) -> str:
    """
    O campo `url` de um *.request.yaml pode ser uma string simples
    ("{{base_url}}/{{api_version}}/pets") ou (em outras collections) um
    objeto estruturado. Aqui tratamos o caso string, que é o usado nesta
    collection.
    """
    if isinstance(url_field, dict):
        url_field = url_field.get("raw", "")
    return str(url_field or "")


def normalize_collection_url(raw_url: str) -> str:
    url = raw_url.split("?", 1)[0]  # remove query string

    def replace_var(match: re.Match) -> str:
        name = match.group(1)
        return KNOWN_COLLECTION_VARS.get(name, match.group(0))

    url = re.sub(r"\{\{(\w+)\}\}", replace_var, url)

    # remove esquema/host se por acaso vier resolvido (não é o caso aqui, mas
    # deixa o normalizador robusto a URLs absolutas também)
    url = re.sub(r"^https?://[^/]+", "", url)

    # :paramName -> {paramName}, no padrão do OpenAPI
    url = re.sub(r":(\w+)", r"{\1}", url)

    return normalize_path(url)


def load_collection_endpoints(collection_dir: Path) -> set[tuple[str, str]]:
    endpoints = set()
    for request_file in collection_dir.rglob("*.request.yaml"):
        data = yaml.safe_load(request_file.read_text(encoding="utf-8"))
        if not data or data.get("$kind") != "http-request":
            continue
        method = str(data.get("method", "")).upper()
        url = normalize_collection_url(resolve_request_url(data.get("url")))
        endpoints.add((method, url))
    return endpoints


def main() -> int:
    if not SPEC_PATH.exists():
        print(f"Spec não encontrada em {SPEC_PATH}", file=sys.stderr)
        return 2
    if not COLLECTION_DIR.exists():
        print(f"Collection não encontrada em {COLLECTION_DIR}", file=sys.stderr)
        return 2

    spec_endpoints = load_spec_endpoints(SPEC_PATH)
    collection_endpoints = load_collection_endpoints(COLLECTION_DIR)

    missing_in_collection = sorted(spec_endpoints - collection_endpoints)
    missing_in_spec = sorted(collection_endpoints - spec_endpoints)

    if not missing_in_collection and not missing_in_spec:
        print(f"OK: {len(spec_endpoints)} endpoints. Spec e collection estão alinhadas.")
        return 0

    if missing_in_collection:
        print("Endpoints na spec SEM requisição correspondente na collection:")
        for method, path in missing_in_collection:
            print(f"  - {method} {path}")

    if missing_in_spec:
        print("Requisições na collection SEM path/operation correspondente na spec:")
        for method, path in missing_in_spec:
            print(f"  - {method} {path}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
