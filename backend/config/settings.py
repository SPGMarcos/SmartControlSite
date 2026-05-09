from datetime import timedelta
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=None, cast=str):
    value = os.environ.get(name, default)
    if cast is bool:
        return str(value).lower() in {"1", "true", "yes", "on"}
    if cast is int:
        return int(value)
    if cast is list:
        if value in (None, ""):
            return []
        return [item.strip() for item in str(value).split(",") if item.strip()]
    return value


SECRET_KEY = env("DJANGO_SECRET_KEY", "unsafe-dev-key-change-me")
DEBUG = env("DJANGO_DEBUG", False, bool)
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1", list)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "csp",
    "apps.core",
    "apps.users",
    "apps.clients",
    "apps.billing",
    "apps.projects",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.RequestIdMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "smartcontrol_sites"),
        "USER": env("POSTGRES_USER", "smartcontrol"),
        "PASSWORD": env("POSTGRES_PASSWORD", "smartcontrol_dev_password"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"sslmode": env("POSTGRES_SSLMODE", "prefer")},
    }
}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "80/hour",
        "user": "1000/hour",
        "auth": "8/minute",
        "register": "5/hour",
        "password_reset": "5/hour",
        "checkout": "20/hour",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SECRET_KEY", SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOWED_ORIGINS = env("DJANGO_CORS_ALLOWED_ORIGINS", "http://localhost:5173", list)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:5173", list)

SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", False, bool)
SECURE_HSTS_SECONDS = 0 if DEBUG else env("SECURE_HSTS_SECONDS", 31536000, int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

FRONTEND_URL = env("FRONTEND_URL", "http://localhost:5173")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", "")
STRIPE_SUCCESS_URL = env("STRIPE_SUCCESS_URL", f"{FRONTEND_URL}/dashboard?checkout=success")
STRIPE_CANCEL_URL = env("STRIPE_CANCEL_URL", f"{FRONTEND_URL}/dashboard?checkout=cancel")
JWT_REFRESH_COOKIE_NAME = env("JWT_REFRESH_COOKIE_NAME", "sc_refresh")
JWT_REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "https://js.stripe.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'", FRONTEND_URL, "https://api.stripe.com")
CSP_FRAME_SRC = ("'self'", "https://js.stripe.com", "https://hooks.stripe.com")
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_like": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s request_id=%(request_id)s",
        },
        "simple": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "filters": {
        "request_id": {"()": "apps.core.logging.RequestIdLogFilter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json_like",
            "filters": ["request_id"],
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
