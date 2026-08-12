# O padrão Git Native do Postman

> Este guia usa como estudo de caso o projeto de referência de onde este kit
> foi extraído: uma collection chamada **PetVerse API**, com pastas
> `Autenticação`, `Owners`, `Pets`, `Appointments`, `System`. Troque
> "PetVerse API" pelo valor de `COLLECTION_NAME` no seu `postman-fern.env`
> ao aplicar os exemplos.

Uma collection Postman no *collection schema v3*: em vez de um único JSON
gigante (`*.postman_collection.json`, schema v2.1), cada pasta, requisição e
exemplo vira um arquivo YAML próprio em disco. É esse formato que o recurso
**Native Git** do Postman lê e escreve quando você conecta um workspace a um
repositório Git.

> Todo o layout abaixo foi gerado e validado com a **Postman CLI oficial**
> (`postman collection migrate` / `postman collection lint`), não escrito à mão —
> garantindo que corresponde ao schema real, e não a uma aproximação.

> A documentação publicada da API (Fern, adquirida pela Postman) tem sua
> própria config em `fern/`, coberta em `docs/fern-docs.md` — este arquivo
> cobre só o formato da collection/ambientes/etc.

## Por que isso existe

O formato antigo (v2.1) é um único arquivo JSON com a collection inteira. Isso é
ótimo para importar/exportar, mas péssimo para Git: qualquer alteração em uma
única requisição gera um diff enorme e ilegível, e dois devs mexendo em
requisições diferentes praticamente sempre entram em conflito de merge.

O schema v3 resolve isso quebrando a collection em um arquivo por requisição
(e por exemplo, por pasta etc.), então o diff de um PR mostra exatamente o que
mudou — e só isso.

## Estrutura gerada

A raiz que o Postman gerencia dentro do repositório é a pasta **`postman/`**
(sem ponto) — é ela que o app cria automaticamente na primeira vez que abre uma
pasta via Native Git, com as subpastas `collections/`, `environments/`,
`specs/`, `documents/`, `flows/`, `globals/` e `mocks/`. Confirmado
observando o próprio Postman Desktop gerar esse esqueleto ao abrir um repo
pela primeira vez (inclusive um `postman/globals/workspace.globals.yaml`
vazio). Uma tentativa usando `.postman/` (com ponto) como raiz falhou — o app
simplesmente não reconheceu, e o menu "Items" ficava vazio porque ele estava
olhando para `postman/`, não para `.postman/`.

```
postman/collections/<COLLECTION_NAME>/
├── .resources/
│   └── definition.yaml              # metadados da collection: nome, descrição,
│                                     # variáveis, auth (bearer) e scripts globais
│                                     # (pre-request/test aplicados a toda requisição)
├── Autenticação/                    # exemplo real do projeto de referência
│   ├── .resources/
│   │   ├── definition.yaml          # metadados da pasta (ordem de exibição etc.)
│   │   └── Login.resources/
│   │       └── examples/
│   │           ├── 200 - Login bem-sucedido.example.yaml
│   │           └── 401 - Credenciais inválidas.example.yaml
│   ├── Login.request.yaml
│   ├── Refresh Token.request.yaml
│   └── Logout.request.yaml
├── Owners/  Pets/  Appointments/  System/   (mesmo padrão acima)
```

Convenções do schema (validadas via `postman collection lint`):

| Elemento | Onde mora | Observações |
|---|---|---|
| Collection/pasta | `<pasta>/.resources/definition.yaml` | chave `$kind: collection`; raiz tem `name`, `description`, `variables`, `auth`, `scripts`; pastas filhas só têm `order` (índice fracionário de ordenação) |
| Requisição | `<pasta>/<Nome da requisição>.request.yaml` | `$kind: http-request`; método, url, headers, query params, body, `scripts` (`beforeRequest`/`afterResponse` — o antigo par pre-request/test) |
| Exemplo de resposta | `<pasta>/.resources/<Nome da requisição>.resources/examples/<nome>.example.yaml` | `$kind: http-example`; contém a requisição original e a resposta simulada |
| Scripts | inline dentro do `.request.yaml`/`definition.yaml`, chave `scripts[].code` | não ficam em arquivos `.js` separados — o texto do script mora dentro do próprio YAML |

Os scripts globais na raiz usam `type: http:beforeRequest` / `http:afterResponse`;
os scripts por requisição usam `type: beforeRequest` / `afterResponse` (sem o
prefixo `http:`) — isso também veio direto da CLI, não é escolha nossa.

## Como isso se conecta ao app Postman

No Postman desktop/web, ao habilitar **Native Git** num workspace e apontar para
um repositório:

1. O Postman clona/observa o repo e passa a ler/escrever collections, ambientes,
   specs, mocks etc. como arquivos locais em vez de só na nuvem.
2. Qualquer edição feita na UI do Postman é refletida nos arquivos deste
   formato (`*.request.yaml` etc.) — e vice-versa: editar o YAML aqui e dar
   `git pull`/commit reflete de volta na UI.
3. Você trabalha com branches, PRs e code review normalmente, como faria com
   qualquer outro código.

Basta abrir a raiz do repositório (não a subpasta da collection) via Native
Git no Postman Desktop, que ele reconhece `postman/collections/<COLLECTION_NAME>`
como uma collection e `postman/environments/*.environment.yaml` como
ambientes automaticamente, sem precisar apontar manualmente para nada.

### O arquivo `.postman/resources.yaml`

Além de `postman/`, o app mantém um `.postman/resources.yaml` (com ponto) com
o id do workspace ao qual o repo está ligado:

```yaml
workspace:
  id: <uuid do workspace>

localResources:
  specs:
    - ../caminho/para/arquivo/fora/de/postman/
```

A regra observada na prática: **tudo que está dentro de `postman/` é
auto-descoberto** — não precisa ser listado. `localResources` só existe para
registrar arquivos que vivem *fora* de `postman/`. Como todo o conteúdo deste
kit já mora dentro de `postman/`, esse arquivo tende a ser recriado
automaticamente pelo próprio app só com a referência do workspace.

Recomendamos **versionar** `.postman/resources.yaml`: é ele que faz qualquer
pessoa (ou máquina) que abra a pasta cair automaticamente no mesmo workspace,
sem configurar nada manualmente. Se o workspace referenciado for pessoal (não
de time), considere adicionar `.postman/resources.yaml` ao `.gitignore` em
vez disso, para cada colaborador apontar para o próprio workspace.

## Como regenerar/atualizar este layout

Se preferir editar a collection como um único JSON (schema v2.1, mais familiar) e
depois regerar os arquivos v3:

```bash
# 1. edite/exporte um .postman_collection.json (v2.1)
# 2. migre para o schema v3 (git-native)
npx postman-cli collection migrate minha-api.postman_collection.json \
  -o "postman/collections/<COLLECTION_NAME>"

# 3. valide o resultado
npx postman-cli collection lint "postman/collections/<COLLECTION_NAME>"
```

## Ambientes e specs

- **Ambientes** também têm um formato v3 (`postman/environments/*.environment.yaml`,
  chaves `name` + `values: [{key, value}]`). Diferente das collections, a
  **Postman CLI ainda não tem um comando `environment migrate`** — quem faz essa
  conversão hoje é só o próprio Postman Desktop: ele detecta um
  `.postman_environment.json` (v2.1) solto na pasta `postman/environments/` e
  oferece "Convert to v3" na UI, que reescreve o arquivo como
  `<Nome>.environment.yaml` e apaga o `.json` antigo. A CLI já sabe **ler** o
  formato novo (`collection run -e arquivo.environment.yaml` funciona
  normalmente), só não sabe **gerar/migrar** ainda.
- **Spec OpenAPI** (`postman/specs/openapi.yaml`) é a fonte de verdade do contrato da API,
  mantida à parte e validada com `@redocly/cli lint` (ver `scripts/lint.sh`).
  Diferente de collections e ambientes, ela **não é auto-descoberta** só por
  estar dentro de `postman/specs/` — precisou ser registrada explicitamente em
  `.postman/resources.yaml`, em `localResources.specs`. Sem essa entrada, o
  arquivo existe em disco mas não aparece no menu "Items" do app.
- **Alinhamento spec ↔ collection**: nada garante automaticamente que todo
  endpoint da spec tem uma requisição correspondente na collection (e
  vice-versa), que a pasta bate com a tag, ou que o body/response bate com o
  schema — são dois artefatos editados separadamente. `scripts/check_spec_alignment.py`
  faz essa checagem localmente em três frentes (endpoints, tags/pasta, schema
  de body/response via `jsonschema`) e roda como parte de `npm run lint` e do
  CI. No app Postman, o equivalente nativo pra endpoints é linkar a spec à
  collection via API Builder ("Define" → "Generate collection" / "Validate"),
  que sinaliza drift direto na UI — mas isso não cobre tags nem schema.

## Documents, Flows e Mocks

- **Documents** (`postman/documents/*.md`) — Markdown puro. Baixo risco: mesmo
  que o Postman não reconheça o arquivo como um "Document" formal, ele
  continua sendo Markdown válido e útil. Se não aparecer listado no app, o
  próximo passo é o mesmo usado para specs: registrar em `localResources` no
  `.postman/resources.yaml`.
- **Mocks** (`postman/mocks/<slug>/`) — cada mock local é uma pasta com:
  - `config.yaml`: `id`, `name`, `slug`, `protocol`, `port`,
    `associations: [{entityType: collection, entityId, relation: source, syncEnabled}]`
    (liga o mock a uma collection do workspace) e
    `scenarios: [{name, path: ./default.js, default: true}]`.
  - `default.js`: um handler **Node puro** (`http.createServer`), sem framework
    — casa `req.method` + uma regex do `pathname` por endpoint. O Postman gera
    esse arquivo automaticamente a partir da collection: para cada requisição
    que tem um exemplo de resposta salvo (`.resources/**/examples/*.example.yaml`),
    ele usa esse exemplo como corpo/status; para as que não têm exemplo, gera um
    placeholder `{"message": "Hi from postman mock"}` com 200.

  O mock local **testa a porta contra o ambiente Local** antes de subir (ver
  `.github/workflows/api-tests.yml`) — os dois são configs editadas
  separadamente pela UI do Postman e não se sincronizam sozinhas.

- **Flows** (`postman/flows/*.flow`) — um único arquivo JSON (não YAML) por
  flow, versão do schema em `version`, o grafo em `flow.nodes`/`flow.connections`,
  e `flow.scenarios` para os gatilhos. Cada nó `task/http-request@2` referencia
  um `.request.yaml` pelo caminho (não duplica a requisição).

  **Portas das conexões — confirmado no app, não deduzido pela doc:**
  - **Trigger → primeiro request**: `sourcePort: "data"` (porta de saída de
    um `ev/endpoint@3`).
  - **Request → request seguinte**: `sourcePort: "success"` — porta de saída
    de um `task/http-request@2` (ele tem pelo menos duas saídas possíveis,
    sucesso/erro). **Não** é `"data"` — extrapolamos isso errado a princípio
    copiando o padrão do trigger, e só descobrimos o valor certo abrindo o
    flow no Postman Desktop, que reescreveu o arquivo com as conexões
    corretas.
  - `targetPort: "AI"` é o nome fixo da porta de entrada de
    `task/http-request@2`, indiferente de quem é a origem.
  - `ignoreTestResults` (em `config` de cada node): com `true` (valor default
    gerado pelo Postman), o flow roda a requisição mas **ignora** se os
    `pm.test(...)` dela passaram ou falharam. Se a collection tem boa
    cobertura de teste, provavelmente você quer `false` em vez do default.

## Erros que já enfrentamos (e a causa real)

Ver `docs/TROUBLESHOOTING.md` pra tabela consolidada (Postman + Fern + CI
juntos). Resumo da parte Postman:

| Erro | Causa real | Correção |
|---|---|---|
| `Add a Git remote to continue` (ao abrir a pasta no Postman Desktop) | O Postman exige um remote git configurado pra continuar — não basta ser um repositório git local solto | `git remote add origin <url>` apontando pra um repositório de verdade |
| `The .postman directory is missing` | O `.postman/resources.yaml` (com o `workspace.id`) foi apagado/nunca existiu | Recriar `.postman/resources.yaml` com `workspace: id: <uuid>` — o app volta a reconhecer o vínculo |
| Menu "Items" fica vazio mesmo com a collection presente no disco | A raiz gerenciada pelo Postman é `postman/` (sem ponto), não `.postman/` (com ponto) | Mover collection/ambientes/specs pra dentro de `postman/` na raiz do repo |
| `postman/environments/*.postman_environment.json` — "Legacy v2 JSON file found. Convert to v3" | Ambientes ainda tinham o formato clássico (v2.1); a Postman CLI **não tem** comando de migração pra ambientes (só pra collections) | Usar o botão "Convert to v3" do próprio Postman Desktop |
| Spec (`postman/specs/openapi.yaml`) existe no disco mas não aparece no sidebar | Diferente de collections/ambientes, specs **não são auto-descobertas** só por estarem dentro de `postman/specs/` | Registrar explicitamente em `.postman/resources.yaml`, em `localResources.specs` |
| `Publish support for multi-protocol collections coming soon` (botão Publish docs) | Collections v3/git-native ainda não têm suporte a esse pipeline de publicação — limitação atual da plataforma | Ver `## O espelho v2.1 em dist/` abaixo, ou usar o portal Redoc (`docs-pages.yml`) |
| "Push to Cloud" → `Repository does not match workspace` mesmo com o remote correto | Provável cache do app associando a pasta a um estado antigo (remover `.git` da URL do remote não resolveu) | Fechar e reabrir o Postman Desktop **por completo** (sair do processo, não só a janela) |
| Renomear uma pasta na collection não muda o nome da seção na Fern | A Fern não lê a collection, só a spec — a navegação vem das `tags` do OpenAPI | Renomear a tag correspondente em `postman/specs/openapi.yaml` também (`tags[].name` + `tags: [...]` de cada operação) |

## O espelho v2.1 em dist/ (por que existe)

Vários recursos de distribuição do Postman (Publish docs, o botão oficial
"Run in Postman", às vezes até Mock Servers) ainda não suportam collections
v3/git-native — o próprio Postman retorna
`"Publish support for multi-protocol collections coming soon"` ao tentar.
Como isso é uma limitação da plataforma (não algo que dá pra contornar
editando arquivos locais), o kit mantém um espelho automático em formato v2.1
clássico, que esses recursos entendem:

- `scripts/export_v2_collection.py` — lê `postman/collections/<COLLECTION_NAME>/`
  (a fonte de verdade, v3) e monta o JSON v2.1 equivalente: `variables` (dict
  → array), `auth` (`credentials.token` → `bearer[0].value`), `scripts`
  (`http:beforeRequest`/`http:afterResponse` → `event[].listen`
  `prerequest`/`test`), pastas e requests na ordem dada pelo campo `order` de
  cada `definition.yaml`/`request.yaml`, exemplos (`*.example.yaml` →
  `response[]`).
- `scripts/normalize_v2_collection.cjs` — segunda etapa, via o SDK oficial
  (`postman-collection`, a lib que Postman/Newman usam por baixo dos panos).
  Necessária porque um `url: {raw: "..."}` sozinho (sem `host`/`path`/`query`
  estruturados) **não é reconstruído** pelo parser do SDK — testado:
  `new sdk.Url({raw: "..."}).toString()` retorna `""`. O normalizador expande
  cada URL com `new sdk.Url(rawString).toJSON()` (dessa vez passando a string
  pura, que o parser processa corretamente) antes de validar com
  `new sdk.Collection(...)`.
- Testado no projeto de referência com **round-trip completo**: o JSON
  gerado foi migrado de volta pra v3 com `postman collection migrate` e
  lintado — mesma contagem de requests e exemplos, lint sem erros.
- `npm run export:v2` roda as duas etapas. O CI (`api-tests.yml`) regenera e
  **auto-commita** `dist/` sozinho em push na `main` (em PR, só falha e pede
  pra rodar local — não faz sentido o Actions commitar numa branch alheia).

## Por que não usar "Generate spec from collection" como fonte de verdade

O Postman consegue gerar uma spec automaticamente a partir de uma collection
(e manter as duas sincronizadas via um `.postman/workflows.yaml` com
`syncSpecToCollection`/`syncCollectionToSpec`). Testamos isso no projeto de
referência — a spec gerada tinha problemas reais o suficiente pra não virar
a fonte de verdade do contrato:

- `servers[0].url: '{{base_url}}'` — sintaxe de variável do Postman, **inválida**
  em OpenAPI puro (`no-undefined-server-variable`, erro de lint, não warning).
- `{{api_version}}` virou parâmetro de path literal (`/{api_version}/pets`) em
  vez de resolver para `/v1/pets`.
- **Nenhuma operação teve `requestBody` gerado** — a geração parte só das
  respostas de exemplo salvas na collection, não dos corpos de requisição.
- Operações sem exemplo salvo saíram com `responses: {}` (nenhum status
  documentado).
- Sem `components.schemas`/`components.parameters` — tudo inline e duplicado
  por operação.

Ou seja: é um bom ponto de partida (zero esforço, direto da collection), mas
documenta "o que a collection já respondeu alguma vez", não "o que a API
aceita". Este kit mantém `postman/specs/openapi.yaml`, escrita à mão e mais
completa, como fonte de verdade.
