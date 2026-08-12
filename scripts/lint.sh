#!/usr/bin/env bash
# Valida a collection Postman (formato v3 / git-native), a especificação OpenAPI
# e o alinhamento entre as duas (mesmos endpoints dos dois lados).
#
# Requer:
#   - Postman CLI: https://learning.postman.com/docs/postman-cli/postman-cli-installation/
#     (ou `npm install postman-cli` e usar via npx, como abaixo)
#   - Python 3 + PyYAML (`pip install pyyaml`)
#
# Uso:
#   ./scripts/lint.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COLLECTION_DIR="$ROOT_DIR/postman/collections/PetVerse API"

echo "==> Lint da collection (v3 / git-native): $COLLECTION_DIR"
npx --yes postman-cli collection lint "$COLLECTION_DIR"

echo "==> Validação da especificação OpenAPI: postman/specs/openapi.yaml"
npx --yes @redocly/cli lint "$ROOT_DIR/postman/specs/openapi.yaml" || \
  npx --yes @apidevtools/swagger-cli validate "$ROOT_DIR/postman/specs/openapi.yaml"

echo "==> Verificando alinhamento spec <-> collection (mesmos endpoints dos dois lados)"
python3 "$ROOT_DIR/scripts/check_spec_alignment.py"

echo "==> OK: collection e spec válidas e alinhadas."
