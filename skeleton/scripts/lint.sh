#!/usr/bin/env bash
# Valida a collection Postman (formato v3 / git-native), a especificação OpenAPI,
# o alinhamento entre as duas (endpoints + tags + schema de body/response) e a
# config da Fern.
#
# Requer:
#   - Node.js 18+ (roda Postman CLI, Redocly e Fern CLI via npx)
#   - Python 3 + PyYAML + jsonschema (`pip install pyyaml jsonschema`)
#
# Uso:
#   ./scripts/lint.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=_load_env.sh
source "$ROOT_DIR/scripts/_load_env.sh"

COLLECTION_DIR="$ROOT_DIR/postman/collections/$COLLECTION_NAME"

echo "==> Lint da collection (v3 / git-native): $COLLECTION_DIR"
npx --yes postman-cli collection lint "$COLLECTION_DIR"

echo "==> Validação da especificação OpenAPI: postman/specs/openapi.yaml"
npx --yes @redocly/cli lint "$ROOT_DIR/postman/specs/openapi.yaml" || \
  npx --yes @apidevtools/swagger-cli validate "$ROOT_DIR/postman/specs/openapi.yaml"

echo "==> Verificando alinhamento spec <-> collection (endpoints, tags, schema)"
python3 "$ROOT_DIR/scripts/check_spec_alignment.py"

if [[ -d "$ROOT_DIR/fern" ]]; then
  echo "==> Validando config da Fern (fern/) e a definição da API que ela referencia"
  npx --yes fern-api check
fi

echo "==> OK: collection, spec e docs válidas e alinhadas."
