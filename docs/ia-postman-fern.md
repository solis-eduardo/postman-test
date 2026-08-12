# Recursos de IA do Postman/Fern — candidatos a adicionar

> Status: **recomendação, ainda não implementada**. Nenhum dos itens abaixo
> foi aplicado em `fern/generators.yml`, `fern/docs.yml` ou `.mcp.json` —
> este arquivo só registra o que vale a pena configurar e como, pra não
> perder o levantamento feito em 2026-08-12.
>
> Para o funcionamento atual de cada pasta, veja `docs/fern-docs.md` (Fern) e
> `docs/postman-git-native.md` (Postman git-native). Este arquivo cobre só as
> features de IA que ainda **não** estão configuradas.

## 1. MCP Server gerado a partir da própria spec

Tanto Fern quanto Postman geram um **servidor MCP automaticamente a partir de
uma spec OpenAPI** — cada endpoint vira uma tool MCP, sem escrever código. A
spec já é fonte única do projeto (`postman/specs/openapi.yaml`, referenciada
por `fern/generators.yml`, pelo portal Redoc e pela collection), então ligar
esse gerador é só apontar pra ela.

**Via Fern** — adicionar um generator MCP em `fern/generators.yml` (mesmo
padrão do `api.specs` que já existe hoje):

```yaml
# fern/generators.yml (proposta — ainda não aplicado)
api:
  specs:
    - openapi: ../postman/specs/openapi.yaml
groups:
  mcp:
    generators:
      - name: fernapi/fern-mcp-server
        version: latest
        output:
          location: local-file-system
          path: ../dist/mcp-server
```

Rodar com `npx fern-api generate --group mcp` e validar com `fern check`
antes de confiar no output (mesmo espírito do fluxo "preview antes de
produção" já documentado em `docs/fern-docs.md`).

**Via Postman** — o Postman MCP Generator faz o equivalente a partir da
collection exportada (`dist/PetVerse API.postman_collection.json`) ou
direto da spec, pelo próprio app/dashboard do Postman.

Resultado: agentes (Claude Code incluso) passam a poder **chamar** a
PetVerse API como tools MCP, em vez de só ler a spec ou a doc publicada.

## 2. Postman MCP Server (workspace) como integração no Claude Code

Existe um MCP server oficial da Postman que expõe o *workspace* (collections,
environments, mocks, specs) como tools — criar/editar requests, rodar
collections, gerenciar environments via API do Postman, em vez de editar os
arquivos YAML git-native na mão.

Proposta de entrada em `.mcp.json` (raiz do repo, ainda não criado/editado):

```json
{
  "mcpServers": {
    "postman": {
      "command": "npx",
      "args": ["-y", "@postman/mcp-server"],
      "env": {
        "POSTMAN_API_KEY": "${POSTMAN_API_KEY}"
      }
    }
  }
}
```

(nome do pacote/flags exatos precisam ser confirmados na documentação oficial
da Postman antes de aplicar — o exemplo acima é ilustrativo da forma, não um
comando validado.)

Motivação específica deste repo: boa parte das dores registradas em
`docs/postman-git-native.md` vêm de editar o schema v3 git-native manualmen-
te (environments em YAML, flows, mocks) e só descobrir erro de schema depois,
rodando `scripts/run-collection.sh`. Com o MCP oficial, o agente passaria a
manipular esses recursos via API real do Postman, que valida o schema no
próprio request — reduz a classe de erro "editei o YAML errado".

## 3. Fern "Ask AI" + `llms.txt` no site publicado

`fern/docs.yml` hoje só define `instances`, `title`, `navigation` e `colors`.
Fern suporta dois recursos de IA voltados pro site publicado
(`solis.docs.buildwithfern.com`):

- **Ask AI**: widget de chat embutido no site publicado, que responde
  perguntas usando o conteúdo da spec/docs indexado.
- **`llms.txt` / `llms-full.txt`**: versão da documentação em texto puro,
  otimizada pra ser consumida por outros LLMs (é o mesmo padrão que
  ferramentas como Mintlify/ReadMe já adotaram).

Proposta de adição em `fern/docs.yml`:

```yaml
# fern/docs.yml (proposta — ainda não aplicado; nomes de chave a confirmar
# na doc oficial da Fern antes de aplicar)
instances:
  - url: solis.docs.buildwithfern.com
title: PetVerse API | Documentação (via fern/ no repo)
navigation:
  - api: API Reference
    paginated: true
colors:
  accentPrimary: '#22c55e'
  background: '#000000'
experimental:
  ask-ai: true
  llms-txt: true
```

Como qualquer mudança em `fern/docs.yml`, validar primeiro com
`npm run fern:check` e depois com um preview
(`npx fern-api generate --docs --preview --id "ask-ai-llms-txt"`) antes de
publicar em produção — fluxo já coberto em `docs/fern-docs.md`.

## Prioridade sugerida

1. **Item 1** (MCP server via Fern) — reaproveita a spec já existente como
   fonte única, é o que mais conecta com o resto do trabalho de IA já em
   andamento no repo.
2. **Item 3** (Ask AI + llms.txt) — mudança pequena e isolada em `docs.yml`,
   baixo risco, testável em preview antes de produção.
3. **Item 2** (Postman MCP Server / workspace) — maior impacto no workflow,
   mas depende de confirmar nome de pacote/flags exatos na doc oficial da
   Postman antes de aplicar.
