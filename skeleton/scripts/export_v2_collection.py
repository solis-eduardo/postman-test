#!/usr/bin/env python3
"""
Exporta a collection v3 (git-native, YAML por request) de volta para um único
arquivo JSON no formato clássico v2.1 (`postman_collection.json`).

Por quê: alguns recursos do Postman ainda não suportam collections v3
"multi-protocol" (git-native) — ex.: "Publish docs" retorna "Publish support
for multi-protocol collections coming soon". O botão "Run in Postman" também
precisa de um único arquivo JSON acessível por URL, não de uma árvore de
arquivos. Este script gera esse espelho v2.1 a partir da v3 (fonte de
verdade), para publicar/importar onde o v3 ainda não é aceito.

O arquivo gerado fica em `dist/`, fora de `postman/`, de propósito: um JSON
v2.1 solto dentro de `postman/collections/` seria tratado pelo Postman
Desktop como um arquivo legado precisando de conversão (mesmo comportamento
visto com os ambientes) e bagunçaria o Local View.

Config: lê COLLECTION_NAME de postman-fern.env (raiz do projeto).

Uso:
    python3 scripts/export_v2_collection.py
    (escreve dist/<COLLECTION_NAME>.postman_collection.json)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

from _env import load_env

ROOT = Path(__file__).resolve().parent.parent
load_env(ROOT)

COLLECTION_DIR = ROOT / "postman" / "collections" / os.environ["COLLECTION_NAME"]
OUT_PATH = ROOT / "dist" / f"{os.environ['COLLECTION_NAME']}.postman_collection.json"

SCRIPT_TYPE_MAP = {
    "beforeRequest": "prerequest",
    "afterResponse": "test",
    "http:beforeRequest": "prerequest",
    "http:afterResponse": "test",
}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def scripts_to_events(scripts: list[dict]) -> list[dict]:
    events = []
    for s in scripts or []:
        listen = SCRIPT_TYPE_MAP.get(s["type"], s["type"])
        events.append({
            "listen": listen,
            "script": {
                "type": s.get("language", "text/javascript"),
                "exec": s["code"].split("\n"),
            },
        })
    return events


def auth_to_v2(auth_list: list[dict]) -> dict | None:
    if not auth_list:
        return None
    a = auth_list[0]
    if a["type"] == "bearer":
        return {"type": "bearer", "bearer": [{"key": "token", "value": a["credentials"]["token"], "type": "string"}]}
    # outros tipos de auth (basic, apikey, oauth2...): adicione o mapeamento aqui se precisar.
    return {"type": a["type"]}


def build_examples(examples_dir: Path) -> list[dict]:
    if not examples_dir.exists():
        return []
    responses = []
    files = sorted(examples_dir.glob("*.example.yaml"), key=lambda p: load_yaml(p).get("order", 0))
    for f in files:
        ex = load_yaml(f)
        name = f.name[: -len(".example.yaml")]
        resp = ex["response"]
        headers = [{"key": k, "value": v} for k, v in (resp.get("headers") or {}).items()]
        responses.append({
            "name": name,
            "originalRequest": {
                "method": ex["request"]["method"],
                "url": {"raw": ex["request"]["url"]},
            },
            "status": resp.get("statusText", ""),
            "code": resp.get("statusCode"),
            "_postman_previewlanguage": (resp.get("body") or {}).get("type", "json"),
            "header": headers,
            "body": (resp.get("body") or {}).get("content", ""),
        })
    return responses


def build_request_item(request_file: Path) -> dict:
    data = load_yaml(request_file)
    name = request_file.name[: -len(".request.yaml")]

    request: dict = {
        "method": data["method"],
        "header": [{"key": k, "value": v} for k, v in (data.get("headers") or {}).items()],
        "url": {"raw": data["url"]},
    }
    if data.get("description"):
        request["description"] = data["description"]
    if data.get("body"):
        request["body"] = {"mode": "raw", "raw": data["body"]["content"]}

    item: dict = {"name": name, "request": request}

    events = scripts_to_events(data.get("scripts") or [])
    if events:
        item["event"] = events

    examples_rel = data.get("examples")
    if examples_rel:
        examples_dir = (request_file.parent / examples_rel).resolve()
        responses = build_examples(examples_dir)
        if responses:
            item["response"] = responses

    return item, data.get("order", 0)


def build_folder_items(folder_dir: Path) -> list[dict]:
    entries = []  # (order, item_dict)

    for sub in sorted(p for p in folder_dir.iterdir() if p.is_dir() and p.name != ".resources"):
        sub_def_path = sub / ".resources" / "definition.yaml"
        sub_def = load_yaml(sub_def_path) if sub_def_path.exists() else {}
        folder_item: dict = {"name": sub.name, "item": build_folder_items(sub)}
        if sub_def.get("description"):
            folder_item["description"] = sub_def["description"]
        entries.append((sub_def.get("order", 0), folder_item))

    for request_file in folder_dir.glob("*.request.yaml"):
        item, order = build_request_item(request_file)
        entries.append((order, item))

    entries.sort(key=lambda pair: pair[0])
    return [item for _, item in entries]


def main() -> int:
    if not COLLECTION_DIR.exists():
        print(f"Collection não encontrada em {COLLECTION_DIR}", file=sys.stderr)
        return 2

    root_def = load_yaml(COLLECTION_DIR / ".resources" / "definition.yaml")

    collection = {
        "info": {
            "name": root_def["name"],
            "description": root_def.get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": build_folder_items(COLLECTION_DIR),
    }

    auth = auth_to_v2(root_def.get("auth") or [])
    if auth:
        collection["auth"] = auth

    events = scripts_to_events(root_def.get("scripts") or [])
    if events:
        collection["event"] = events

    variables = root_def.get("variables") or {}
    if variables:
        collection["variable"] = [{"key": k, "value": v} for k, v in variables.items()]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(collection, ensure_ascii=False, indent=2), encoding="utf-8")

    n_requests = sum(1 for _ in COLLECTION_DIR.rglob("*.request.yaml"))
    print(f"OK: {n_requests} requisições exportadas para {OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
