# Migracao para Supabase

## Variaveis de ambiente

Backend:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`
- `SUPABASE_DATABASE_URL`
- `SUPABASE_PASSWORD_RESET_REDIRECT_URL`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_SUCCESS_URL`
- `STRIPE_CANCEL_URL`
- `STRIPE_PORTAL_RETURN_URL`

Frontend:

- `VITE_API_URL`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

## Passos de migracao dos dados

1. Crie o projeto no Supabase e copie a connection string do Postgres em `SUPABASE_DATABASE_URL`.
2. Execute `docs/SUPABASE_SCHEMA.sql` no SQL Editor do Supabase.
3. Exporte o banco antigo do Render:

```bash
pg_dump "$DATABASE_URL" --no-owner --no-acl --format=custom --file smartcontrol-render.dump
```

4. Importe no Postgres do Supabase:

```bash
pg_restore --no-owner --no-acl --clean --if-exists --dbname "$SUPABASE_DATABASE_URL" smartcontrol-render.dump
```

5. Rode as migrations Django contra o Supabase:

```bash
cd backend
python manage.py migrate
```

6. Para cada usuario existente, crie o usuario correspondente no Supabase Auth e preencha `users.supabase_user_id` com o UUID retornado.
7. Garanta que `profiles.id` seja igual ao UUID do Supabase Auth.
8. Preencha os novos vinculos:

```sql
update public.subscriptions s
set user_id = c.user_id,
    stripe_customer_id = coalesce(s.stripe_customer_id, c.stripe_customer_id),
    plano = coalesce(nullif(s.plano, ''), p.slug, p.name, '')
from public.clients c
left join public.plans p on p.id = s.plan_id
where s.client_id = c.id;

update public.payments p
set user_id = c.user_id,
    stripe_payment_intent = coalesce(p.stripe_payment_intent, p.stripe_payment_intent_id)
from public.clients c
where p.client_id = c.id;
```

## Fluxo de autenticacao

1. Cadastro chama `/api/auth/register/`.
2. O backend cria o usuario no Supabase Auth com service role.
3. O backend cria/sincroniza `profiles`, `users` e `clients` no Postgres do Supabase.
4. O backend faz login no Supabase Auth e retorna `access`/`refresh`.
5. O frontend persiste a sessao com `@supabase/supabase-js`.
6. Chamadas privadas usam `Authorization: Bearer <supabase_access_token>`.
7. O DRF valida o JWT com `SUPABASE_JWT_SECRET`.

## Fluxo Stripe para Supabase

1. Checkout cria/usa `clients.stripe_customer_id`.
2. Webhooks Stripe chegam em `/api/billing/webhook/stripe/`.
3. O backend valida `STRIPE_WEBHOOK_SECRET`.
4. Eventos atualizam `subscriptions`, `payments`, `transaction_logs` e status dos projetos.
5. As linhas recebem `user_id`, `stripe_customer_id`, `plano` e ids Stripe para auditoria e RLS.

## Checklist de testes

- Cadastro cria usuario no Supabase Auth, `profiles`, `users` e `clients`.
- Login retorna token Supabase e abre `/dashboard`.
- Refresh automatico mantem a sessao apos expirar o access token.
- Logout limpa sessao no frontend e invalida a sessao no Supabase.
- Reset de senha envia email pelo Supabase e permite atualizar senha.
- Usuario cliente ve apenas seus projetos, pagamentos e assinaturas.
- Usuario admin ve clientes, projetos, planos, pagamentos e solicitacoes.
- Checkout cria sessao Stripe e registra pagamento pendente.
- Webhooks `checkout.session.completed`, `customer.subscription.*`, `invoice.paid` e `invoice.payment_failed` atualizam o Supabase.
- Policies RLS bloqueiam acesso direto a dados de outro usuario via Supabase client.
