# postman-test — PetVerse API (collection fictícia + aplicação Laravel)

Repositório de exemplo com uma API fictícia de clínica veterinária/petshop
(**PetVerse API**), montado para demonstrar o **padrão Git Native do Postman**:
a collection é versionada como *um arquivo YAML por requisição* (schema v3),
não como um único `.postman_collection.json`. Além da collection/spec, o
repositório também abriga a **aplicação Laravel** que implementa a API
descrita pela spec/collection.

> Todo o conteúdo (endpoints, dados, e-mails, tokens) é fictício, para fins de
> demonstração/estudo do formato.

> **Visão geral da integração Postman ↔ Fern** (o que configura o quê, como
> cada um se mantém atualizado): `docs/architecture.md`.

## Conteúdo

| Caminho | O quê |
|---|---|
| `app/`, `routes/`, `database/`, `config/`, `resources/`, `tests/Feature`, `tests/Unit` | **Aplicação Laravel** que implementa a PetVerse API |
| `postman/collections/PetVerse API/` | Collection no formato **v3 / Git Native** — pastas `Autenticação`, `Owners`, `Pets`, `Appointments`, `System`, cada requisição em seu próprio `*.request.yaml`, com scripts (pre-request/test) e exemplos de resposta |
| `postman/environments/` | 4 ambientes (Local, Development, Staging, Production) no formato **v3** (`*.environment.yaml`) |
| `postman/specs/openapi.yaml` | Especificação **OpenAPI 3.0** da API — fonte de verdade do contrato, validada com Redocly |
| `postman/documents/` | Documentação de referência da API, exposta como "Documents" no workspace |
| `postman/mocks/petverse-api/` | Mock server local (Node puro) gerado a partir da collection, com respostas revisadas |
| `postman/flows/` | Flow de exemplo: trigger HTTP → Login → Create Owner → Create Pet → Create Appointment |
| `fern/` | Config da **Fern Docs** (adquirida pela Postman) — `generators.yml` referencia `postman/specs/openapi.yaml` como fonte da API; publica em https://solis.docs.buildwithfern.com |
| `tests/data/` | Massa de dados para execuções data-driven (CSV/JSON/dataset) da collection |
| `tests/Feature`, `tests/Unit` | Testes automatizados (Pest) da aplicação Laravel |
| `scripts/` | Scripts de apoio: lint da collection/spec/Fern, **verificação de alinhamento spec↔collection**, execução da collection |
| `docs/architecture.md` | **Visão geral**: mapa pasta/arquivo → responsabilidade, como Postman e Fern se mantêm atualizados, ciclo de vida de uma mudança |
| `docs/postman-git-native.md` | Explicação detalhada do padrão Git Native, estrutura de arquivos e troubleshooting do Postman |
| `docs/fern-docs.md` | Setup completo da Fern: autenticação, preview/publicação, CI, troubleshooting e equivalente GitLab |
| `dist/PetVerse API.postman_collection.json` | **Espelho v2.1** da collection, gerado automaticamente (`npm run export:v2`) — usado onde o formato v3 ainda não é aceito (ver "Compartilhando com clientes") |
| `.github/workflows/api-tests.yml` | CI: lint da collection/spec, alinhamento spec↔collection, checa se `dist/` está atualizado |
| `.github/workflows/docs-pages.yml` | CI: publica o portal Redoc (`postman/specs/openapi.yaml`) no GitHub Pages a cada push |
| `.github/workflows/fern-check.yml` | CI: valida `fern/` (`fern check`) em PRs e pushes que tocam a config da Fern ou a spec |
| `.github/workflows/fern-docs-publish.yml` | CI: publica a Fern Docs (`fern generate --docs`) a cada push em `main` — requer o secret `FERN_TOKEN` |

## Setup do zero (checklist)

Passo a passo pra quem está pegando este repositório pela primeira vez —
tanto a parte Postman quanto a Fern. Cada passo linka pro detalhe/troubleshooting
correspondente; siga na ordem, porque cada etapa depende da anterior.

### 1. Clonar e instalar dependências

```bash
git clone https://github.com/solis-eduardo/postman-test.git
cd postman-test
npm install
```

### 2. Conectar o Postman Desktop (Native Git)

1. No Postman Desktop, abra a **raiz** deste repositório via Native Git
   (workspace → conectar repositório local).
2. Se aparecer **"Add a Git remote to continue"**: o repo local não tem
   remote configurado — não deve acontecer clonando daqui, mas se acontecer,
   `git remote add origin <url>`.
3. Se aparecer **"The .postman directory is missing"**: falta
   `.postman/resources.yaml` — não deve acontecer nesse repo (já está
   commitado), mas se sumir, veja como recriar em
   `docs/postman-git-native.md`.
4. O menu "Items" deve mostrar a collection **PetVerse API** (5 pastas, 16
   requisições) e 4 ambientes automaticamente. Se aparecer vazio, veja
   "Erros que já enfrentamos" em `docs/postman-git-native.md`.

### 3. Validar tudo localmente

```bash
npm run lint
```

Roda, nessa ordem: lint da collection (v3), validação da spec OpenAPI,
alinhamento spec↔collection, e `fern check`. Deve terminar sem erros — se
`fern check` falhar aqui, é só validação estrutural (não precisa de login),
então normalmente indica um problema real de config em `fern/`.

### 4. Autenticar e configurar a Fern

```bash
npx fern-api login                                    # autentica via GitHub
npx fern-api org get                                  # confirma a organização (deve ser "solis-com-br-s-team")
```

Se der `HTTP 403`, veja a tabela de erros em `docs/fern-docs.md` — geralmente
é `fern.config.json` com o slug de organização errado.

### 5. Gerar um preview antes de publicar

```bash
npx fern-api generate --docs --preview --id "meu-teste"
```

Confirma que a spec/config estão corretas sem afetar o site em produção. Veja
o link publicado, confira, e apague quando terminar:

```bash
npx fern-api docs preview delete "<url do preview>"
```

### 6. Configurar o CI (uma vez só, por quem for mantenedor)

```bash
npx fern-api token --organization solis-com-br-s-team
gh secret set FERN_TOKEN --repo solis-eduardo/postman-test --body "<token gerado>"
```

A partir daqui, todo push em `main` que tocar `fern/**` ou a spec publica
automaticamente via `.github/workflows/fern-docs-publish.yml`. Detalhes e
erros comuns desse passo (token de organização errada, domínio já
registrado) estão em `docs/fern-docs.md`.

### Resumo do que cada validação cobre

| Comando | O que valida |
|---|---|
| `npm run lint` | Collection v3 + spec OpenAPI + alinhamento entre as duas + config da Fern |
| `npm test` | Roda a collection de ponta a ponta contra o ambiente Local |
| `npm run export:v2` | Regenera o espelho v2.1 em `dist/` (CI falha se ficar desatualizado) |
| `npm run fern:check` | Só a config da Fern (`fern check`) |
| `npm run fern:dev` | Preview local da Fern (`fern docs dev`) |

## Aplicação Laravel (API)

A pasta raiz também contém uma aplicação **Laravel 12 / PHP 8.5** que serve
como implementação (em construção) da PetVerse API descrita pela spec/collection.

### Pré-requisitos

- PHP 8.5+ e Composer
- Node.js 18+ (assets do front-end, se aplicável)

### Setup

```bash
composer install
cp .env.example .env
php artisan key:generate
php artisan migrate
php artisan serve
```

### Rodando os testes

```bash
php artisan test --compact
```

## Pré-requisitos (collection/spec)

- [Node.js](https://nodejs.org/) 18+ (para rodar a Postman CLI via `npx`)
- Python 3 + `pip install pyyaml jsonschema` (para `scripts/check_spec_alignment.py`)
- Nenhuma conta/login é necessária para lint e execução local — apenas para
  recursos que envolvem a nuvem Postman (workspace, datasets remotos etc.)

## Uso rápido (collection/spec)

```bash
# validar collection (v3) e spec OpenAPI
npm run lint

# rodar a collection inteira contra o ambiente Local
npm test

# rodar contra Staging
npm run test:staging

# rodar só a pasta Pets, gerando um pet por linha do CSV de massa de dados
npx postman-cli collection run "postman/collections/PetVerse API" \
  -e "postman/environments/PetVerse API - Local.environment.yaml" \
  -i "Pets/Create Pet" \
  -d tests/data/pets.iteration-data.csv

# subir o mock local na porta que o ambiente Local espera, e testar
MOCK_PORT=$(grep -oP '^port:\s*\K\d+' "postman/mocks/petverse-api/config.yaml")
cd "postman/mocks/petverse-api" && PORT="$MOCK_PORT" node default.js &
curl "http://localhost:$MOCK_PORT/health"
```

> `config.yaml` (`port:`) e o ambiente **Local**
> (`postman/environments/PetVerse API - Local.environment.yaml`, `base_url`)
> são editados **separadamente** pela UI do Postman e precisam apontar pra
> mesma porta pra collection/flow conseguirem falar com o mock — o Postman
> não sincroniza isso sozinho. `default.js` cai pra `4500` se `PORT` não for
> definida. O CI (`api-tests.yml`) falha alto se essas duas portas
> divergirem, em vez de testar silenciosamente contra a errada.

## Fluxo da API (para rodar de ponta a ponta)

1. `Autenticação/Login` — autentica e guarda `access_token`/`refresh_token` no ambiente.
2. `Owners/Create Owner` — cria um tutor e guarda `owner_id`.
3. `Pets/Create Pet` — cria um pet vinculado ao `owner_id` e guarda `pet_id`.
4. `Appointments/Create Appointment` — agenda uma consulta para o `pet_id`.
5. `Appointments/Cancel Appointment`, `Pets/Delete Pet`, `Owners/Delete Owner` — limpeza.

Essa é a ordem que a coleção assume dentro de cada pasta (`order` nos arquivos
`*.request.yaml`), então um `postman collection run` sem filtros já segue esse fluxo.

## Mantendo a spec e a collection alinhadas

Nada impede alguém de adicionar uma requisição só na collection (pela UI) ou só
um path na spec (editando `postman/specs/openapi.yaml`) e esquecer do outro
lado — ou editar os dois, mas de um jeito que não bate mais. `scripts/check_spec_alignment.py`
compara os dois em três frentes:

1. **Endpoints** — todo `METHOD /path` da spec tem uma requisição
   correspondente na collection (normaliza `{{base_url}}`, `{{api_version}}`,
   `:param` → `{param}`), e vice-versa.
2. **Tags/agrupamento** — a pasta que contém a requisição na collection bate
   com a(s) tag(s) da operação na spec (é o que dá nome às seções no site da
   Fern — ver `docs/fern-docs.md`).
3. **Schema do body/response** — o corpo de requisição e cada resposta de
   exemplo salva na collection validam contra o `requestBody`/`responses`
   (JSON Schema) da spec. Variáveis de collection ainda não resolvidas
   (`{{pet_species}}`) são tratadas como "presente, tipo desconhecido" em vez
   de comparadas literalmente, pra não virar falso-positivo.

Já roda como parte de `npm run lint` e do CI.

```bash
python3 scripts/check_spec_alignment.py    # requer PyYAML + jsonschema
```

No app Postman, o caminho nativo pra isso é **linkar a spec à collection**
(API Builder → "Define" → apontar para `postman/specs/openapi.yaml`, depois
"Generate collection" ou "Validate") — o Postman então sinaliza divergências
direto na UI. O script acima é o mesmo tipo de checagem, mas versionado e
rodável no CI sem depender da UI.

## Editando pelo app Postman

Basta apontar o recurso **Native Git** do Postman (workspace → conectar
repositório) para este repositório. Ele vai reconhecer
`postman/collections/PetVerse API` como uma collection e
`postman/environments/*.environment.yaml` como ambientes.

Veja `docs/postman-git-native.md` para o detalhamento completo do formato.

## Documentação com Fern

A [Fern](https://buildwithfern.com) foi adquirida pela Postman em janeiro de
2026 e é a nova plataforma de documentação/SDKs. A pasta `fern/` versiona a
configuração de um site de docs gerado a partir da nossa spec — **fonte de
verdade única**: `fern/generators.yml` referencia `postman/specs/openapi.yaml`
(o mesmo arquivo que o portal Redoc e a collection já usam), então documentar
a API uma vez alimenta os três.

```
fern/
├── fern.config.json   # organização Fern (solis-com-br-s-team) + versão do CLI
├── generators.yml     # api.specs -> ../postman/specs/openapi.yaml (fonte real da API)
├── docs.yml           # navegação, tema, instância publicada
└── .gitignore
```

```bash
npm run fern:check     # valida fern/ + a spec referenciada
npm run fern:dev       # preview local (fern docs dev)
```

Veja **`docs/fern-docs.md`** para o fluxo completo: autenticação, preview vs.
produção, configuração do CI (`FERN_TOKEN`), a tabela de erros reais que já
enfrentamos configurando isso (organização errada, URL duplicada, domínio já
registrado, token de conta trocada) e o equivalente pra GitLab.

## Compartilhando com clientes

Este repositório é **público**: https://github.com/solis-eduardo/postman-test
— qualquer cliente pode acessá-lo diretamente, sem convite.

### 1. Portal de referência (OpenAPI/Redoc) — já no ar

**https://solis-eduardo.github.io/postman-test/**

Gerado automaticamente por `.github/workflows/docs-pages.yml` a partir de
`postman/specs/openapi.yaml` toda vez que a spec muda. É o link mais simples
pra mandar pra um cliente: não exige conta no Postman, é só uma página web.

### 2. Importar a collection direto no Postman do cliente

O botão oficial "Run in Postman" (aquele badge clicável) só funciona quando a
collection já está publicada num workspace público do Postman — o link dele
usa `entityId`/`workspaceId` internos, não uma URL qualquer. Isso está
bloqueado hoje (ver item 1 abaixo), então o caminho que funciona **agora, sem
depender do Postman Cloud**, é a importação por link:

1. No Postman do cliente: **Import → Link**
2. Colar:
   ```
   https://raw.githubusercontent.com/solis-eduardo/postman-test/main/dist/PetVerse API.postman_collection.json
   ```
3. Pronto — a collection inteira (16 requisições, scripts, exemplos) entra no
   workspace dele, editável, sem precisar clonar o repositório.

Esse arquivo em `dist/` é um **espelho v2.1** gerado a partir da collection v3
(`npm run export:v2`) só porque o import-por-link do Postman entende v2.1, não
a árvore de arquivos v3. O CI falha se alguém atualizar a collection e
esquecer de regenerar esse espelho.

Quando o item 1 abaixo for resolvido (workspace publicado), dá pra trocar isso
pelo badge oficial de verdade:
```markdown
[![Run in Postman](https://run.pstmn.io/button.svg)](<link gerado pelo Postman em Share → Run in Postman>)
```

### 3. Ambientes

Cada cliente usa o `postman/environments/*.environment.yaml` correspondente
(Development/Staging/Production) — ou importa também por link raw do GitHub,
mesmo mecanismo do item acima.

### 4. Sandbox rodando (mock)

O mock em `postman/mocks/petverse-api/` só roda local hoje (ver "Uso rápido"
acima). Pra virar uma URL pública que um cliente acessa sem precisar rodar
nada:
- **Nativo do Postman**: clique direito na collection no sidebar → devia
  aparecer "Mock collection" (gera uma URL hospedada pelo Postman a partir dos
  mesmos exemplos). Se esse botão não aparecer, é provável que seja a mesma
  limitação do item 1 (recursos de nuvem ainda não cobrindo collections v3
  "multi-protocol"/git-native) — vale tentar de novo depois que isso for
  liberado, ou testar criando uma collection duplicada a partir do
  `dist/PetVerse API.postman_collection.json` (v2.1 clássico) só pra mockar.
- **Deploy próprio**: `postman/mocks/petverse-api/default.js` é só Node puro
  (`http.createServer`, sem dependências) — dá pra subir em qualquer host
  (Render, Railway, Fly.io, um VPS que vocês já tenham) com
  `node default.js` e a porta via `PORT`. Não tenho como fazer esse deploy
  por vocês (precisa de conta/credenciais no host escolhido) — me diga qual
  vocês usam e eu preparo o `Dockerfile`/config específico.

### 5. Workspace público/compartilhado (colaboração, não só leitura)

Se o cliente vai colaborar (comentar, sugerir mudança, fazer fork) em vez de
só consumir docs:

- **Team → Workspace → Manage roles**: convidar por e-mail com papel
  Viewer/Editor. Exige que o cliente crie conta no Postman (grátis) e que
  vocês tenham espaço de convite no plano do time.
- **Visibilidade do workspace**: em Workspace → Visibility, mudar de
  `Private`/`Team` para `Public` — qualquer pessoa com o link acessa e pode
  fazer fork, sem convite individual. É o equivalente ao que fizemos com o
  repositório GitHub agora.
- **Partner Workspace** (recurso pago, times Enterprise): meio-termo entre os
  dois — compartilha com uma organização externa específica com mais
  controle de permissões do que um workspace totalmente público.

### 1. Por que "Publish docs" está bloqueado

A mensagem `"Publish support for multi-protocol collections coming soon"`
indica que o recurso de **Publish** (a documentação hospedada clássica do
Postman, diferente do portal Redoc do item acima) ainda não foi liberado pra
collections no formato v3/git-native — só pra collections v2.1 clássicas.
Não há nada a configurar do nosso lado; é uma limitação atual da plataforma.
Workaround enquanto isso não sai do ar: publicar a partir do
`dist/PetVerse API.postman_collection.json` (v2.1) — importe esse arquivo como
uma collection **separada e não vinculada ao Git** no workspace, e use
"Publish" nela. Ela deixa de sincronizar automaticamente com a v3 (por isso
"separada"), então regenere/reimporte quando o `dist/` mudar — ou use o portal
Redoc (item acima), que já é 100% automático.
