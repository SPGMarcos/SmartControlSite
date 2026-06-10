# Deploy GitHub + Render + Supabase

Este projeto esta preparado para:

- Frontend React no GitHub Pages ou Render.
- Backend Django REST no Render.
- Auth e PostgreSQL gerenciado pelo Supabase.
- Pagamentos e webhooks pelo Stripe.

## URLs esperadas

- Frontend: `https://spgmarcos.github.io/SmartControlSite/`
- Backend: `https://smartcontrolsite.onrender.com/api`
- Health check backend: `https://smartcontrolsite.onrender.com/api/health/`

## Supabase

1. Crie um projeto no Supabase.
2. Copie `Project URL`, `anon public key`, `service_role key` e `JWT secret`.
3. Copie a connection string Pooler/Transaction ou Direct para `SUPABASE_DATABASE_URL`.
4. Execute `docs/SUPABASE_SCHEMA.sql` no SQL Editor.
5. Configure o redirect de recuperacao de senha para:

```text
https://spgmarcos.github.io/SmartControlSite/reset-password
```

## Backend no Render

O `render.yaml` cria apenas o web service da API. O banco nao e mais criado no Render.

Secrets obrigatorios:

```text
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_JWT_SECRET
SUPABASE_DATABASE_URL
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
```

Variaveis de URL:

```text
FRONTEND_URL=https://spgmarcos.github.io/SmartControlSite
FRONTEND_ORIGIN=https://spgmarcos.github.io
SUPABASE_PASSWORD_RESET_REDIRECT_URL=https://spgmarcos.github.io/SmartControlSite/reset-password
STRIPE_SUCCESS_URL=https://spgmarcos.github.io/SmartControlSite/billing?checkout=success&session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=https://spgmarcos.github.io/SmartControlSite/billing?checkout=cancel
STRIPE_PORTAL_RETURN_URL=https://spgmarcos.github.io/SmartControlSite/billing
```

O build executa:

```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py bootstrap_credentials
```

## Frontend

Configure:

```text
VITE_API_URL=https://smartcontrolsite.onrender.com/api
VITE_APP_BASE_PATH=/SmartControlSite/
VITE_SUPABASE_URL=<project-url>
VITE_SUPABASE_ANON_KEY=<anon-key>
```

Depois rode:

```bash
npm ci
npm run build
```

## Stripe

Webhook:

```text
https://smartcontrolsite.onrender.com/api/billing/webhook/stripe/
```

Eventos:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`
- `invoice.payment_succeeded`

## Migracao do banco antigo

Use `docs/SUPABASE_MIGRATION.md`. Depois da importacao, rode:

```bash
python manage.py migrate
```

Valide cadastro, login, checkout, webhooks e RLS antes de desligar qualquer recurso antigo.
