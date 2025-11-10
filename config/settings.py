import os
from pathlib import Path
from datetime import timedelta

import environ

TELEGRAM_BOT_INGEST_TOKEN = os.getenv("TELEGRAM_BOT_INGEST_TOKEN")

# ===================================
# BASE SETTINGS
# ===================================
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# SECURITY
SECRET_KEY = env("SECRET_KEY", default="django-insecure-secret-key")

DEBUG = bool(os.getenv("DEBUG", "True") == "True")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

# Reverse proxy/Nginx or dockerized deployments
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ===================================
# APPLICATIONS
# ===================================
DJANGO_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.users",
    "apps.tests",
    "apps.user_tests",
    "apps.payments",
    "apps.core",
    "apps.teacher_checking",
    "apps.speaking",
    "apps.profiles",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ===================================
# MIDDLEWARE
# ===================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CORS first, after sessions
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ===================================
# URLS & WSGI
# ===================================
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# ===================================
# DATABASE (Docker)
# ===================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
    }
}

# ===================================
# AUTH USER MODEL
# ===================================
AUTH_USER_MODEL = "users.User"

# ===================================
# TEMPLATES
# ===================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

# ===================================
# PASSWORD VALIDATION
# ===================================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ===================================
# INTERNATIONALIZATION
# ===================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

# ===================================
# STATIC & MEDIA
# ===================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ===================================
# DEFAULTS
# ===================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ===================================
# REST FRAMEWORK & JWT
# ===================================
REST_FRAMEWORK = {
    # --- Auth / Perms
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # Browsable API uchun faqat DEBUG’da sessiya auth qulay:
        *(
            ("rest_framework.authentication.SessionAuthentication",)
            if DEBUG
            else tuple()
        ),
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    # --- Parsers / Renderers
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        *(("rest_framework.renderers.BrowsableAPIRenderer",) if DEBUG else tuple()),
    ),
    # --- Filtering / Searching / Ordering (ko‘p endpointlarda kerak bo‘ladi)
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    # --- Throttling
    # Eslatma: scope-lar ishlashi uchun ScopedRateThrottle NI ham yoqish shart,
    # va view’larda `throttle_scope = "otp_ingest"` kabi qo‘yish kerak bo‘ladi.
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/min",
        "user": "200/min",
        "otp_ingest": "60/min",
        "otp_verify": "20/min",
        "otp_status": "60/min",
    },
    # --- API schema (Swagger/OpenAPI)
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # --- Datetime format
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%SZ",
    # --- Pagination (tavsiya etiladi: count ko‘rinadi, bo‘sh ro‘yxatda ham aniqroq)
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # --- Testlar uchun qulaylik
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}


# ===================================
# Simple JWT
# ===================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ALGORITHM": "HS256",
    # "SIGNING_KEY": SECRET_KEY,  # odatda default SECRET_KEY ishlatiladi
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}


SPECTACULAR_SETTINGS = {
    "TITLE": "CDI IELTS API",
    "DESCRIPTION": "IELTS Practice Platform backend (accounts/users/profiles/test flows)",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": True,  # <-- shu joyni True qilamiz
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SERVE_AUTHENTICATION": [],
}


CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

# ===================================
# CORS (Docker + Frontend)
# ===================================
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)
# CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# ===================================
# TELEGRAM BOT & SECURITY
# ===================================
TELEGRAM_BOT_INGEST_TOKEN = env("TELEGRAM_BOT_INGEST_TOKEN", default="super-secret")


# click.uz to‘lov tizimi sozlamalari
CLICK = {
    "SERVICE_ID": env.int("CLICK_SERVICE_ID"),
    "MERCHANT_ID": env.int("CLICK_MERCHANT_ID"),
    "MERCHANT_USER_ID": env.int("CLICK_MERCHANT_USER_ID"),
    "SECRET_KEY": env("CLICK_SECRET_KEY"),
    "BASE_URL": env("CLICK_BASE_URL"),
    "RETURN_URL": env("CLICK_RETURN_URL"),
    "CANCEL_URL": env("CLICK_CANCEL_URL"),
    "ALLOWED_IPS": [
        "91.204.239.44",
        "91.204.239.45",
    ],
}

PAYMENTS = {
    "MIN_TOPUP": 1000,  # 1 000 UZS
    "MAX_TOPUP": 5_000_000,  # 5 mln UZS
}


SPEAKING = {
    "FEE": 50000,
}
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_ADMIN_CHAT_ID = env("TELEGRAM_ADMIN_CHAT_ID", default="")

# ===================================
# LOGGING (useful in Docker)
# ===================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name} {message}", "style": "{"},
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
