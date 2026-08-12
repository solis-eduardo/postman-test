# postman-test — PetVerse API (collection fictícia)

Repositório de exemplo com uma API fictícia de clínica veterinária/petshop
(**PetVerse API**), montado para demonstrar o **padrão Git Native do Postman**:
a collection é versionada como *um arquivo YAML por requisição* (schema v3),
não como um único `.postman_collection.json`.

> Todo o conteúdo (endpoints, dados, e-mails, tokens) é fictício, para fins de
> demonstração/estudo do formato.

## Conteúdo

| Caminho | O quê |
|---|---|
| `postman/collections/PetVerse API/` | Collection no formato **v3 / Git Native** — pastas `Auth`, `Owners`, `Pets`, `Appointments`, `System`, cada requisição em seu próprio `*.request.yaml`, com scripts (pre-request/test) e exemplos de resposta |
| `postman/environments/` | 4 ambientes (Local, Development, Staging, Production) no formato **v3** (`*.environment.yaml`) |
| `postman/specs/openapi.yaml` | Especificação **OpenAPI 3.0** da API — fonte de verdade do contrato, validada com Redocly |
| `postman/documents/` | Documentação de referência da API, exposta como "Documents" no workspace |
| `postman/mocks/petverse-api/` | Mock server local (Node puro) gerado a partir da collection, com respostas revisadas |
| `postman/flows/` | Flow de exemplo: trigger HTTP → Login → Create Owner → Create Pet → Create Appointment |
| `tests/` | Massa de dados para execuções data-driven (CSV/JSON/dataset) + explicação de onde vivem os testes funcionais |
| `scripts/` | Scripts de apoio: lint da collection/spec, **verificação de alinhamento spec↔collection**, execução da collection |
| `docs/postman-git-native.md` | Explicação detalhada do padrão Git Native e da estrutura de arquivos |
| `dist/PetVerse API.postman_collection.json` | **Espelho v2.1** da collection, gerado automaticamente (`npm run export:v2`) — usado onde o formato v3 ainda não é aceito (ver "Compartilhando com clientes") |
| `.github/workflows/api-tests.yml` | CI: lint da collection/spec, alinhamento spec↔collection, checa se `dist/` está atualizado |
| `.github/workflows/docs-pages.yml` | CI: publica o portal Redoc (`postman/specs/openapi.yaml`) no GitHub Pages a cada push |

## Pré-requisitos

- [Node.js](https://nodejs.org/) 18+ (para rodar a Postman CLI via `npx`)
- Nenhuma conta/login é necessária para lint e execução local — apenas para
  recursos que envolvem a nuvem Postman (workspace, datasets remotos etc.)

## Uso rápido

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

# subir o mock local (porta 4500 por padrão) e testar
cd "postman/mocks/petverse-api" && node default.js &
curl http://localhost:4500/health
```

## Fluxo da API (para rodar de ponta a ponta)

1. `Auth/Login` — autentica e guarda `access_token`/`refresh_token` no ambiente.
2. `Owners/Create Owner` — cria um tutor e guarda `owner_id`.
3. `Pets/Create Pet` — cria um pet vinculado ao `owner_id` e guarda `pet_id`.
4. `Appointments/Create Appointment` — agenda uma consulta para o `pet_id`.
5. `Appointments/Cancel Appointment`, `Pets/Delete Pet`, `Owners/Delete Owner` — limpeza.

Essa é a ordem que a coleção assume dentro de cada pasta (`order` nos arquivos
`*.request.yaml`), então um `postman collection run` sem filtros já segue esse fluxo.

## Mantendo a spec e a collection alinhadas

Nada impede alguém de adicionar uma requisição só na collection (pela UI) ou só
um path na spec (editando `postman/specs/openapi.yaml`) e esquecer do outro
lado. `scripts/check_spec_alignment.py` compara os dois: lê todos os
`METHOD /path` da spec e todos os `*.request.yaml` da collection, normaliza
(`{{base_url}}`, `{{api_version}}`, `:param` → `{param}`) e aponta qualquer
endpoint que exista só de um lado. Já roda como parte de `npm run lint` e do CI.

```bash
python3 scripts/check_spec_alignment.py
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

O mock em `postman/mocks/petverse-api/` só roda local hoje
(`node default.js`, porta 4500). Pra virar uma URL pública que um cliente
acessa sem precisar rodar nada:
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
