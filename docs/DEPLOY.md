# Deploy GitHub + Render

Este projeto esta preparado para:

- Frontend React no GitHub Pages.
- Backend Django REST no Render gratuito.
- PostgreSQL gerenciado pelo Render.

## URLs esperadas

- Frontend: `https://spgmarcos.github.io/SmartControlSite/`
- Backend: `https://smartcontrol-sites-api.onrender.com/api`
- Health check backend: `https://smartcontrol-sites-api.onrender.com/api/health/`

Se o Render mudar o subdominio do backend, atualize:

- Variavel do GitHub Actions: `VITE_API_BASE_URL`
- Variaveis do Render: `DJANGO_ALLOWED_HOSTS`, `STRIPE_SUCCESS_URL`, `STRIPE_CANCEL_URL`
- O proprio `render.yaml`, se quiser manter tudo documentado no repo

## Frontend no GitHub Pages

O workflow esta em `.github/workflows/frontend-pages.yml`.

Passos no GitHub:

1. Va em `Settings > Pages`.
2. Em `Build and deployment`, selecione `GitHub Actions`.
3. Opcional: em `Settings > Secrets and variables > Actions > Variables`, crie:

```text
VITE_API_BASE_URL=https://smartcontrol-sites-api.onrender.com/api
```

4. Faca push na branch `main`.

O workflow executa:

```bash
npm ci
npm run build
```

Depois publica `frontend/dist` no GitHub Pages.

## Backend no Render

O arquivo `render.yaml` cria:

- Web service Python gratuito: `smartcontrol-sites-api`
- PostgreSQL gratuito: `smartcontrol-sites-db`

Passos no Render:

1. Abra `Blueprints`.
2. Clique em `New Blueprint Instance`.
3. Selecione o repo `SPGMarcos/SmartControlSite`.
4. Aplique o blueprint.
5. Preencha os secrets solicitados:

```text
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
```

O Render usa:

```bash
bash build.sh
python manage.py migrate --no-input
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

O build instala dependencias e coleta estaticos. O pre-deploy executa migrations antes de iniciar a nova versao.

## Criar admin em producao

Depois do primeiro deploy, abra o Shell do servico no Render e rode:

```bash
python manage.py createsuperuser
```

## Stripe

No dashboard Stripe, configure o webhook:

```text
https://smartcontrol-sites-api.onrender.com/api/billing/webhook/stripe/
```

Eventos usados:

- `checkout.session.completed`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`

## Observacoes do plano gratuito

- O backend pode dormir quando ficar sem trafego.
- A primeira chamada depois de inatividade pode demorar.
- Para producao comercial real, migre para plano pago antes de vender em escala.
