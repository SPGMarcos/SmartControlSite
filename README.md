# SmartControl Sites 🌐⚡

Plataforma fullstack para criação, venda, assinatura e gerenciamento de sites profissionais.



## 📌 Visão Geral

O **SmartControl Sites** foi desenvolvido para oferecer uma plataforma moderna de criação e gerenciamento de sites profissionais.

A proposta é permitir que clientes tenham:

✅ Sites profissionais  
✅ Lojas online  
✅ Painéis administrativos  
✅ Gestão de produtos  
✅ Sistema de assinaturas  
✅ Hospedagem centralizada  

Tudo isso em uma plataforma moderna, segura e escalável.



# 🎯 Objetivo

Criar uma plataforma SaaS que seja:

- Moderna
- Escalável
- Segura
- Fácil de usar
- Automatizada
- Preparada para múltiplos clientes



# 🌐 O que a plataforma faz

A plataforma permite:

## 🔹 Venda de sites por assinatura

- Planos recorrentes
- Gestão de assinaturas
- Cobrança automatizada
- Integração Stripe

## 🔹 Criação de lojas online

- Gestão de produtos
- Cadastro de clientes
- Dashboard administrativa
- Controle de pedidos

## 🔹 Sistema de autenticação

- Login seguro
- JWT com refresh token
- Sessões protegidas
- Controle de permissões

## 🔹 Gestão administrativa

- Controle de clientes
- Controle de sites
- Gestão de planos
- Administração centralizada



# 🧠 Como funciona

O frontend React se comunica com a API Django REST.

A API gerencia:

- Autenticação
- Pagamentos
- Usuários
- Planos
- Dados dos sites

O PostgreSQL armazena todas as informações da plataforma.



# ⚙️ Arquitetura

## Fluxo principal

```text
Usuário
   ↓
Frontend React
   ↓
API Django REST
   ↓
PostgreSQL
   ↓
Stripe
```



# 💻 Tecnologias utilizadas

## Frontend

- React
- Vite
- JavaScript
- HTML5
- CSS3

## Backend

- Python
- Django
- Django REST Framework

## Banco de dados

- PostgreSQL

## Pagamentos

- Stripe

## Autenticação

- JWT
- Refresh Token Rotativo



# 🔐 Segurança implementada

## 🔹 Autenticação segura

- JWT com expiração curta
- Refresh token rotativo
- Cookies HttpOnly
- Controle de sessão

## 🔹 Proteções da aplicação

- Rate limiting
- Proteção CSRF
- CORS configurável
- CSP e HSTS
- Sanitização de inputs

## 🔹 Segurança de usuários

- Hash de senha com Argon2
- RBAC para admin e cliente
- Logs de autenticação
- Logs de ações sensíveis

## 🔹 Integrações seguras

- Webhook Stripe validado
- Secrets via variáveis de ambiente



# 📂 Estrutura do projeto

```text
SmartControlSite/

├── backend/      → API Django REST
├── frontend/     → Aplicação React
└── docs/         → Arquitetura e documentação
```



# 🚀 Rodando em desenvolvimento

## Clonar o projeto

```bash
git clone
```



## Configurar variáveis de ambiente

```bash
cp backend/.env.example backend/.env

cp frontend/.env.example frontend/.env
```



## Subir PostgreSQL

```bash
docker compose up -d postgres
```



## Backend

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



## Frontend

```bash
cd frontend

npm install

npm run dev
```



# 🔄 Fluxo da plataforma

```text
Usuário acessa a plataforma
        ↓
Frontend React
        ↓
Autenticação JWT
        ↓
API Django
        ↓
Banco PostgreSQL
        ↓
Stripe processa pagamentos
        ↓
Sistema libera funcionalidades
```



# 🛡️ Confiabilidade

✅ Estrutura fullstack moderna  
✅ Sistema escalável  
✅ Segurança robusta  
✅ API modular  
✅ Backend desacoplado  
✅ Preparado para múltiplos clientes  



# ⚠️ Limitações atuais

- Sistema de email ainda precisa de provedor real
- Algumas áreas administrativas continuam em desenvolvimento
- Plataforma ainda está recebendo melhorias visuais



# 📈 Próximos passos

- Builder visual de sites
- Gestão automática de domínios
- Deploy automatizado
- Sistema white-label
- IA para criação de layouts
- Dashboard financeira
- Analytics avançado
- Multi-tenant completo



# 🌍 Aplicações

- Sites institucionais
- Lojas online
- Landing pages
- Portfólios
- Sistemas SaaS
- Gestão de clientes
- Assinaturas recorrentes



# 🔗 Projeto

## GitHub Pages

https://spgmarcos.github.io/SmartControlSite/



# 👨‍💻 Autores

## Ryan Maximiano

## Marcos Gabriel Ferreira Miranda

Desenvolvedor Fullstack | IoT | Automação

React • Django • PostgreSQL • Stripe

Fundador da SmartControl

📍 Belo Horizonte - MG
