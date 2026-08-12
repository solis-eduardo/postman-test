# O padrão Git Native do Postman

Este repositório guarda a collection **PetVerse API** no *collection schema v3*
do Postman: em vez de um único JSON gigante (`*.postman_collection.json`, schema
v2.1), cada pasta, requisição e exemplo vira um arquivo YAML próprio em disco.
É esse formato que o recurso **Native Git** do Postman lê e escreve quando você
conecta um workspace a um repositório Git.

> Todo o layout abaixo foi gerado e validado com a **Postman CLI oficial**
> (`postman collection migrate` / `postman collection lint`), não escrito à mão —
> garantindo que corresponde ao schema real, e não a uma aproximação.

## Por que isso existe

O formato antigo (v2.1) é um único arquivo JSON com a collection inteira. Isso é
ótimo para importar/exportar, mas péssimo para Git: qualquer alteração em uma
única requisição gera um diff enorme e ilegível, e dois devs mexendo em
requisições diferentes praticamente sempre entram em conflito de merge.

O schema v3 resolve isso quebrando a collection em um arquivo por requisição
(e por exemplo, por pasta etc.), então o diff de um PR mostra exatamente o que
mudou — e só isso.

## Estrutura gerada

```
.postman/collections/PetVerse API/
├── .resources/
│   └── definition.yaml              # metadados da collection: nome, descrição,
│                                     # variáveis, auth (bearer) e scripts globais
│                                     # (pre-request/test aplicados a toda requisição)
├── Auth/
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

Este repositório foi construído para já nascer nesse formato, então basta
apontar o Native Git do Postman para a pasta `.postman/collections/PetVerse API`
(ou o repositório inteiro) para começar a editar pela UI também.

## Como regenerar/atualizar este layout

Se preferir editar a collection como um único JSON (schema v2.1, mais familiar) e
depois regerar os arquivos v3:

```bash
# 1. edite/exporte um .postman_collection.json (v2.1)
# 2. migre para o schema v3 (git-native)
npx postman-cli collection migrate petverse.postman_collection.json \
  -o ".postman/collections/PetVerse API"

# 3. valide o resultado
npx postman-cli collection lint ".postman/collections/PetVerse API"
```

## Ambientes e specs

- **Ambientes** (`.postman/environments/*.postman_environment.json`) continuam no
  formato clássico (v2.1) de ambiente — é o formato estável e documentado que o
  Postman, a Postman CLI e o Newman entendem hoje.
- **Spec OpenAPI** (`specs/openapi.yaml`) é a fonte de verdade do contrato da API,
  mantida à parte e validada com `@redocly/cli lint` (ver `scripts/lint.sh`). No
  Postman, é comum linkar essa spec à collection para manter as duas em sincronia
  (feature "Generate/validate from spec").
