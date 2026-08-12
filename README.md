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
| `postman/environments/` | 4 ambientes (Local, Development, Staging, Production) no formato clássico de ambiente Postman |
| `postman/specs/openapi.yaml` | Especificação **OpenAPI 3.0** da API — fonte de verdade do contrato, validada com Redocly |
| `tests/` | Massa de dados para execuções data-driven (CSV/JSON/dataset) + explicação de onde vivem os testes funcionais |
| `scripts/` | Scripts de apoio (lint, execução da collection) usando a **Postman CLI** |
| `docs/postman-git-native.md` | Explicação detalhada do padrão Git Native e da estrutura de arquivos |
| `.github/workflows/api-tests.yml` | CI de exemplo: lint da collection/spec + execução via Postman CLI |

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
  -e postman/environments/Local.postman_environment.json \
  -i "Pets/Create Pet" \
  -d tests/data/pets.iteration-data.csv
```

## Fluxo da API (para rodar de ponta a ponta)

1. `Auth/Login` — autentica e guarda `access_token`/`refresh_token` no ambiente.
2. `Owners/Create Owner` — cria um tutor e guarda `owner_id`.
3. `Pets/Create Pet` — cria um pet vinculado ao `owner_id` e guarda `pet_id`.
4. `Appointments/Create Appointment` — agenda uma consulta para o `pet_id`.
5. `Appointments/Cancel Appointment`, `Pets/Delete Pet`, `Owners/Delete Owner` — limpeza.

Essa é a ordem que a coleção assume dentro de cada pasta (`order` nos arquivos
`*.request.yaml`), então um `postman collection run` sem filtros já segue esse fluxo.

## Editando pelo app Postman

Basta apontar o recurso **Native Git** do Postman (workspace → conectar
repositório) para este repositório. Ele vai reconhecer
`postman/collections/PetVerse API` como uma collection e
`postman/environments/*.postman_environment.json` como ambientes.

Veja `docs/postman-git-native.md` para o detalhamento completo do formato.
