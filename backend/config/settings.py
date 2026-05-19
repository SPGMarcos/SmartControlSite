from datetime import timedelta
import os
from pathlib import Path

from corsheaders.defaults import default_headers
import dj_database_url
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


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


def unique(items):
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result


def strip_trailing_slash(value):
    return str(value or "").strip().rstrip("/")


SECRET_KEY = env("DJANGO_SECRET_KEY", "unsafe-dev-key-change-me")
DEBUG = env("DJANGO_DEBUG", False, bool)
ALLOWED_HOSTS = env(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,smartcontrol-sites-api.onrender.com",
    list,
)
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", "")
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
ALLOWED_HOSTS = unique(ALLOWED_HOSTS)


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
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

DEFAULT_DATABASE_URL = (
    f"postgresql://{env('POSTGRES_USER', 'smartcontrol')}:"
    f"{env('POSTGRES_PASSWORD', 'smartcontrol_dev_password')}@"
    f"{env('POSTGRES_HOST', 'localhost')}:"
    f"{env('POSTGRES_PORT', '5432')}/"
    f"{env('POSTGRES_DB', 'smartcontrol_sites')}"
)
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
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
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),

    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),

    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),

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

FRONTEND_URL = strip_trailing_slash(env("FRONTEND_URL", "http://127.0.0.1:5173"))
FRONTEND_ORIGIN = strip_trailing_slash(env("FRONTEND_ORIGIN", FRONTEND_URL))
FRONTEND_ORIGINS = unique(
    [strip_trailing_slash(item) for item in env("FRONTEND_ORIGINS", FRONTEND_ORIGIN, list)]
)
DEFAULT_DEV_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]
DEFAULT_RENDER_ORIGINS = [
    "https://smartcontrol-sites-api.onrender.com",
    "https://smartcontrol-sites-frontend.onrender.com",
]
DEFAULT_GITHUB_PAGES_ORIGINS = [
    "https://spgmarcos.github.io",
]
CORS_ALLOWED_ORIGINS = unique(
    [strip_trailing_slash(item) for item in env("DJANGO_CORS_ALLOWED_ORIGINS", "", list)]
    + FRONTEND_ORIGINS
    + DEFAULT_DEV_ORIGINS
    + DEFAULT_RENDER_ORIGINS
    + DEFAULT_GITHUB_PAGES_ORIGINS
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = unique(list(default_headers) + [
    "x-csrftoken",
])
CSRF_TRUSTED_ORIGINS = unique(
    [strip_trailing_slash(item) for item in env("DJANGO_CSRF_TRUSTED_ORIGINS", "", list)]
    + CORS_ALLOWED_ORIGINS
)

SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", False, bool)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 0 if DEBUG else env("SECURE_HSTS_SECONDS", 31536000, int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
COOKIE_SAMESITE = env("COOKIE_SAMESITE", "Lax" if DEBUG else "None")
SESSION_COOKIE_SAMESITE = COOKIE_SAMESITE
CSRF_COOKIE_SAMESITE = COOKIE_SAMESITE
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_NAME = env("CSRF_COOKIE_NAME", "csrftoken")
CSRF_COOKIE_PATH = "/"
CSRF_USE_SESSIONS = False

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", "")
STRIPE_SUCCESS_URL = env("STRIPE_SUCCESS_URL", f"{FRONTEND_URL}/billing?checkout=success&session_id={{CHECKOUT_SESSION_ID}}")
STRIPE_CANCEL_URL = env("STRIPE_CANCEL_URL", f"{FRONTEND_URL}/billing?checkout=cancel")
STRIPE_PORTAL_RETURN_URL = env("STRIPE_PORTAL_RETURN_URL", f"{FRONTEND_URL}/billing")
JWT_REFRESH_COOKIE_NAME = env("JWT_REFRESH_COOKIE_NAME", "sc_refresh")
JWT_REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60
JWT_REFRESH_COOKIE_SAMESITE = env("JWT_REFRESH_COOKIE_SAMESITE", COOKIE_SAMESITE)
JWT_REFRESH_COOKIE_SECURE = env("JWT_REFRESH_COOKIE_SECURE", not DEBUG, bool)

PROJECT_ATTACHMENT_MAX_FILES = env("PROJECT_ATTACHMENT_MAX_FILES", 10, int)
PROJECT_ATTACHMENT_MAX_SIZE = env("PROJECT_ATTACHMENT_MAX_SIZE", 10 * 1024 * 1024, int)
PROJECT_ATTACHMENT_ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".txt",
    ".zip",
}
PROJECT_ATTACHMENT_ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "application/zip",
    "application/x-zip-compressed",
}

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "https://js.stripe.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = tuple(
    unique(
        [
            "'self'",
            FRONTEND_ORIGIN,
            *FRONTEND_ORIGINS,
            *DEFAULT_RENDER_ORIGINS,
            *DEFAULT_GITHUB_PAGES_ORIGINS,
            "https://smartcontrol-sites-api.onrender.com",
            "https://api.stripe.com",
        ]
    )
)
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
