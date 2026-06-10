# SmartControl Sites

Plataforma fullstack para criacao, venda, assinatura e gerenciamento de sites profissionais.

## Arquitetura

```text
Usuario
  -> Frontend React/Vite
  -> Supabase Auth
  -> API Django REST
  -> PostgreSQL gerenciado pelo Supabase
  -> Stripe
```

O Supabase e o backend principal de identidade e persistencia. A API Django continua concentrando as regras de negocio da plataforma, validando JWTs do Supabase e atendendo projetos, pagamentos, planos, clientes e webhooks Stripe.

## Tecnologias

- Frontend: React, Vite, React Router, Supabase JS
- Backend: Django, Django REST Framework
- Auth: Supabase Auth
- Banco: PostgreSQL gerenciado pelo Supabase
- Pagamentos: Stripe
- Deploy: Render para API/frontend e Supabase para dados/auth

## Variaveis de ambiente

Backend:

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=
DJANGO_CORS_ALLOWED_ORIGINS=
DJANGO_CSRF_TRUSTED_ORIGINS=
FRONTEND_URL=
FRONTEND_ORIGIN=
FRONTEND_ORIGINS=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
SUPABASE_DATABASE_URL=
SUPABASE_PASSWORD_RESET_REDIRECT_URL=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_SUCCESS_URL=
STRIPE_CANCEL_URL=
STRIPE_PORTAL_RETURN_URL=
```

Frontend:

```env
VITE_API_URL=
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

Nunca exponha `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` ou `STRIPE_SECRET_KEY` no frontend.

## Autenticacao

1. Cadastro chama `/api/auth/register/`.
2. A API cria o usuario no Supabase Auth.
3. A API cria/sincroniza `profiles`, `users` e `clients` no Postgres do Supabase.
4. Login e refresh usam tokens nativos do Supabase.
5. O frontend persiste a sessao com `@supabase/supabase-js`.
6. Rotas privadas usam `Authorization: Bearer <supabase_access_token>`.
7. A API valida o JWT com `SUPABASE_JWT_SECRET`.

## Stripe para Supabase

Webhooks recebidos em `/api/billing/webhook/stripe/` atualizam automaticamente:

- `subscriptions`
- `payments`
- `transaction_logs`
- status de projetos relacionados

Eventos suportados:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`

## Banco e RLS

Execute o script:

```bash
docs/SUPABASE_SCHEMA.sql
```

Ele cria `profiles`, trigger de perfil para novos usuarios Supabase, colunas de associacao com Stripe e policies RLS para usuarios acessarem apenas seus proprios dados.

## Desenvolvimento

Backend:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Deploy

1. Crie o projeto no Supabase.
2. Execute `docs/SUPABASE_SCHEMA.sql`.
3. Configure as variaveis Supabase e Stripe no Render.
4. Rode `python manage.py migrate` no deploy da API.
5. Configure o webhook Stripe para `/api/billing/webhook/stripe/`.
6. Configure o redirect de reset de senha para `/reset-password`.

## Migracao

O guia completo esta em `docs/SUPABASE_MIGRATION.md`.
