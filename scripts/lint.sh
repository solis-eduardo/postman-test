#!/usr/bin/env bash
# Valida a collection Postman (formato v3 / git-native) e a especificação OpenAPI.
#
# Requer:
#   - Postman CLI: https://learning.postman.com/docs/postman-cli/postman-cli-installation/
#     (ou `npm install postman-cli` e usar via npx, como abaixo)
#
# Uso:
#   ./scripts/lint.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COLLECTION_DIR="$ROOT_DIR/.postman/collections/PetVerse API"

echo "==> Lint da collection (v3 / git-native): $COLLECTION_DIR"
npx --yes postman-cli collection lint "$COLLECTION_DIR"

echo "==> Validação da especificação OpenAPI: specs/openapi.yaml"
npx --yes @redocly/cli lint "$ROOT_DIR/specs/openapi.yaml" || \
  npx --yes @apidevtools/swagger-cli validate "$ROOT_DIR/specs/openapi.yaml"

echo "==> OK: collection e spec válidas."
