#!/usr/bin/env bash
# Executa a collection PetVerse API (formato v3 / git-native) via Postman CLI.
#
# Requer a Postman CLI instalada (ou disponível via `npx postman-cli`):
#   https://learning.postman.com/docs/postman-cli/postman-cli-installation/
#
# Uso:
#   ./scripts/run-collection.sh [ambiente] [reporter]
#
# Exemplos:
#   ./scripts/run-collection.sh                     # ambiente Local, reporter cli
#   ./scripts/run-collection.sh Staging              # ambiente Staging
#   ./scripts/run-collection.sh Development cli,junit
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${1:-Local}"
REPORTERS="${2:-cli}"

COLLECTION_DIR="$ROOT_DIR/.postman/collections/PetVerse API"
ENV_FILE="$ROOT_DIR/.postman/environments/${ENV_NAME}.postman_environment.json"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Ambiente '$ENV_NAME' não encontrado em .postman/environments/. Ambientes disponíveis:" >&2
  ls "$ROOT_DIR/.postman/environments" >&2
  exit 1
fi

echo "==> Rodando collection '$COLLECTION_DIR'"
echo "==> Ambiente: $ENV_FILE"
npx --yes postman-cli collection run "$COLLECTION_DIR" \
  --environment "$ENV_FILE" \
  --reporters "$REPORTERS"
