# Troubleshooting consolidado

Todo erro real enfrentado construindo e configurando este kit, num projeto
de referência de ponta a ponta — não é teoria. Cada linha tem a **causa
real** (não a mensagem genérica) e a correção que funcionou. Organizado por
sistema; veja também `docs/postman-git-native.md` e `docs/fern-docs.md` pra
contexto completo de cada item.

## Postman (Native Git)

| Erro/sintoma | Causa real | Correção |
|---|---|---|
| `Add a Git remote to continue` (ao abrir a pasta no Postman Desktop) | O Postman exige um remote git configurado — não basta ser um repositório git local solto | `git remote add origin <url>` apontando pra um repositório de verdade |
| `The .postman directory is missing` | O `.postman/resources.yaml` (com o `workspace.id`) foi apagado/nunca existiu | Recriar com `workspace: id: <uuid>` — o app volta a reconhecer o vínculo |
| Menu "Items" vazio mesmo com a collection presente no disco | A raiz gerenciada pelo Postman é `postman/` (sem ponto), não `.postman/` (com ponto) | Mover collection/ambientes/specs pra dentro de `postman/` na raiz do repo |
| `.postman_environment.json` — "Legacy v2 JSON file found. Convert to v3" | Ambiente ainda no formato clássico (v2.1); a Postman CLI **não tem** comando de migração pra ambientes (só pra collections) | Botão "Convert to v3" do próprio Postman Desktop |
| Spec existe no disco mas não aparece no sidebar | Diferente de collections/ambientes, specs **não são auto-descobertas** só por estarem dentro de `postman/specs/` | Registrar em `.postman/resources.yaml`, `localResources.specs` |
| `Publish support for multi-protocol collections coming soon` | Collections v3/git-native ainda não têm suporte a esse pipeline — limitação da plataforma | Usar o espelho v2.1 (`dist/`, `npm run export:v2`) ou o portal Redoc |
| "Push to Cloud" → `Repository does not match workspace` com remote correto | Provável cache do app associando a pasta a um estado antigo | Fechar e reabrir o Postman Desktop **por completo** (sair do processo, não só a janela) |
| Renomear pasta na collection não reflete em lugar nenhum publicado | Pasta = só a collection. Tag na spec = o que a Fern usa. São independentes | Renomear a tag em `postman/specs/openapi.yaml` também |

## Fern

| Erro/sintoma | Causa real | Correção |
|---|---|---|
| `fern init --docs --openapi <path>` "conecta" a spec mas `fern check` passa mesmo sem ela existir | Só `--docs` **não** conecta de verdade — a referência é decorativa | Usar `fern init --api --openapi <path>` (sem `--docs`), que gera `generators.yml` com `api.specs` de verdade |
| `Domain "X" is already registered to another organization` (ao publicar) | `fern.config.json` com slug de organização **diferente** do dono real do domínio em `docs.yml` | Achar o slug real: dashboard mostra em "Source" algo como `fern-starter/<org-real>` (org fica depois da barra) — ou `fern login && fern org get` |
| `HTTP 403 — You do not have permission...` (`fern org get`) | Slug errado em `fern.config.json`, ou conta logada sem acesso à org | Corrigir o slug; `fern logout && fern login` se persistir |
| `"User does not belong to organization"` (só no CI) | `FERN_TOKEN` gerado **antes** de confirmar org/conta certos localmente | Gerar token novo *depois* de `fern org get` funcionar local, atualizar o secret |
| URL vira `https://https://dominio...` (duplicada) | `instances[].url` em `docs.yml` tinha `https://` — o campo só aceita o domínio puro | Remover `https://` de `instances[].url` |
| Site publicado mostra só `<title>Documentation</title>`, sem conteúdo | URL redirecionando pra tela de login (`/~login?returnTo=...`) — site protegido | Checar visibilidade/access control no dashboard da Fern, e/ou "Finish custom domain setup" pendente |
| Site não aparece em "Domains" no dashboard, mas o link do preview funciona | Previews são deploys efêmeros num namespace à parte, não a lista principal de domínios | Não é bug — `fern docs preview list/delete` |
| Renomear pasta na collection do Postman não muda a seção na Fern | A Fern **não lê a collection**, só a spec (`generators.yml` → `openapi.yaml`) | Renomear a `tag` correspondente na spec |
| `"1 tag contain non-ASCII characters"` + `"Skipping API fern"` com tag acentuada | Aviso de validação — **não impede** a publicação de verdade (testado) | Nenhuma ação necessária; confirmar em preview antes de assumir que quebrou |
| Cor/logo/tema não aparece como esperado mesmo com `fern check` limpo | `fern check` só valida **estrutura**, não que o valor certo renderizou | Sempre confirmar em preview (`fern generate --docs --preview --id ...`), nunca só no check |
| Logo com texto branco ilegível no tema claro | Uma imagem só serve bem pra um tema quando tem texto de cor fixa | Recolorir só os pixels de texto (preservando cor de marca + alpha) — script de referência em `docs/fern-docs.md` |
| Presets do assistente do Dashboard (Layout/Button shape/Font style) sem chave YAML confirmada | Não documentados publicamente, não achados no bundle da CLI, `fern docs theme list` (feature diferente) vazio | Escolher no dashboard, salvar, ler o diff que aparece em `fern/docs.yml` (Fern Editor commita direto no GitHub) |

## CI / Geral

| Erro/sintoma | Causa real | Correção |
|---|---|---|
| `Node.js 20 is deprecated` (aviso no Actions) | `node-version` do `setup-node` em 20; também as próprias actions (`checkout@v4`, `setup-node@v4`) rodam num runtime Node deprecado, independente do `node-version` configurado | Subir `node-version` pra 24; considerar `@v5` das actions (`actions/checkout@v5`, `actions/setup-node@v5`) |
| Collection roda contra o mock, mas todas as requisições falham por "connection refused" no CI | Mock não subiu antes da collection rodar, ou subiu na porta errada | Ver receita completa em `.github/workflows/api-tests.yml` (sobe o mock, espera health check responder, só então roda a collection) |
| Testes passam localmente mas falham no CI por porta errada | `postman/mocks/<slug>/config.yaml` (porta do mock) e o ambiente Local (`base_url`) foram editados **separadamente** e divergiram | CI já falha alto comparando as duas antes de rodar — reconcilie manualmente qual porta usar |
| `dist/` desatualizado quebra o CI depois de qualquer mudança na collection | É proposital: `dist/` é gerado, nunca editado à mão | Em push na `main`, o CI já regenera e commita sozinho; em PR, rode `npm run export:v2` local e commite |
| `gh secret set` recusado / não executa | Ferramentas de automação (ex.: harness de agente de IA) costumam bloquear gravação de secrets em modo automático, por segurança | Rode o comando você mesmo, manualmente, no terminal |
| Push não dispara o workflow (nem push nem manual aparecem por um tempo) | Atraso pontual na entrega do webhook do GitHub — não é o workflow nem o repositório | Adicionar `workflow_dispatch:` ao trigger do workflow (bom ter de qualquer forma) e disparar manualmente (`gh workflow run <arquivo>.yml`) enquanto isso |
| Repositório privado + GitHub Pages não funciona | GitHub Pages grátis só em repo público | Tornar o repo público (se o conteúdo permitir) ou trocar de host pro portal estático |

## Meta: como esta tabela foi construída

Cada linha aqui só entrou depois de reproduzir o erro de verdade (não é uma
lista de "problemas prováveis") — e cada correção foi confirmada rodando de
novo depois de aplicada, não só assumida. Ao adicionar uma linha nova no seu
projeto, siga o mesmo padrão: **causa real** (o que efetivamente estava
errado, não a mensagem de erro reformulada) e **correção testada** (não só
"provavelmente resolve").
