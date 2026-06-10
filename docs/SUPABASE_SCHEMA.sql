-- SmartControl Sites - Supabase schema and RLS
-- Run in Supabase SQL Editor before pointing the application to the Supabase database.

create extension if not exists "pgcrypto";

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  nome text not null,
  plano text not null default 'client',
  creditos integer not null default 0 check (creditos >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_touch_updated_at on public.profiles;
create trigger profiles_touch_updated_at
before update on public.profiles
for each row execute function public.touch_updated_at();

create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email, nome, plano, creditos)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'name', new.raw_user_meta_data->>'first_name', new.email),
    coalesce(new.raw_user_meta_data->>'plano', 'client'),
    0
  )
  on conflict (id) do update
    set email = excluded.email,
        nome = excluded.nome,
        updated_at = now();
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_auth_user();

alter table public.profiles enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
on public.profiles for select
to authenticated
using (id = auth.uid());

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
on public.profiles for update
to authenticated
using (id = auth.uid())
with check (id = auth.uid());

-- These ALTER statements match the Django models used by the API.
-- Run them only if the tables already exist and were created before this migration.
alter table if exists public.users
  add column if not exists supabase_user_id uuid unique;

create index if not exists users_supabase_user_id_idx
  on public.users (supabase_user_id);

alter table if exists public.subscriptions
  add column if not exists user_id bigint references public.users(id) on delete cascade,
  add column if not exists stripe_customer_id text,
  add column if not exists plano text not null default '';

create index if not exists subscriptions_user_id_idx
  on public.subscriptions (user_id);
create index if not exists subscriptions_stripe_customer_id_idx
  on public.subscriptions (stripe_customer_id);

alter table if exists public.payments
  add column if not exists user_id bigint references public.users(id) on delete cascade,
  add column if not exists stripe_payment_intent text;

create index if not exists payments_user_id_idx
  on public.payments (user_id);

alter table if exists public.subscriptions enable row level security;
alter table if exists public.payments enable row level security;

drop policy if exists "subscriptions_select_own" on public.subscriptions;
create policy "subscriptions_select_own"
on public.subscriptions for select
to authenticated
using (
  user_id in (
    select id from public.users where supabase_user_id = auth.uid()
  )
);

drop policy if exists "payments_select_own" on public.payments;
create policy "payments_select_own"
on public.payments for select
to authenticated
using (
  user_id in (
    select id from public.users where supabase_user_id = auth.uid()
  )
);

-- Service-role writes are used by Django and Stripe webhooks. Do not expose the service role key in the frontend.
