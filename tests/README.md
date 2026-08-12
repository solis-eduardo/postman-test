# Testes

A maior parte dos testes funcionais desta API **vive dentro da própria collection**,
como scripts `afterResponse` (o equivalente moderno ao antigo "Tests" tab do Postman),
seguindo o padrão Git Native:

- Testes **globais** (aplicados a toda requisição): `.postman/collections/PetVerse API/.resources/definition.yaml`
  → chave `scripts`, entradas com `type: http:afterResponse`.
- Testes **por pasta**: `.postman/collections/PetVerse API/<Pasta>/.resources/definition.yaml`.
- Testes **por requisição**: dentro do próprio `*.request.yaml`, chave `scripts` com
  `type: afterResponse` (ex.: `Auth/Login.request.yaml`, `Pets/Create Pet.request.yaml`).

Isso é intencional: no schema v3 do Postman, scripts e asserções ficam versionados
junto da requisição a que pertencem, em vez de um arquivo de testes separado — o que
gera diffs de PR pequenos e legíveis por requisição alterada.

## O que fica aqui em `tests/`

Este diretório concentra apenas **massa de dados** para execuções orientadas a dados
(data-driven) e a documentação de como rodar a suíte:

- `data/pets.iteration-data.csv` e `data/pets.iteration-data.json` — linhas usadas
  para criar vários pets em lote, consumidas pelas variáveis `{{pet_name}}`,
  `{{pet_species}}` e `{{pet_breed}}` na requisição `Pets/Create Pet`.
- `data/pets.dataset.yaml` — exemplo (BETA) do recurso nativo `postman dataset`,
  a alternativa versionada ao CSV solto (ver `postman dataset --help`). Foi gerado com:
  ```bash
  postman dataset create tests/data/pets.dataset.yaml \
    --name "Pets de exemplo" \
    --description "Massa de dados para criação de pets em lote"
  ```
  Para popular esse dataset com uma fonte de dados real, use
  `postman dataset source add` (recurso ainda em BETA na Postman CLI).

## Como rodar

```bash
# suíte completa contra o ambiente Local
npx postman-cli collection run ".postman/collections/PetVerse API" \
  -e .postman/environments/Local.postman_environment.json

# somente a pasta Pets
npx postman-cli collection run ".postman/collections/PetVerse API" \
  -e .postman/environments/Local.postman_environment.json \
  -i "Pets"

# data-driven: cria um pet para cada linha do CSV
npx postman-cli collection run ".postman/collections/PetVerse API" \
  -e .postman/environments/Local.postman_environment.json \
  -i "Pets/Create Pet" \
  -d tests/data/pets.iteration-data.csv
```

Veja também `scripts/run-collection.sh` e `scripts/lint.sh`.
