# Guia da API PetVerse

> Documento de referência rápida para quem for consumir a **PetVerse API**
> (fictícia). Para o contrato completo, veja a spec OpenAPI em
> `postman/specs/openapi.yaml`; para exemplos prontos de requisição, veja a
> collection em `postman/collections/PetVerse API/`.

## Visão geral

A PetVerse API atende o sistema de uma clínica veterinária/petshop fictícia:
cadastro de tutores (**owners**), pets, agendamento de **consultas**
(appointments) e autenticação.

- **Base URL (produção):** `https://api.petverse.example.com`
- **Autenticação:** Bearer token (`Authorization: Bearer <access_token>`),
  obtido em `POST /v1/auth/login`.
- **Formato:** todas as requisições e respostas usam `application/json`.

## Fluxo típico de uso

1. `POST /v1/auth/login` — autentica e retorna `access_token` + `refresh_token`.
2. `POST /v1/owners` — cadastra o tutor.
3. `POST /v1/pets` — cadastra um pet vinculado ao `ownerId` retornado no passo 2.
4. `POST /v1/appointments` — agenda uma consulta para o `petId` do passo 3.
5. Quando o `access_token` expirar, use `POST /v1/auth/refresh` com o
   `refresh_token` em vez de logar de novo.

## Recursos

| Recurso | Endpoints | Pasta na collection |
|---|---|---|
| Auth | login, refresh, logout | `Auth/` |
| Owners | CRUD de tutores | `Owners/` |
| Pets | CRUD de pets | `Pets/` |
| Appointments | criar/listar/cancelar consultas | `Appointments/` |
| System | health check | `System/` |

## Erros

Todo erro segue o mesmo formato:

```json
{
  "error": "not_found",
  "message": "Pet não encontrado."
}
```

| Código | Quando acontece |
|---|---|
| `400` | corpo da requisição inválido (campo obrigatório faltando, tipo errado) |
| `401` | token ausente, inválido ou expirado |
| `404` | recurso (owner/pet/appointment) não encontrado |

## Ambientes disponíveis

Ver `postman/environments/`: **Local**, **Development**, **Staging** e
**Production** — cada um com sua própria `base_url` e credenciais.
