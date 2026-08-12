#!/usr/bin/env bash
# Carrega postman-fern.env (na raiz do projeto) como variáveis de ambiente.
# Sourced por todos os outros scripts .sh deste kit -- não rode direto.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/postman-fern.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "::error::postman-fern.env não encontrado em $ROOT_DIR. Copie postman-fern.env.example pra postman-fern.env e preencha os valores." >&2
  exit 2
fi

set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

: "${COLLECTION_NAME:?defina COLLECTION_NAME em postman-fern.env}"
