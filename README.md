# SmartControl Sites

Plataforma fullstack para venda, assinatura, criacao e gestao de sites para clientes.

## Stack

- Frontend: React + Vite
- Backend: Django REST Framework
- Banco: PostgreSQL
- Auth: JWT com refresh token rotativo
- Pagamentos: Stripe + webhooks assinados

## Estrutura

```text
SmartControlSite/
  backend/      API Django REST
  frontend/     Aplicacao React
  docs/         Arquitetura, SQL e endpoints
```

## Documentacao

- [Arquitetura](docs/ARCHITECTURE.md)
- [Modelo SQL](docs/DATABASE.sql)
- [Endpoints](docs/API.md)
- [Estrutura de pastas](docs/STRUCTURE.md)
- [Deploy GitHub + Render](docs/DEPLOY.md)

## Rodando em desenvolvimento

1. Copie os arquivos de ambiente:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. Suba o PostgreSQL:

```bash
docker compose up -d postgres
```

3. Backend:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

4. Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Seguranca implementada na base

- Hash de senha com Argon2
- JWT com expiracao curta e refresh token rotativo em cookie HttpOnly
- Rate limiting em auth e API
- CORS e CSRF configuraveis por ambiente
- Headers de seguranca, CSP e HSTS
- RBAC para admin e cliente
- Validacao e sanitizacao de inputs textuais
- Webhook Stripe com validacao de assinatura
- Logs de autenticacao, erros e acoes sensiveis
- Secrets apenas via variaveis de ambiente

## Observacoes

- A recuperacao de senha ja possui token seguro e resposta anti-enumeration; falta conectar um provedor real de email.
- Stripe ja tem checkout e webhook assinado; preencha `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` e os price ids dos planos.
- Em producao, use HTTPS, `DJANGO_DEBUG=False`, secrets fortes e origins explicitamente configuradas.
