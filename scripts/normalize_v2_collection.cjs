#!/usr/bin/env node
/**
 * Segunda etapa da exportação v3 -> v2.1: carrega o JSON gerado por
 * export_v2_collection.py, expande cada `url: {raw: "..."}` para a forma
 * estruturada completa (host/path/query) usando o parser oficial do SDK
 * (`postman-collection`, a mesma lib que Postman/Newman usam por baixo dos
 * panos), e só então valida com `new sdk.Collection(...)`.
 *
 * Por quê o pré-processamento manual: construir um `sdk.Url` a partir de um
 * objeto `{raw: "..."}` NÃO popula host/path/query nem preserva o `raw` —
 * o parser só deriva esses campos quando recebe a URL como string pura.
 * Passar o objeto adiante sem tratar deixaria a URL efetivamente vazia no
 * JSON final.
 *
 * Uso:
 *   node scripts/normalize_v2_collection.cjs "dist/PetVerse API.postman_collection.json"
 */
const fs = require("fs");
const path = require("path");
const sdk = require("postman-collection");

const file = process.argv[2];
if (!file) {
  console.error("Uso: node normalize_v2_collection.cjs <arquivo.json>");
  process.exit(2);
}

const data = JSON.parse(fs.readFileSync(file, "utf8"));

function expandUrl(urlField) {
  if (!urlField || typeof urlField !== "object" || !urlField.raw) return urlField;
  return new sdk.Url(urlField.raw).toJSON();
}

function walkItems(items) {
  for (const it of items) {
    if (Array.isArray(it.item)) {
      walkItems(it.item);
      continue;
    }
    if (it.request && it.request.url) {
      it.request.url = expandUrl(it.request.url);
    }
    for (const res of it.response || []) {
      if (res.originalRequest && res.originalRequest.url) {
        res.originalRequest.url = expandUrl(res.originalRequest.url);
      }
    }
  }
}

walkItems(data.item || []);

// valida com o SDK oficial depois de expandir as URLs
const collection = new sdk.Collection(data);
let count = 0;
collection.forEachItem((item) => {
  count++;
  if (!item.request.url.toString()) {
    throw new Error(`URL vazia após normalização em: ${item.name}`);
  }
});

fs.writeFileSync(file, JSON.stringify(data, null, 2), "utf8");
console.log(`OK: ${count} requisições normalizadas (URLs expandidas) em ${path.basename(file)}`);
