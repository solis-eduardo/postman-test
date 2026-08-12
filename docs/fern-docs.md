# Documentação com Fern

A [Fern](https://buildwithfern.com) foi adquirida pela Postman em janeiro de
2026 ([anúncio oficial](https://blog.postman.com/postman-acquires-fern/)) e é
a nova plataforma de documentação/SDKs do ecossistema Postman. Este arquivo
documenta o fluxo completo de configuração e uso da pasta `fern/` deste
repositório — incluindo os erros reais que enfrentamos configurando pela
primeira vez, porque são exatamente o tipo de coisa que se repete se alguém
tiver que reconectar isso do zero.

> Para o "porquê" da collection/ambientes/specs do Postman, veja
> `docs/postman-git-native.md`. Este arquivo cobre só a Fern.

## Por que `fern/` existe (e não só o botão Publish do Postman)

O Postman tem um botão nativo pra isso: collection → "View complete
documentation" → ícone de Publish → escolher **Fern**. Só que esse botão
passa pelo mesmo pipeline de "Publish" que já vimos bloqueado pra collections
v3/git-native — `"Publish support for multi-protocol collections coming
soon"`. Então versionamos a config da Fern aqui como **docs-as-code**,
publicando direto a partir da spec (`postman/specs/openapi.yaml`), sem
depender desse botão funcionar.

Isso também significa que **a spec é a fonte única**: `fern/generators.yml`
referencia o mesmo `postman/specs/openapi.yaml` que o portal Redoc
(`docs-pages.yml`) e a collection já usam — documentar a API numa spec só
alimenta os três.

## Estrutura

```
fern/
├── fern.config.json   # organização Fern + versão do CLI (builds determinísticos)
├── generators.yml     # api.specs -> ../postman/specs/openapi.yaml (fonte real da API)
├── docs.yml           # navegação, tema, instância (domínio publicado)
├── pages/
│   └── guia-da-api.mdx  # página de docs (fora da API Reference), na navegação
└── .gitignore
```

```json
// fern.config.json
{
    "organization": "solis-com-br-s-team",
    "version": "5.94.0"
}
```

```yaml
# generators.yml
api:
  specs:
    - openapi: ../postman/specs/openapi.yaml
```

```yaml
# docs.yml
instances:
  - url: solis.docs.buildwithfern.com   # SEM https:// -- ver "Erros que já enfrentamos" abaixo
title: PetVerse API | Documentação (via fern/ no repo)
navigation:
  - page: Guia da API
    path: pages/guia-da-api.mdx
  - api: API Reference
    paginated: true
colors:
  accent-primary:
    light: '#F7931D'
    dark: '#F7931D'
  background:
    light: '#FFFCF8'
    dark: '#0C0701'
  border:
    light: '#D9D2CA'
    dark: '#362F27'
```

**Cores com variante light/dark**: a chave é `accent-primary` (kebab-case),
não `accentPrimary` como no exemplo simples de cor única que usamos antes —
os dois formatos coexistem na Fern (cor única ou `{light, dark}` por chave:
`accent-primary`, `background`, `border`, `sidebar-background`,
`header-background`, `card-background`). Confirmado publicando um preview e
conferindo as CSS custom properties geradas (`--accent-track`, `--border`
em `rgba()`, não em hex) — não confie só no `fern check`, ele valida
estrutura, não que a cor certa foi de fato aplicada.

**Página de docs além da API Reference**: `navigation` aceita `page` (com
`path` apontando pra um `.mdx` dentro de `fern/`) no mesmo nível de `api`.
Sem isso, só a seção "API Reference" aparece — foi exatamente o que
aconteceu até adicionarmos `postman/documents/Guia da API PetVerse.md` como
`fern/pages/guia-da-api.mdx` referenciado em `docs.yml`. Confirmado com
`fern generate --docs --preview`: o log passa a mostrar `N pages` (antes
sempre `0 pages`), e a seção aparece na navegação publicada.

### `fern init --docs --openapi` NÃO conecta a spec de verdade

Ao gerar essa estrutura pela primeira vez, testamos
`fern init --docs --openapi postman/specs/openapi.yaml`. O `docs.yml` saiu
certo, mas **a spec não ficou conectada** — confirmamos removendo o arquivo
`openapi.yaml` temporariamente e rodando `fern check`: continuou dizendo
"0 errors" mesmo sem a spec existir, provando que a referência era decorativa.

Quem conecta a spec de verdade é `fern init --api --openapi <path>` (sem
`--docs`), que gera o `generators.yml` com `api.specs`. Confirmamos com o
mesmo teste de controle (remover a spec → `fern check` agora reporta
`Missing file: ../postman/specs/openapi.yaml`). Por isso este repo tem os
dois arquivos (`generators.yml` do `--api`, `docs.yml` do `--docs`)
combinados manualmente, não gerados por um único comando.

## Autenticação

```bash
npx fern-api login     # abre o navegador, autentica via GitHub
npx fern-api org get   # confirma a organização ativa (deve bater com fern.config.json)
```

Se `fern org get` retornar `HTTP 403 — You do not have permission to access
files for the specified organization`, a organização em `fern.config.json`
está errada **ou** a conta logada não tem acesso a ela — ver "Erros que já
enfrentamos" abaixo antes de ficar tentando slugs diferentes no escuro.

## Setup local

```bash
npm run fern:check    # valida fern/ + a spec referenciada (roda também no npm run lint e no CI)
npm run fern:dev      # preview local (fern docs dev)
```

## Fluxo: preview antes de produção

**Sempre valide num preview antes de publicar em produção** — é rápido, não
afeta o site real, e pega problemas de config cedo (foi assim que achamos o
bug do `https://` duplicado, ver abaixo).

```bash
# gera um preview com id estável (reexecutar com o mesmo --id sobrescreve a URL)
npx fern-api generate --docs --preview --id "minha-mudanca"
# -> publica em algo como https://solis-com-br-s-team-preview-minha-mudanca.docs.buildwithfern.com

# lista todos os previews ativos da organização
npx fern-api docs preview list

# apaga um preview quando não precisar mais
npx fern-api docs preview delete "solis-com-br-s-team-preview-minha-mudanca.docs.buildwithfern.com"
```

Publicar em produção de verdade (sem `--preview`) pede confirmação
interativa, porque afeta o domínio real:

```bash
npx fern-api generate --docs --log-level debug
```

## CI

- **`.github/workflows/fern-check.yml`** — roda `fern check` em PRs/pushes
  que tocam `fern/**` ou a spec. Não precisa de token (validação estrutural).
- **`.github/workflows/fern-docs-publish.yml`** — roda
  `fern generate --docs` a cada push em `main`. **Precisa do secret
  `FERN_TOKEN`** no repositório:

  ```bash
  npx fern-api login
  npx fern-api token --organization solis-com-br-s-team
  gh secret set FERN_TOKEN --repo solis-eduardo/postman-test --body "<token gerado>"
  ```

  > O comando `gh secret set` grava um valor sensível — o harness do Claude
  > Code bloqueia isso em modo automático por padrão. Rode você mesmo no
  > terminal; eu não tenho como executar esse passo sozinho.

## Erros que já enfrentamos (e a causa real, não a genérica)

Estes já aconteceram configurando este repositório — documentados porque vão
se repetir se alguém reconectar do zero ou trocar de organização/domínio.

| Erro | Causa real | Correção |
|---|---|---|
| `Domain "X" is already registered to another organization` (ao publicar) | `fern.config.json` tinha um slug de organização **diferente** da que já é dona do domínio configurado em `docs.yml` — no nosso caso, chutei `"solis"` (um slug genérico) quando a org real (criada pelo fluxo Postman → Publish → Fern) tinha um slug diferente | Achar o slug real: dashboard da Fern mostra em "Source" algo como `fern-starter/<org-real>` (a org fica **depois** da barra, não é o nome do template `fern-starter`) — ou peça pra rodar `npx fern-api login && npx fern-api org get` e usar o `orgId` retornado |
| `HTTP 403 — You do not have permission to access files for the specified organization` (`fern org get`) | Slug de organização errado em `fern.config.json`, ou a conta logada (`fern login`) não pertence a essa organização | Corrigir `fern.config.json` pro slug certo; se persistir, confirmar que logou com a conta certa (`fern logout && fern login`) |
| `FDR registerApiDefinition failed... "User does not belong to organization"` (só no CI, `fern-docs-publish.yml`) | O secret `FERN_TOKEN` no GitHub foi gerado **antes** de descobrir o slug/conta certos — o token em si pertence a outra organização, mesmo com `fern.config.json` já corrigido localmente | Gerar um token novo *depois* de confirmar `fern org get` funciona localmente (`npx fern-api token --organization <org>`) e atualizar o secret (`gh secret set FERN_TOKEN`) |
| URL mostrada como `https://https://dominio...` (duplicada) ao rodar `fern generate --docs` | `docs.yml`'s `instances[].url` tinha o prefixo `https://` — o campo espera só o domínio puro (`dominio.docs.buildwithfern.com`), a CLI adiciona o esquema sozinha | Remover `https://` de `instances[].url` em `docs.yml` |
| Site publicado mostra só `<title>Documentation</title>` genérico, sem o conteúdo | A URL real estava redirecionando pra uma tela de login (`/~login?returnTo=...`) — o site estava protegido, então o "conteúdo" que carregava era a página de login | Verificar configuração de visibilidade/access control do site no dashboard da Fern (não encontramos comando de CLI pra isso) — e/ou terminar a etapa "Finish custom domain setup" pendente no dashboard |
| Site não aparece em "Domains" no dashboard, mas o link do preview funciona | Previews (`--preview --id`) são deploys efêmeros num namespace à parte (`<org>-preview-<id>.docs.buildwithfern.com`), geridos via `fern docs preview list/delete`, não pela tela principal de domínios | Não é um bug — usar `fern docs preview list` pra ver/gerenciar previews |
| Renomear uma pasta na collection do Postman não muda o nome da seção na Fern | A Fern **não lê a collection** — só lê `postman/specs/openapi.yaml` (`fern/generators.yml`). A navegação/agrupamento do site vem das `tags` da spec, não das pastas do Postman; os dois são editados separadamente e nada sincroniza um pro outro | Renomear a tag correspondente em `postman/specs/openapi.yaml` (`tags[].name` + todo `tags: [...]` das operações) |
| `fern generate --docs` avisa `"1 tag contain non-ASCII characters"` e `"Skipping API fern"` ao usar um nome de tag com acento (ex.: `Autenticação`) | Validação da Fern sinaliza tags fora de ASCII — mas na prática **não impediu** a publicação: testamos em preview e a navegação saiu certa (`"Autenticação"` no sidebar, slug normalizado pra `api-reference/autenticacao`) | Nenhuma — é um aviso, não um erro real. Confirmar sempre em preview antes de assumir que quebrou |

## Equivalente para GitLab

A Fern **não tem um app dedicado do GitLab** (diferente do GitHub, que cria
repositório automaticamente via app quando você publica pelo Postman). A
integração é só via pipeline CI/CD, no mesmo espírito do
`fern-check.yml`/`fern-docs-publish.yml` deste repo, só que em
`.gitlab-ci.yml` ([fonte](https://buildwithfern.com/learn/docs/developer-tools/git-lab)):

| Stage | Gatilho | Ação |
|---|---|---|
| `check` | MRs e branch principal | `fern check` |
| `preview_docs` | Só em MRs | `fern generate --docs --preview`, comenta o link no MR |
| `publish_docs` | Merge na branch principal | `fern generate --docs` (produção) |
| `cleanup_preview` | Merge na branch principal | Apaga o preview do MR mergeado |

Variáveis de CI/CD necessárias no GitLab:

- `FERN_TOKEN` — mesmo token gerado por `fern token`, sem proteção de branch.
- `REPO_TOKEN` — um Project Access Token do GitLab (role **Reporter**, scope
  **api**), usado só pra comentar o link do preview no MR.

`fern/` em si não muda nada — é agnóstico de onde o Git está hospedado. Self-managed/on-premise GitLab não é
explicitamente documentado pela Fern; os exemplos assumem `gitlab.com`.
