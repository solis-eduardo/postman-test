#!/usr/bin/env python3
"""
Verifica que a especificação OpenAPI (postman/specs/openapi.yaml) e a collection
Postman v3 (postman/collections/PetVerse API/**/*.request.yaml) descrevem a
mesma API em três frentes:

  1. Endpoints  — todo METHOD+path existe dos dois lados (nem a mais, nem a menos).
  2. Tags       — a pasta que contém a requisição na collection bate com a(s)
                  tag(s) da operação correspondente na spec (a Fern usa as tags
                  da spec pra montar a navegação do site publicado; a collection
                  usa pastas — os dois são editados separadamente e nada
                  sincroniza um pro outro, então isso pode divergir em silêncio).
  3. Schema     — o corpo de requisição (e de cada resposta de exemplo salva)
                  na collection valida contra o `requestBody`/`responses` da
                  spec (JSON Schema, com $ref resolvido dentro da própria spec).

Por quê: nada impede alguém de editar só a collection (adicionar/renomear algo
pela UI do Postman) ou só a spec (mudar um path, uma tag, um schema) e esquecer
do outro lado. Esse script fecha esse gap localmente, sem depender de nenhuma
feature de nuvem do Postman — dá pra rodar no CI (ver .github/workflows/api-tests.yml).

Requer: PyYAML + jsonschema (`pip install pyyaml jsonschema`).

Uso:
    python3 scripts/check_spec_alignment.py
    (exit code 0 = tudo alinhado, 1 = alguma divergência encontrada, 2 = erro de setup)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema
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

Endpoint = tuple[str, str]  # (METHOD, /path/normalizado)


def normalize_path(raw: str) -> str:
    """Normaliza um path para comparação: remove barra final, mantém {param}."""
    path = raw.strip()
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


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


def try_parse_json(raw: str | None) -> object | None:
    """Faz parse best-effort; retorna None se não for JSON (ex.: corpo vazio,
    texto puro, XML) -- schemas só são checados quando dá pra interpretar."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def load_spec(spec_path: Path) -> tuple[dict, dict[Endpoint, dict]]:
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    operations: dict[Endpoint, dict] = {}
    for path, path_item in (spec.get("paths") or {}).items():
        for method, operation in path_item.items():
            if method.lower() in HTTP_METHODS:
                operations[(method.upper(), normalize_path(path))] = operation
    return spec, operations


def load_examples(request_file: Path, examples_rel: str | None) -> list[dict]:
    if not examples_rel:
        return []
    examples_dir = (request_file.parent / examples_rel).resolve()
    if not examples_dir.exists():
        return []
    examples = []
    for ex_file in sorted(examples_dir.glob("*.example.yaml")):
        ex = yaml.safe_load(ex_file.read_text(encoding="utf-8")) or {}
        response = ex.get("response") or {}
        body = (response.get("body") or {}).get("content")
        examples.append({
            "file": ex_file,
            "status": response.get("statusCode"),
            "body_json": try_parse_json(body),
        })
    return examples


def load_collection(collection_dir: Path) -> dict[Endpoint, dict]:
    requests: dict[Endpoint, dict] = {}
    for request_file in collection_dir.rglob("*.request.yaml"):
        data = yaml.safe_load(request_file.read_text(encoding="utf-8"))
        if not data or data.get("$kind") != "http-request":
            continue
        method = str(data.get("method", "")).upper()
        url = normalize_collection_url(resolve_request_url(data.get("url")))
        body_content = (data.get("body") or {}).get("content")
        requests[(method, url)] = {
            "file": request_file,
            "folder": request_file.parent.name,
            "body_json": try_parse_json(body_content),
            "examples": load_examples(request_file, data.get("examples")),
        }
    return requests


TEMPLATE_RE = re.compile(r"^\{\{[^{}]+\}\}$")  # ex.: "{{pet_species}}" -- variável Postman ainda não resolvida


def resolve_schema(schema: dict, resolver: jsonschema.RefResolver) -> dict:
    if "$ref" in schema:
        _, resolved = resolver.resolve(schema["$ref"])
        return resolved
    return schema


def dummy_value_for(prop_schema: dict, resolver: jsonschema.RefResolver) -> object:
    """Valor mínimo que satisfaz o tipo/enum declarado, pra usar no lugar de
    uma variável Postman ({{var}}) ainda não resolvida -- não valida o valor
    real (impossível saber em lint-time), só evita falso-positivo de
    tipo/enum enquanto ainda pega campo errado/faltando/extra."""
    prop_schema = resolve_schema(prop_schema, resolver)
    if "enum" in prop_schema:
        return prop_schema["enum"][0]
    type_ = prop_schema.get("type")
    return {
        "integer": 0,
        "number": 0.0,
        "boolean": True,
        "array": [],
        "object": {},
    }.get(type_, "valor-de-exemplo")  # string cobre também format: date/date-time/email


def substitute_templates(instance: object, schema: dict, resolver: jsonschema.RefResolver) -> object:
    """Troca strings que são só um placeholder `{{var}}` por um valor
    compatível com o schema daquela propriedade, pra variáveis de collection
    ainda não resolvidas não virarem falso-positivo de tipo/enum."""
    schema = resolve_schema(schema, resolver)
    if not isinstance(instance, dict) or schema.get("type") != "object":
        return instance
    properties = schema.get("properties") or {}
    result = {}
    for key, value in instance.items():
        if isinstance(value, str) and TEMPLATE_RE.match(value) and key in properties:
            result[key] = dummy_value_for(properties[key], resolver)
        else:
            result[key] = value
    return result


def get_json_schema(operation: dict, *, response_status: str | None = None) -> dict | None:
    if response_status is None:
        container = operation.get("requestBody") or {}
    else:
        container = (operation.get("responses") or {}).get(response_status) or {}
    return ((container.get("content") or {}).get("application/json") or {}).get("schema")


def schema_errors(instance: object, schema: dict, resolver: jsonschema.RefResolver) -> list[str]:
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema, resolver=resolver)
    return [f"{'.'.join(str(p) for p in err.path) or '<raiz>'}: {err.message}"
            for err in validator.iter_errors(instance)]


def main() -> int:
    if not SPEC_PATH.exists():
        print(f"Spec não encontrada em {SPEC_PATH}", file=sys.stderr)
        return 2
    if not COLLECTION_DIR.exists():
        print(f"Collection não encontrada em {COLLECTION_DIR}", file=sys.stderr)
        return 2

    spec, spec_ops = load_spec(SPEC_PATH)
    collection_reqs = load_collection(COLLECTION_DIR)
    resolver = jsonschema.RefResolver(base_uri="", referrer=spec)

    spec_endpoints = set(spec_ops)
    collection_endpoints = set(collection_reqs)
    common = spec_endpoints & collection_endpoints

    missing_in_collection = sorted(spec_endpoints - collection_endpoints)
    missing_in_spec = sorted(collection_endpoints - spec_endpoints)

    tag_mismatches: list[str] = []
    request_body_errors: list[str] = []
    response_body_errors: list[str] = []

    for method, path in sorted(common):
        operation = spec_ops[(method, path)]
        req = collection_reqs[(method, path)]

        # 2. tags/agrupamento
        tags = operation.get("tags") or []
        if req["folder"] not in tags:
            tag_mismatches.append(
                f"  - {method} {path}: pasta na collection é \"{req['folder']}\", "
                f"mas a spec marca essa operação com tags {tags!r}"
            )

        # 3a. schema do corpo de requisição
        request_schema = get_json_schema(operation)
        if request_schema is not None and req["body_json"] is not None:
            instance = substitute_templates(req["body_json"], request_schema, resolver)
            for msg in schema_errors(instance, request_schema, resolver):
                request_body_errors.append(f"  - {method} {path} ({req['file'].name}): {msg}")

        # 3b. schema de cada resposta de exemplo salva
        for example in req["examples"]:
            status = str(example["status"]) if example["status"] is not None else None
            if status is None or example["body_json"] is None:
                continue
            response_schema = get_json_schema(operation, response_status=status)
            if response_schema is None:
                continue
            instance = substitute_templates(example["body_json"], response_schema, resolver)
            for msg in schema_errors(instance, response_schema, resolver):
                response_body_errors.append(
                    f"  - {method} {path} [{status}] ({example['file'].name}): {msg}"
                )

    problems = missing_in_collection or missing_in_spec or tag_mismatches \
        or request_body_errors or response_body_errors

    if not problems:
        print(f"OK: {len(common)} endpoints. Spec e collection alinhadas em "
              f"endpoints, tags e schema de body/response.")
        return 0

    if missing_in_collection:
        print("Endpoints na spec SEM requisição correspondente na collection:")
        for method, path in missing_in_collection:
            print(f"  - {method} {path}")

    if missing_in_spec:
        print("Requisições na collection SEM path/operation correspondente na spec:")
        for method, path in missing_in_spec:
            print(f"  - {method} {path}")

    if tag_mismatches:
        print("Pasta da collection não corresponde à(s) tag(s) da spec:")
        print("\n".join(tag_mismatches))

    if request_body_errors:
        print("Corpo de requisição da collection não bate com o schema da spec:")
        print("\n".join(request_body_errors))

    if response_body_errors:
        print("Exemplo de resposta salvo na collection não bate com o schema da spec:")
        print("\n".join(response_body_errors))

    return 1


if __name__ == "__main__":
    sys.exit(main())
