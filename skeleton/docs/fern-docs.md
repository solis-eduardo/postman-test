# Documentação com Fern

A [Fern](https://buildwithfern.com) foi adquirida pela Postman em janeiro de
2026 ([anúncio oficial](https://blog.postman.com/postman-acquires-fern/)) e é
a nova plataforma de documentação/SDKs do ecossistema Postman. Este arquivo
documenta o fluxo completo de configuração e uso da pasta `fern/` — incluindo
os erros reais enfrentados configurando isso pela primeira vez num projeto
real, porque são exatamente o tipo de coisa que se repete se alguém tiver
que reconectar do zero.

> Para o "porquê" da collection/ambientes/specs do Postman, veja
> `docs/postman-git-native.md`. Este arquivo cobre só a Fern.

## Por que `fern/` existe (e não só o botão Publish do Postman)

O Postman tem um botão nativo pra isso: collection → "View complete
documentation" → ícone de Publish → escolher **Fern**. Só que esse botão
passa pelo mesmo pipeline de "Publish" que já vimos bloqueado pra collections
v3/git-native — `"Publish support for multi-protocol collections coming
soon"`. Então este kit versiona a config da Fern como **docs-as-code**,
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
├── docs.yml           # navegação, tema, logo, instância (domínio publicado)
├── pages/
│   └── example.mdx    # página de docs (fora da API Reference), na navegação
├── assets/            # logo(s) e outros arquivos estáticos referenciados por docs.yml
└── .gitignore
```

```json
// fern.config.json
{
    "organization": "__FERN_ORG__",
    "version": "5.94.0"
}
```

```yaml
# generators.yml
api:
  specs:
    - openapi: ../postman/specs/openapi.yaml
```

Ver `fern/docs.yml` deste kit pra um exemplo completo já testado (navegação,
tema light/dark, navbar-links pra spec, comentários com as outras opções
disponíveis).

### `fern init --docs --openapi` NÃO conecta a spec de verdade

Ao gerar essa estrutura pela primeira vez num projeto real, testamos
`fern init --docs --openapi postman/specs/openapi.yaml`. O `docs.yml` saiu
certo, mas **a spec não ficou conectada** — confirmamos removendo o arquivo
`openapi.yaml` temporariamente e rodando `fern check`: continuou dizendo
"0 errors" mesmo sem a spec existir, provando que a referência era decorativa.

Quem conecta a spec de verdade é `fern init --api --openapi <path>` (sem
`--docs`), que gera o `generators.yml` com `api.specs`. Confirmamos com o
mesmo teste de controle (remover a spec → `fern check` agora reporta
`Missing file: ../postman/specs/openapi.yaml`). Por isso este kit tem os
dois arquivos (`generators.yml` do `--api`, `docs.yml` do `--docs`)
combinados manualmente, não gerados por um único comando.

## Cores (tema light/dark)

```yaml
colors:
  accent-primary:
    light: '#3B82F6'
    dark: '#60A5FA'
  background:
    light: '#FFFFFF'
    dark: '#0A0A0A'
  border:
    light: '#E5E7EB'
    dark: '#27272A'
```

A chave é `accent-primary` (kebab-case), não `accentPrimary` como no formato
simples de cor única — os dois coexistem na Fern (cor única ou `{light,
dark}` por chave: `accent-primary`, `background`, `border`,
`sidebar-background`, `header-background`, `card-background`). Confirmado
publicando um preview e conferindo as CSS custom properties geradas
(`--accent-track`, `--border` em `rgba()`, não em hex) — **não confie só no
`fern check`**, ele valida estrutura, não que a cor certa foi de fato
aplicada (mesma lição do bug do `https://` duplicado abaixo).

## Página de docs além da API Reference

`navigation` aceita `page` (com `path` apontando pra um `.mdx` dentro de
`fern/`) no mesmo nível de `api`. Sem isso, só a seção "API Reference"
aparece. Confirmado com `fern generate --docs --preview`: o log passa a
mostrar `N pages` (antes sempre `0 pages`) quando a página está corretamente
referenciada, e a seção aparece na navegação publicada.

## Logo

```yaml
logo:
  href: https://seu-site.com
  light: assets/logo-escura.png   # usada quando o site está em tema claro
  dark: assets/logo-clara.png     # usada quando o site está em tema escuro
  height: 28
```

- `logo.light`/`logo.dark` só aceitam **arquivo local** (caminho relativo a
  `fern/`), não URL remota direto — baixe a imagem pro repo primeiro.
- A Fern troca a imagem automaticamente por CSS (`dark:hidden` /
  `dark:block`), confirmado inspecionando o HTML de um preview: os dois
  `<img>` ficam no DOM, só um visível por vez conforme o tema.
- **Se você só tem uma variante da logo** (ex.: uma versão com texto branco,
  que funciona no tema escuro mas fica ilegível no claro): dá pra gerar a
  outra variante recolorindo só os pixels do texto (preservando ícone/cor de
  marca e a transparência original) com Pillow — script de referência:

  ```python
  from PIL import Image
  img = Image.open("logo-original.png").convert("RGBA")
  out = []
  for r, g, b, a in img.getdata():
      # "fator de brancura": alto quando r,g,b são altos E próximos entre si
      # (evita recolorir cores de marca saturadas, tipo laranja/azul puro)
      brancura = max(0, min(r, g, b) - 180) / 75 * (1 - (max(r,g,b)-min(r,g,b))/255)
      brancura = max(0.0, min(1.0, brancura))
      nr = int(r * (1 - brancura) + 17 * brancura)
      ng = int(g * (1 - brancura) + 17 * brancura)
      nb = int(b * (1 - brancura) + 17 * brancura)
      out.append((nr, ng, nb, a))
  img.putdata(out)
  img.save("logo-recolorida.png")
  ```

  Sempre confira pixel a pixel antes/depois (não só visualmente) que a cor
  de marca não mudou e que o alpha original foi preservado.

## Navbar links (ex.: expor a spec crua)

```yaml
navbar-links:
  - type: minimal
    text: OpenAPI (JSON)
    href: /openapi.json
    target: _blank
  - type: minimal
    text: OpenAPI (YAML)
    href: /openapi.yaml
    target: _blank
```

A Fern serve a spec automaticamente em `/openapi.json` e `/openapi.yaml` do
site publicado — sem precisar declarar isso em nenhum outro lugar. Confirmado
que esses dois paths respondem `200` mesmo com o domínio principal atrás de
tela de login (diferente do resto do site). **Atenção**: é a spec que a Fern
*re-derivou* a partir do que indexou, não o `postman/specs/openapi.yaml`
original servido cru — testamos e a versão servida virou OpenAPI 3.1 (mesmo
a fonte sendo 3.0.x) e perdeu `description`/`contact`/`license` do `info`
(ficou só `title` genérico + `version`). Os paths/schemas batem, então serve
bem pra importar noutra ferramenta, mas não é um espelho fiel dos metadados.

`type` aceita `minimal | filled | outlined | github | dropdown`.

## Outras opções de tema/config em `docs.yml`

Documentadas oficialmente
([global configuration](https://buildwithfern.com/learn/docs/getting-started/global-configuration)),
mas sem preview confirmado neste kit:

| Chave | Pra quê |
|---|---|
| `favicon` | Ícone da aba do navegador (arquivo local, tipo `logo`) |
| `background-image` | Imagem de fundo do site, variante `light`/`dark` |
| `typography` | Fonte customizada pra título, corpo de texto e código |
| `footer-links` | Links de rodapé (GitHub, Slack, redes sociais) |
| `layout` | Dimensões estruturais (altura do header, largura da página) |
| `settings` | Comportamento do site: texto de busca, desabilitar busca, etc. |
| `metadata` | Tags de SEO/preview social (Open Graph, Twitter Card) |
| `analytics` | Integração com GA4 e outros provedores |
| `redirects` | Redirecionamentos de path (útil ao renomear uma página) |
| `landing-page` | Página de entrada dedicada, diferente da primeira da navegação |
| `ai-search` / `agents` | "Ask Fern" (busca com IA) e diretivas pra agentes de IA (`llms.txt`) |
| `header` / `footer` | Componente React customizado, pra quem quer fugir do template padrão |
| `global-theme` | Nome de um tema de organização pré-salvo (`fern docs theme list/upload`) — **não** são os presets "Layout/Button shape/Font style" do assistente do dashboard; essas são features diferentes (ver tabela de `theme` abaixo) |

### `theme` — testado e confirmado (todas as 6 dimensões)

```yaml
theme:
  sidebar: minimal          # default | minimal
  body: default              # default | canvas
  tabs: default               # default | bubble (só visível se a navegação usa `tab:`)
  page-actions: toolbar      # default | toolbar
  footer-nav: minimal        # default | minimal
  product-switcher: default  # default | toggle (só visível com múltiplos produtos)
```

Publicamos um preview isolado de cada dimensão num projeto real pra comparar
lado a lado antes de decidir: `sidebar: minimal`, `page-actions: toolbar` e
`footer-nav: minimal` fizeram diferença visual clara e boa; `body: canvas`
foi testado e descartado (não curtiram); `tabs`/`product-switcher` não
mostraram efeito visível sem tabs/múltiplos produtos configurados — não é
bug, é esperado.

**As 3 opções "Layout (Stacked/Side by side/Minimal)", "Button shape
(Sharp/Smooth/Round)" e "Font style (Classic/Editorial/Futuristic)" que
aparecem no assistente inicial do Dashboard da Fern NÃO foram identificadas
como chaves de `docs.yml`** — não achamos essas strings na documentação
oficial nem no bundle da CLI (`fern-api`), e `fern docs theme list` (que
lista temas de organização salvos) voltou vazio. `fern check` **rejeita
chave desconhecida** com erro claro (`Unexpected property`), então dá pra
sondar com segurança, mas isso consome ciclos de preview sem garantia de
achar o nome certo. **Caminho mais rápido pra confirmar**: escolher a
combinação no Dashboard, salvar, e ler o diff que aparece em `fern/docs.yml`
— o "Fern Editor" do dashboard commita direto no GitHub (é assim que
`fern.config.json` chegou a ser corrigido nesse projeto sem ninguém rodar
`git commit` manualmente), então o valor real aparece no histórico do repo.

Sempre confirme qualquer mudança de tema em **preview**, nunca só com
`fern check` — ele valida estrutura, não pega bug de renderização (foi assim
que achamos o bug do `https://` duplicado, e é o único jeito de saber se uma
cor/imagem realmente aplicou).

## Autenticação

```bash
npx fern-api login     # abre o navegador, autentica via GitHub
npx fern-api org get   # confirma a organização ativa (deve bater com fern.config.json)
```

Se `fern org get` retornar `HTTP 403 — You do not have permission to access
files for the specified organization`, a organização em `fern.config.json`
está errada **ou** a conta logada não tem acesso a ela — ver a tabela de
erros abaixo antes de ficar tentando slugs diferentes no escuro.

## Setup local

```bash
npm run fern:check    # valida fern/ + a spec referenciada (roda também no npm run lint e no CI)
npm run fern:dev      # preview local (fern docs dev)
```

## Fluxo: preview antes de produção

**Sempre valide num preview antes de publicar em produção** — é rápido, não
afeta o site real, e pega problemas de config cedo.

```bash
# gera um preview com id estável (reexecutar com o mesmo --id sobrescreve a URL)
npx fern-api generate --docs --preview --id "minha-mudanca"
# -> publica em algo como https://<sua-org>-preview-minha-mudanca.docs.buildwithfern.com

# lista todos os previews ativos da organização
npx fern-api docs preview list

# apaga um preview quando não precisar mais
npx fern-api docs preview delete "<url do preview>"
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
  npx fern-api org get                                    # confirme a org ANTES de gerar o token
  npx fern-api token --organization <sua-org>
  gh secret set FERN_TOKEN --repo <owner>/<repo> --body "<token gerado>"
  ```

  > O comando `gh secret set` grava um valor sensível — o harness do Claude
  > Code (se for esse o seu caso) bloqueia isso em modo automático por
  > padrão. Rode você mesmo no terminal.

## Erros que já enfrentamos (e a causa real, não a genérica)

Estes já aconteceram configurando um projeto real com este kit —
documentados porque vão se repetir se alguém reconectar do zero ou trocar
de organização/domínio.

| Erro | Causa real | Correção |
|---|---|---|
| `Domain "X" is already registered to another organization` (ao publicar) | `fern.config.json` tinha um slug de organização **diferente** da que já é dona do domínio configurado em `docs.yml` | Achar o slug real: dashboard da Fern mostra em "Source" algo como `fern-starter/<org-real>` (a org fica **depois** da barra, não é o nome do template `fern-starter`) — ou rode `npx fern-api login && npx fern-api org get` e use o `orgId` retornado |
| `HTTP 403 — You do not have permission to access files for the specified organization` (`fern org get`) | Slug de organização errado em `fern.config.json`, ou a conta logada (`fern login`) não pertence a essa organização | Corrigir `fern.config.json` pro slug certo; se persistir, confirmar que logou com a conta certa (`fern logout && fern login`) |
| `FDR registerApiDefinition failed... "User does not belong to organization"` (só no CI, `fern-docs-publish.yml`) | O secret `FERN_TOKEN` no GitHub foi gerado **antes** de descobrir o slug/conta certos — o token em si pertence a outra organização, mesmo com `fern.config.json` já corrigido localmente | Gerar um token novo *depois* de confirmar `fern org get` funciona localmente e atualizar o secret |
| URL mostrada como `https://https://dominio...` (duplicada) ao rodar `fern generate --docs` | `docs.yml`'s `instances[].url` tinha o prefixo `https://` — o campo espera só o domínio puro | Remover `https://` de `instances[].url` em `docs.yml` |
| Site publicado mostra só `<title>Documentation</title>` genérico, sem o conteúdo | A URL real estava redirecionando pra uma tela de login (`/~login?returnTo=...`) — site protegido | Verificar configuração de visibilidade/access control do site no dashboard da Fern (sem comando de CLI pra isso) — e/ou terminar "Finish custom domain setup" pendente no dashboard |
| Site não aparece em "Domains" no dashboard, mas o link do preview funciona | Previews (`--preview --id`) são deploys efêmeros num namespace à parte, geridos via `fern docs preview list/delete`, não pela tela principal de domínios | Não é um bug — usar `fern docs preview list` pra ver/gerenciar previews |
| Renomear uma pasta na collection do Postman não muda o nome da seção na Fern | A Fern **não lê a collection** — só lê `postman/specs/openapi.yaml`. A navegação vem das `tags` da spec, não das pastas do Postman | Renomear a tag correspondente em `postman/specs/openapi.yaml` (`tags[].name` + todo `tags: [...]` das operações) |
| `fern generate --docs` avisa `"1 tag contain non-ASCII characters"` e `"Skipping API fern"` ao usar tag com acento | Validação sinaliza tags fora de ASCII — mas na prática **não impediu** a publicação em teste real | Nenhuma — é um aviso, não um erro real. Confirmar sempre em preview antes de assumir que quebrou |
| Presets do assistente inicial do dashboard (Layout/Button shape/Font style) sem chave YAML confirmada | Não documentados publicamente nem achados no bundle da CLI; `fern docs theme list` (recurso diferente) voltou vazio | Escolher no dashboard, salvar, e ler o diff em `fern/docs.yml` (o Fern Editor commita direto no GitHub) |

## Equivalente para GitLab

A Fern **não tem um app dedicado do GitLab** (diferente do GitHub, que cria
repositório automaticamente via app quando você publica pelo Postman). A
integração é só via pipeline CI/CD, no mesmo espírito do
`fern-check.yml`/`fern-docs-publish.yml` — ver `.gitlab-ci.yml.example`
neste kit
([fonte](https://buildwithfern.com/learn/docs/developer-tools/git-lab)):

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

`fern/` em si não muda nada — é agnóstico de onde o Git está hospedado.
Self-managed/on-premise GitLab não é explicitamente documentado pela Fern;
os exemplos assumem `gitlab.com`.
