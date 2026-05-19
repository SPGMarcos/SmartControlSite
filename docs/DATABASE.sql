-- SmartControl Sites - PostgreSQL schema
-- Este SQL documenta a modelagem. Em runtime, Django gerencia migrations.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMPTZ NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    email VARCHAR(254) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    role VARCHAR(20) NOT NULL DEFAULT 'client',
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_role_check CHECK (role IN ('admin', 'client'))
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

CREATE TABLE clients (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(180) NOT NULL,
    document VARCHAR(32) NOT NULL DEFAULT '',
    phone VARCHAR(32) NOT NULL DEFAULT '',
    status VARCHAR(24) NOT NULL DEFAULT 'active',
    stripe_customer_id VARCHAR(128) UNIQUE NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT clients_status_check CHECK (status IN ('active', 'inactive', 'blocked'))
);

CREATE INDEX idx_clients_status ON clients(status);
CREATE INDEX idx_clients_company ON clients(company_name);

CREATE TABLE plans (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(140) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    setup_price NUMERIC(10,2) NOT NULL DEFAULT 0,
    monthly_price NUMERIC(10,2) NOT NULL DEFAULT 0,
    features JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    stripe_setup_price_id VARCHAR(128) NULL,
    stripe_monthly_price_id VARCHAR(128) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT plans_setup_price_check CHECK (setup_price >= 0),
    CONSTRAINT plans_monthly_price_check CHECK (monthly_price >= 0)
);

CREATE INDEX idx_plans_active ON plans(is_active);

CREATE TABLE subscriptions (
    id BIGSERIAL PRIMARY KEY,
    client_id BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    plan_id BIGINT NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    stripe_subscription_id VARCHAR(128) UNIQUE NULL,
    current_period_start TIMESTAMPTZ NULL,
    current_period_end TIMESTAMPTZ NULL,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT subscriptions_status_check CHECK (
        status IN ('pending', 'active', 'past_due', 'canceled', 'unpaid', 'incomplete')
    )
);

CREATE INDEX idx_subscriptions_client ON subscriptions(client_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

CREATE TABLE projects (
    id BIGSERIAL PRIMARY KEY,
    client_id BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    plan_id BIGINT NULL REFERENCES plans(id) ON DELETE SET NULL,
    name VARCHAR(160) NOT NULL,
    site_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'awaiting_analysis',
    domain VARCHAR(255) NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    references TEXT NOT NULL DEFAULT '',
    desired_features TEXT NOT NULL DEFAULT '',
    visual_style TEXT NOT NULL DEFAULT '',
    repository_url VARCHAR(500) NOT NULL DEFAULT '',
    production_url VARCHAR(500) NOT NULL DEFAULT '',
    start_date DATE NULL,
    due_date DATE NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT projects_site_type_check CHECK (site_type IN ('landing_page', 'institutional_site', 'web_system')),
    CONSTRAINT projects_status_check CHECK (
        status IN ('awaiting_analysis', 'quote_sent', 'payment_pending', 'in_development', 'review', 'completed')
    )
);

CREATE INDEX idx_projects_client ON projects(client_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_site_type ON projects(site_type);

CREATE TABLE project_attachments (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    uploaded_by_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    file VARCHAR(100) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(120) NOT NULL DEFAULT '',
    size INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_project_attachments_project ON project_attachments(project_id);
CREATE INDEX idx_project_attachments_uploaded_by ON project_attachments(uploaded_by_id);

ALTER TABLE subscriptions
    ADD COLUMN project_id BIGINT NULL REFERENCES projects(id) ON DELETE SET NULL;

CREATE INDEX idx_subscriptions_project ON subscriptions(project_id);

CREATE TABLE requests (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    client_id BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    created_by_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title VARCHAR(180) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(16) NOT NULL DEFAULT 'medium',
    status VARCHAR(24) NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT requests_priority_check CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    CONSTRAINT requests_status_check CHECK (status IN ('open', 'in_progress', 'waiting_client', 'done', 'canceled'))
);

CREATE INDEX idx_requests_project ON requests(project_id);
CREATE INDEX idx_requests_client ON requests(client_id);
CREATE INDEX idx_requests_status ON requests(status);

CREATE TABLE payments (
    id BIGSERIAL PRIMARY KEY,
    client_id BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    subscription_id BIGINT NULL REFERENCES subscriptions(id) ON DELETE SET NULL,
    project_id BIGINT NULL REFERENCES projects(id) ON DELETE SET NULL,
    kind VARCHAR(24) NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'pending',
    amount NUMERIC(10,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'BRL',
    stripe_payment_intent_id VARCHAR(128) UNIQUE NULL,
    stripe_invoice_id VARCHAR(128) UNIQUE NULL,
    paid_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stripe_checkout_session_id VARCHAR(128) UNIQUE NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    CONSTRAINT payments_kind_check CHECK (kind IN ('one_time', 'subscription', 'installment')),
    CONSTRAINT payments_status_check CHECK (status IN ('pending', 'paid', 'failed', 'refunded', 'canceled')),
    CONSTRAINT payments_amount_check CHECK (amount >= 0)
);

CREATE INDEX idx_payments_client ON payments(client_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_kind ON payments(kind);
CREATE INDEX idx_payments_checkout_session ON payments(stripe_checkout_session_id);

CREATE TABLE transaction_logs (
    id BIGSERIAL PRIMARY KEY,
    provider VARCHAR(32) NOT NULL DEFAULT 'stripe',
    stripe_event_id VARCHAR(128) UNIQUE NULL,
    event_type VARCHAR(120) NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'created',
    client_id BIGINT NULL REFERENCES clients(id) ON DELETE SET NULL,
    subscription_id BIGINT NULL REFERENCES subscriptions(id) ON DELETE SET NULL,
    project_id BIGINT NULL REFERENCES projects(id) ON DELETE SET NULL,
    payment_id BIGINT NULL REFERENCES payments(id) ON DELETE SET NULL,
    amount NUMERIC(10,2) NULL,
    currency CHAR(3) NOT NULL DEFAULT '',
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT transaction_logs_status_check CHECK (
        status IN ('created', 'processed', 'ignored', 'failed', 'duplicate')
    )
);

CREATE INDEX idx_transaction_logs_provider_event ON transaction_logs(provider, event_type);
CREATE INDEX idx_transaction_logs_status ON transaction_logs(status);
CREATE INDEX idx_transaction_logs_client ON transaction_logs(client_id);
CREATE INDEX idx_transaction_logs_created_at ON transaction_logs(created_at);

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(120) NOT NULL,
    target_type VARCHAR(120) NOT NULL DEFAULT '',
    target_id VARCHAR(120) NOT NULL DEFAULT '',
    ip_address INET NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

CREATE TABLE auth_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(254) NOT NULL DEFAULT '',
    event VARCHAR(80) NOT NULL,
    ip_address INET NULL,
    user_agent TEXT NOT NULL DEFAULT '',
    success BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_auth_logs_email ON auth_logs(email);
CREATE INDEX idx_auth_logs_event ON auth_logs(event);
CREATE INDEX idx_auth_logs_created_at ON auth_logs(created_at);
