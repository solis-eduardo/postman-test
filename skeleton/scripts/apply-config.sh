#!/usr/bin/env bash
# Aplica os valores de postman-fern.env em todo o kit de uma vez: renomeia as
# pastas placeholder (__COLLECTION_NAME__, __MOCK_SLUG__) e substitui os
# placeholders dentro do conteúdo dos arquivos (__COLLECTION_NAME__,
# __MOCK_SLUG__, __FERN_ORG__, __FERN_DOMAIN__). Rode uma vez, logo depois de
# preencher postman-fern.env (ver docs/SETUP.md).
#
# Idempotente: rodar de novo depois de já ter aplicado não quebra nada (as
# pastas/arquivos placeholder simplesmente não existem mais pra encontrar).
#
# Uso:
#   bash scripts/apply-config.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/postman-fern.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "::error::postman-fern.env não encontrado. Copie postman-fern.env.example pra postman-fern.env e preencha antes de rodar isto." >&2
  exit 2
fi

set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

: "${COLLECTION_NAME:?defina COLLECTION_NAME em postman-fern.env}"
: "${MOCK_SLUG:?defina MOCK_SLUG em postman-fern.env}"

cd "$ROOT_DIR"

echo "==> Renomeando pastas/arquivos placeholder"

if [[ -d "postman/collections/__COLLECTION_NAME__" ]]; then
  mv "postman/collections/__COLLECTION_NAME__" "postman/collections/$COLLECTION_NAME"
  echo "  postman/collections/__COLLECTION_NAME__ -> postman/collections/$COLLECTION_NAME"
fi

if [[ -f "postman/environments/__COLLECTION_NAME__ - Local.environment.yaml" ]]; then
  mv "postman/environments/__COLLECTION_NAME__ - Local.environment.yaml" \
     "postman/environments/$COLLECTION_NAME - Local.environment.yaml"
  echo "  ambiente Local renomeado"
fi

if [[ -d "postman/mocks/__MOCK_SLUG__" ]]; then
  mv "postman/mocks/__MOCK_SLUG__" "postman/mocks/$MOCK_SLUG"
  echo "  postman/mocks/__MOCK_SLUG__ -> postman/mocks/$MOCK_SLUG"
fi

echo "==> Substituindo placeholders dentro do conteúdo dos arquivos"

# Só em arquivos de texto conhecidos deste kit (evita tocar em binários como
# logos em fern/assets/). Usa `find -exec sed` em vez de `grep -rl | xargs`
# pra lidar bem com nomes de arquivo com espaço.
find postman .postman fern -type f \
  \( -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.mdx" -o -name "*.md" \) \
  -print0 2>/dev/null | while IFS= read -r -d '' file; do
    sed -i \
      -e "s/__COLLECTION_NAME__/$COLLECTION_NAME/g" \
      -e "s/__MOCK_SLUG__/$MOCK_SLUG/g" \
      -e "s/__FERN_ORG__/${FERN_ORG:-__FERN_ORG__}/g" \
      -e "s/__FERN_DOMAIN__/${FERN_DOMAIN:-__FERN_DOMAIN__}/g" \
      "$file"
done

echo "==> Conferindo se sobrou algum placeholder"
remaining=$(grep -rl "__COLLECTION_NAME__\|__MOCK_SLUG__\|__FERN_ORG__\|__FERN_DOMAIN__" \
  postman .postman fern 2>/dev/null || true)
if [[ -n "$remaining" ]]; then
  echo "::warning::Ainda restam placeholders nestes arquivos (confira à mão):"
  echo "$remaining"
else
  echo "OK: nenhum placeholder restante."
fi
