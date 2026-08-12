# Setup: adotando este kit num projeto existente

Checklist na ordem certa — cada passo depende do anterior. Leva uns 20-30
minutos na primeira vez; a maior parte é esperar validação, não decisão.

## 0. Copiar os arquivos

Copie o **conteúdo** de `skeleton/` (não a pasta `skeleton/` em si) pra raiz
do seu projeto existente. Se o projeto já tem `.github/workflows/`,
`package.json` etc., mescle em vez de sobrescrever — os arquivos deste kit
são pensados pra conviver ao lado de outros (ex.: um `package.json` de app
Laravel/Node já existente: só adicione os `scripts` e `devDependencies`
deste kit aos que já existem, não substitua o arquivo inteiro).

## 1. Preencher a config central

```bash
cp postman-fern.env.example postman-fern.env
```

Edite `postman-fern.env`: no mínimo, `COLLECTION_NAME` e `MOCK_SLUG`. Os
outros (`FERN_ORG`, `FERN_DOMAIN`, `GITHUB_REPO`) você só vai saber depois
dos passos 4-5 — pode deixar o placeholder por enquanto. **Valores com
espaço precisam de aspas duplas** (ex.: `COLLECTION_NAME="Minha API"`) —
sem isso o `source` do bash quebra (testado).

Aplique a config em todo o kit de uma vez (renomeia as pastas placeholder e
troca `__COLLECTION_NAME__`/`__MOCK_SLUG__`/`__FERN_ORG__`/`__FERN_DOMAIN__`
dentro do conteúdo dos arquivos — não é só nome de pasta, os placeholders
também aparecem dentro de `definition.yaml`, `config.yaml`, `docs.yml` etc.):

```bash
bash scripts/apply-config.sh
```

Confira a saída — ele avisa se sobrou algum placeholder não substituído.

## 2. Preencher `.postman/resources.yaml`

```bash
mkdir -p .postman
cp .postman/resources.yaml.example .postman/resources.yaml
```

Precisa do `workspace.id` de um workspace real do Postman. Se não tiver um
ainda, pule este passo — o próprio Postman Desktop recria esse arquivo
sozinho na primeira vez que você conecta a pasta (passo 3).

## 3. Conectar o Postman Desktop (Native Git)

1. Se o projeto não é um repositório git ainda, `git init` + configure um
   remote (`git remote add origin <url>`) — o Postman **exige** um remote
   configurado, não basta ser um repo git local solto
   (`docs/TROUBLESHOOTING.md`, "Add a Git remote to continue").
2. Abra a **raiz do projeto** (não a subpasta `postman/`) via Native Git no
   Postman Desktop.
3. Confirme que o menu "Items" mostra a collection e o ambiente. Se não
   aparecer, ou aparecer algum erro na tela, veja
   `docs/TROUBLESHOOTING.md` primeiro — a causa quase certamente já está
   catalogada lá.

## 4. Instalar dependências e validar

```bash
npm install
pip install pyyaml jsonschema
bash scripts/lint.sh
```

Deve passar limpo (o kit já vem com um endpoint de exemplo — `GET /health`
— que bate entre spec e collection). Se `fern check` falhar aqui, é
validação estrutural, não precisa de login — geralmente indica um erro
real de sintaxe em `fern/`, não falta de autenticação.

## 5. Autenticar e configurar a Fern

```bash
npx fern-api login
npx fern-api org get
```

Confirme que o `orgId` retornado bate com o que você quer usar. Atualize
`fern/fern.config.json` (`organization`) e `postman-fern.env` (`FERN_ORG`)
com esse valor exato.

Gere um preview antes de qualquer coisa em produção:

```bash
npx fern-api generate --docs --preview --id "setup-inicial"
```

Confira o link, depois apague (`npx fern-api docs preview delete "<url>"`).

## 6. Publicar de verdade

```bash
npx fern-api generate --docs --log-level debug   # produção, pede confirmação
```

## 7. Configurar o CI

```bash
npx fern-api token --organization <sua-org>   # só DEPOIS de confirmar login na org certa (passo 5)
gh secret set FERN_TOKEN --repo <owner>/<repo> --body "<token gerado>"
```

Sem esse secret, `fern-docs-publish.yml` existe mas falha ao tentar
publicar — `fern-check.yml` (sem token) continua funcionando normalmente.

Se o repositório for **privado**, `docs-pages.yml` (portal Redoc via
GitHub Pages) só funciona em plano pago do GitHub — torne o repo público
ou adapte o workflow pra outro host de páginas estáticas.

## 8. Primeiro push

```bash
git add -A
git commit -m "feat: adiciona kit Postman Git Native + Fern Docs"
git push
```

Acompanhe os workflows (`gh run list` / aba Actions do GitHub). Se algo
falhar, o erro quase certamente é um dos catalogados em
`docs/TROUBLESHOOTING.md` — comece por ali antes de investigar do zero.

## Depois disso

- Substitua o endpoint de exemplo (`Example/Health Check` na collection,
  `/health` na spec, `pages/example.mdx` na Fern) pelos endpoints reais da
  sua API.
- Sempre que adicionar/mudar um endpoint: edite a spec primeiro, depois a
  collection (mesma tag/pasta!), rode `npm run lint`, e só então commit.
- Tema/logo/navbar da Fern: `fern/docs.yml` já vem com um tema testado
  aplicado e comentários explicando as outras opções -- ver
  `docs/fern-docs.md` pra a tabela completa e o passo a passo de logo
  light/dark.
