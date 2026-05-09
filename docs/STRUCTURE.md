# Estrutura de pastas

```text
SmartControlSite/
  backend/
    config/
      settings.py
      urls.py
      asgi.py
      wsgi.py
    apps/
      core/
        middleware.py
        permissions.py
        services.py
        validators.py
      users/
        models.py
        serializers.py
        services.py
        views.py
      clients/
        models.py
        serializers.py
        views.py
      billing/
        models.py
        serializers.py
        services.py
        views.py
      projects/
        models.py
        serializers.py
        views.py
    manage.py
    requirements.txt
    .env.example
  frontend/
    src/
      components/
      contexts/
      hooks/
      pages/
      routes/
      services/
      styles/
      utils/
    package.json
    .env.example
  docs/
    ARCHITECTURE.md
    API.md
    DATABASE.sql
    DEPLOY.md
    STRUCTURE.md
  .github/workflows/
    frontend-pages.yml
  render.yaml
```

## Responsabilidades

- `backend/apps/*/services.py`: regras de negocio e integracoes externas.
- `backend/apps/*/views.py`: controllers REST.
- `backend/apps/core/permissions.py`: RBAC e permissoes reutilizaveis.
- `frontend/src/services`: cliente HTTP e contratos com a API.
- `frontend/src/routes`: protecao por autenticacao e role.
- `frontend/src/pages`: telas publicas, cliente e admin.
