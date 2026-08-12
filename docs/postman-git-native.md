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

A raiz que o Postman gerencia dentro do repositório é a pasta **`postman/`**
(sem ponto) — é ela que o app cria automaticamente na primeira vez que abre uma
pasta via Native Git, com as subpastas `collections/`, `environments/`,
`specs/`, `documents/`, `flows/`, `globals/` e `mocks/`. Foi confirmado
observando o próprio Postman Desktop gerar esse esqueleto ao abrir este repo
(inclusive um `postman/globals/workspace.globals.yaml` vazio). Uma tentativa
anterior aqui usou `.postman/` (com ponto) como raiz e o app simplesmente não
reconheceu — o menu "Items" ficava vazio porque ele estava olhando para
`postman/`, não para `.postman/`.

```
postman/collections/PetVerse API/
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

Este repositório foi construído para já nascer nesse formato: basta abrir a
raiz do repositório (não a subpasta da collection) via Native Git no Postman
Desktop, que ele reconhece `postman/collections/PetVerse API` como uma
collection e `postman/environments/*.environment.yaml` como ambientes
automaticamente, sem precisar apontar manualmente para nada.

### O arquivo `.postman/resources.yaml`

Além de `postman/`, o app mantém um `.postman/resources.yaml` (com ponto,
ignorado pelo `.gitignore` do próprio Postman em alguns fluxos, mas aqui optamos
por deixá-lo versionado) com o id do workspace ao qual o repo está ligado:

```yaml
workspace:
  id: <uuid do workspace>

localResources:
  specs:
    - ../caminho/para/arquivo/fora/de/postman/
```

A regra observada na prática: **tudo que está dentro de `postman/` é
auto-descoberto** — não precisa ser listado. `localResources` só existe para
registrar arquivos que vivem *fora* de `postman/` (por exemplo, se você
preferisse manter `specs/openapi.yaml` na raiz do repo em vez de movê-lo para
`postman/specs/`). Como todo o conteúdo deste repositório já mora dentro de
`postman/`, esse arquivo tende a ser recriado automaticamente pelo próprio app
só com a referência do workspace, sem precisar de `localResources`.

Neste repositório optamos por **versionar** `.postman/resources.yaml`: é ele
que faz qualquer pessoa (ou máquina) que abra a pasta cair automaticamente no
mesmo workspace, sem configurar nada manualmente — é essencialmente o
equivalente do Postman a um arquivo de config de projeto compartilhado. Se o
workspace referenciado for pessoal (não de time), considere adicionar
`.postman/resources.yaml` ao `.gitignore` em vez disso, para cada colaborador
apontar para o próprio workspace.

## Como regenerar/atualizar este layout

Se preferir editar a collection como um único JSON (schema v2.1, mais familiar) e
depois regerar os arquivos v3:

```bash
# 1. edite/exporte um .postman_collection.json (v2.1)
# 2. migre para o schema v3 (git-native)
npx postman-cli collection migrate petverse.postman_collection.json \
  -o "postman/collections/PetVerse API"

# 3. valide o resultado
npx postman-cli collection lint "postman/collections/PetVerse API"
```

## Ambientes e specs

- **Ambientes** também têm um formato v3 (`postman/environments/*.environment.yaml`,
  chaves `name` + `values: [{key, value}]`). Diferente das collections, a
  **Postman CLI ainda não tem um comando `environment migrate`** — quem faz essa
  conversão hoje é só o próprio Postman Desktop: ele detecta um
  `.postman_environment.json` (v2.1) solto na pasta `postman/environments/` e
  oferece "Convert to v3" na UI, que reescreve o arquivo como
  `<Nome>.environment.yaml` e apaga o `.json` antigo. Foi assim que os 4
  ambientes deste repositório foram convertidos — não escrevemos esse YAML à
  mão. A CLI já sabe **ler** o formato novo (`collection run -e arquivo.environment.yaml`
  funciona normalmente), só não sabe **gerar/migrar** ainda.
- **Spec OpenAPI** (`postman/specs/openapi.yaml`) é a fonte de verdade do contrato da API,
  mantida à parte e validada com `@redocly/cli lint` (ver `scripts/lint.sh`).
  Diferente de collections e ambientes, ela **não é auto-descoberta** só por
  estar dentro de `postman/specs/` — precisou ser registrada explicitamente em
  `.postman/resources.yaml`, em `localResources.specs`. Sem essa entrada, o
  arquivo existe em disco mas não aparece no menu "Items" do app.
- **Alinhamento spec ↔ collection**: nada garante automaticamente que todo
  endpoint da spec tem uma requisição correspondente na collection (e
  vice-versa) — são dois artefatos editados separadamente. `scripts/check_spec_alignment.py`
  faz essa checagem localmente (parseia os `paths` do OpenAPI e os `method`/`url`
  de cada `*.request.yaml`, normaliza `{{base_url}}`/`{{api_version}}`/`:param`
  e compara os dois conjuntos) e roda como parte de `npm run lint` e do CI. No
  app Postman, o equivalente nativo é linkar a spec à collection via API
  Builder ("Define" → "Generate collection" / "Validate"), que sinaliza drift
  direto na UI.

## Documents, Flows e Mocks

- **Documents** (`postman/documents/*.md`) — Markdown puro. Criamos um exemplo
  (`Guia da API PetVerse.md`) com o mesmo raciocínio da spec: baixo risco, já
  que mesmo que o Postman não reconheça o arquivo como um "Document" formal,
  ele continua sendo Markdown válido e útil. **Ainda não confirmamos** se ele
  aparece listado no app — se não aparecer, o próximo passo é o mesmo usado
  para specs: registrar em `localResources` no `.postman/resources.yaml`.
- **Flows** e **Mocks** ficaram **sem exemplo de propósito**. Os dois têm
  formatos que não dá pra chutar com segurança:
  - Flows são grafos visuais (nós/conexões) — não há um schema JSON/YAML
    simples e documentado publicamente para escrever um `.flow` à mão.
  - Mocks locais (`postman mock run <manifest>`, testado via Postman CLI)
    exigem um handler JavaScript próprio (`mockSrc`) ou um `.sim.yaml` de
    fault-injection — não um "replay" declarativo dos exemplos já salvos na
    collection. O caminho realmente simples para mock aqui é o nativo do
    Postman: botão direito na collection → "Mock collection" (usa as
    respostas de exemplo que já estão em
    `postman/collections/PetVerse API/**/.resources/**/examples/*.example.yaml`),
    que roda na nuvem do Postman sem precisar de nenhum arquivo local.

  Se quiser um Flow ou Mock local de verdade neste repo, o caminho mais seguro
  é criar um mínimo pela UI do Postman e a partir do arquivo gerado eu adapto/
  documento o padrão real — o mesmo método que resolveu o formato de
  ambientes e o registro da spec.
