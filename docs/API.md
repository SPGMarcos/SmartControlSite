# API - SmartControl Sites

Base URL local: `http://localhost:8000/api`

## Health

| Metodo | Endpoint | Acesso | Descricao |
| --- | --- | --- | --- |
| GET | `/health/` | Publico | Health check para Render |

## Auth

| Metodo | Endpoint | Acesso | Descricao |
| --- | --- | --- | --- |
| POST | `/auth/register/` | Publico | Cadastra cliente |
| POST | `/auth/login/` | Publico | Retorna access e refresh token |
| POST | `/auth/token/refresh/` | Publico | Rotaciona refresh token via cookie HttpOnly |
| POST | `/auth/password-reset/` | Publico | Solicita recuperacao com resposta generica |
| POST | `/auth/password-reset/confirm/` | Publico | Confirma nova senha |
| GET | `/auth/me/` | Autenticado | Dados do usuario logado |
| POST | `/auth/logout/` | Autenticado | Invalida refresh token |
| GET | `/csrf/` | Publico | Emite cookie CSRF quando necessario |

## Clientes

| Metodo | Endpoint | Acesso | Descricao |
| --- | --- | --- | --- |
| GET | `/clients/` | Admin | Lista clientes |
| POST | `/clients/` | Admin | Cria cliente |
| GET | `/clients/{id}/` | Admin ou dono | Detalha cliente |
| PATCH | `/clients/{id}/` | Admin | Atualiza cliente |
| GET | `/clients/me/` | Cliente | Dados do proprio cliente |

## Planos

| Metodo | Endpoint | Acesso | Descricao |
| --- | --- | --- | --- |
| GET | `/plans/` | Publico | Lista planos ativos |
| POST | `/plans/` | Admin | Cria plano |
| PATCH | `/plans/{id}/` | Admin | Atualiza plano |

## Projetos

| Metodo | Endpoint | Acesso | Descricao |
| --- | --- | --- | --- |
| GET | `/projects/` | Admin ou cliente | Lista projetos permitidos |
| POST | `/projects/` | Admin | Cria projeto |
| GET | `/projects/{id}/` | Admin ou dono | Detalha projeto |
| PATCH | `/projects/{id}/` | Admin | Atualiza projeto |

## Solicitacoes

| Metodo | Endpoint | Acesso | Descricao |
| --- | --- | --- | --- |
| GET | `/requests/` | Admin ou cliente | Lista solicitacoes permitidas |
| POST | `/requests/` | Cliente/Admin | Cria solicitacao |
| PATCH | `/requests/{id}/` | Admin ou dono | Atualiza solicitacao conforme permissao |

## Billing

| Metodo | Endpoint | Acesso | Descricao |
| --- | --- | --- | --- |
| GET | `/subscriptions/` | Admin ou cliente | Lista assinaturas permitidas |
| GET | `/payments/` | Admin ou cliente | Lista pagamentos permitidos |
| POST | `/billing/checkout-session/` | Cliente | Cria sessao Stripe Checkout |
| POST | `/billing/webhook/stripe/` | Stripe | Recebe eventos assinados |

## Padrao de erro

```json
{
  "detail": "Mensagem generica segura.",
  "code": "optional_error_code"
}
```

## Headers

Rotas autenticadas:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

Fluxos com cookie, como login, logout e refresh, usam:

```http
X-CSRFToken: <csrftoken>
```

O frontend chama `/csrf/` antes de requisicoes inseguras para manter o cookie CSRF sincronizado.
