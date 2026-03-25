"""Django settings for the words project."""

from datetime import timedelta
from os import getenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT = "words"
APP = "wordsapp"


def get_bool(name: str, default: bool = False) -> bool:
    """Return a boolean environment value."""
    value = getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


DEBUG = get_bool("DEBUG", True)
SECRET_KEY = getenv("SECRET_KEY", "words-dev-secret-key")
PROJECT_DOMAIN = getenv("PROJECT_DOMAIN", "localhost")
FRONTEND_URL = getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
FRONTEND_URL2 = getenv("FRONTEND_URL2", "").rstrip("/")
INTERNAL_IP = getenv("INTERNAL_IP", "127.0.0.1")
STATIC_URL = getenv("STATIC_URL", "/static/")
TIME_ZONE = getenv("TIME_ZONE", "America/Toronto")

ALLOWED_HOSTS = [
    host
    for host in {
        PROJECT_DOMAIN,
        "localhost",
        "127.0.0.1",
    }
    if host
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_registration",
    APP,
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "words.urls"
WSGI_APPLICATION = "words.wsgi.application"

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

DATABASE_ENGINE = getenv("DB_ENGINE", "django.db.backends.sqlite3")
if DATABASE_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DATABASE_ENGINE,
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DATABASE_ENGINE,
            "NAME": getenv("DB_NAME", PROJECT),
            "USER": getenv("DB_USER", "root"),
            "PASSWORD": getenv("DB_PASSWORD", "password"),
            "HOST": getenv("DB_HOST", "127.0.0.1"),
            "PORT": getenv("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }

AUTH_USER_MODEL = "wordsapp.User"
AUTH_ANONYMOUS_MODEL = "wordsapp.models.UserAnonymous"
AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_TZ = True

STATIC_ROOT = BASE_DIR / "static"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = getenv("ADMIN_EMAIL", "admin@example.com")

CORS_ALLOWED_ORIGINS = [url for url in [FRONTEND_URL, FRONTEND_URL2] if url]
CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

REST_REGISTRATION = {
    "USER_LOGIN_FIELDS": ["username"],
    "REGISTER_SERIALIZER_CLASS": "wordsapp.serializers.WordsRegisterSerializer",
    "REGISTER_SERIALIZER_PASSWORD_CONFIRM": False,
    "REGISTER_VERIFICATION_ENABLED": True,
    "REGISTER_EMAIL_VERIFICATION_URL": f"{FRONTEND_URL}/verify-email/",
    "REGISTER_VERIFICATION_URL": f"{FRONTEND_URL}/verify-user/",
    "RESET_PASSWORD_VERIFICATION_URL": f"{FRONTEND_URL}/reset-password/",
    "RESET_PASSWORD_SERIALIZER_PASSWORD_CONFIRM": False,
    "CHANGE_PASSWORD_SERIALIZER_PASSWORD_CONFIRM": False,
    "VERIFICATION_FROM_EMAIL": DEFAULT_FROM_EMAIL,
}
