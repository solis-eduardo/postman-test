# Kit Postman Git Native + Fern Docs

Skeleton pronto pra copiar pra dentro de um projeto **existente**: collection
Postman no formato v3 (Native Git), spec OpenAPI como fonte única, portal
Redoc, Fern Docs (com tema/logo/navbar customizados) e os workflows de CI
que ligam tudo isso — extraído de um projeto real onde cada peça foi
testada de verdade (não é teoria: erros reais e as correções estão
documentados em `docs/TROUBLESHOOTING.md`).

## Comece aqui

**`docs/SETUP.md`** — checklist passo a passo de como adotar isto num
projeto existente. Comece por ali, não por este README.

## O que tem aqui

| Caminho | O quê |
|---|---|
| `postman-fern.env.example` | **Config central** — nome da collection, org da Fern, domínio etc. Todo script/workflow lê daqui, nada fica hardcoded |
| `postman/` | Esqueleto da collection (v3/Native Git), 1 ambiente de exemplo, spec OpenAPI mínima, 1 mock de exemplo — tudo já validado com a Postman CLI oficial |
| `.postman/resources.yaml.example` | Vínculo do repo com o workspace do Postman |
| `fern/` | Config completa da Fern Docs: spec, navegação, tema (light/dark), logo, navbar-links |
| `scripts/apply-config.sh` | Roda uma vez na adoção: aplica `postman-fern.env` em todo o kit (renomeia pastas placeholder + substitui `__COLLECTION_NAME__` etc. dentro dos arquivos) |
| `scripts/` (resto) | `lint.sh` (valida tudo), `run-collection.sh`, `check_spec_alignment.py` (endpoints + tags + schema), `export_v2_collection.py` + `normalize_v2_collection.cjs` (espelho v2.1) |
| `.github/workflows/` | CI: lint + roda a collection contra o mock, portal Redoc no GitHub Pages, `fern check`, publish da Fern |
| `.gitlab-ci.yml.example` | Equivalente GitLab da Fern (ela não tem app dedicado, só pipeline) |
| `docs/SETUP.md` | Passo a passo de adoção |
| `docs/TROUBLESHOOTING.md` | Todo erro real enfrentado construindo isto, com causa e correção |
| `docs/architecture.md` | Como as peças se conectam e se mantêm atualizadas |

Testado de ponta a ponta: copiado pra um diretório novo, configurado com um
nome de collection com espaço/acento, `apply-config.sh` rodado, e todo o
pipeline validado (`lint.sh`, mock local, `run-collection.sh`, exportação
v2.1 + round-trip de volta pro v3) — sem erro.

## Por que este formato

- **Collection em YAML por request** (não um JSON gigante) — diffs de PR
  pequenos e legíveis, sem conflito de merge entre quem mexe em requests
  diferentes.
- **Uma spec OpenAPI só**, alimentando collection, portal Redoc e Fern Docs
  ao mesmo tempo — documentar uma vez, publicar em três lugares.
- **Tudo versionado**, incluindo o que normalmente fica só na cabeça de
  quem configurou (org da Fern, por que a porta do mock precisa bater com
  o ambiente, por que `dist/` existe) — é o que `docs/TROUBLESHOOTING.md`
  resolve pra quem vier depois.
