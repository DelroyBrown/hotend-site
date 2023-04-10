import os
from dotenv import load_dotenv
import django_heroku
import dj_database_url

load_dotenv()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = bool(int(os.environ.get("DEBUG", 1)))
SECRET_KEY = "local_key" if DEBUG else os.environ.get("SECRET_KEY")

# BASE_URL = "https://production-monitor.herokuapp.com"
ALLOWED_HOSTS = ["*"] if DEBUG else os.environ.get("ALLOWED_HOSTS", BASE_URL).split(",")

# Separate test mode flag.
# Django always runs tests with DEBUG=False regardless of the settings.py value, to get as close as possible
# to a realistic environment. We use some test-specific URLs in base_models, and want to disable authentication
# entirely when running unit tests, so we need some way of distinguishing this case.
TEST_MODE = bool(int(os.environ.get("TEST_MODE", 0)))


INSTALLED_APPS = [
    "base_models",
    "core",
    "projects.generic",
    # "projects.hemera",
    # "projects.integrated_hotend_press",
    # "projects.prusa_nube_press",
    # "projects.v6_component_qc",
    # "projects.v6_hot_tightening",
    "projects.v7_post_curing_qc",
    # "v7_label_generator",
    "web_interface",

    "rest_framework",
    "rest_framework.authtoken",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

REST_FRAMEWORK = {
    # In production, force authentication on every view (that doesn't have an explicit exception) and use
    # TokenAuthentication. API clients will need an access token to a valid user account; instructions
    # for generating these are at https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

if DEBUG:
    # For local development, enable SessionAuthentication.
    # This allows users to log in (via the admin) to use the browsable API, without disabling authentication
    # entirely (so we can test it).
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ]

if TEST_MODE:
    # When running unit tests, turn off the authentication so we can make API requests without having to
    # jump through loads of hoops.
    REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = [
        "rest_framework.permissions.AllowAny",
    ]


ROOT_URLCONF = "web_interface.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = "web_interface.wsgi.application"


# DATABASES = {
#     "default": dj_database_url.config(
#         default="postgres:///production_monitor",
#     ),
# }
# DATABASES["default"]["ATOMIC_REQUESTS"] = True
# DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': os.environ.get('NAME'),
#         'USER': os.environ.get('USER'),
#         'PASSWORD': os.environ.get('PASSWORD'),
#         'HOST': os.environ.get('HOST'),
#         'PORT': os.environ.get('PORT'),
#     },
#     'new_db': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': os.environ.get('NEW_DB_NAME'),
#         'USER': os.environ.get('NEW_DB_USER'),
#         'PASSWORD': os.environ.get('NEW_DB_PASSWORD'),
#         'HOST': os.environ.get('NEW_DB_HOST'),
#         'PORT': os.environ.get('NEW_DB_PORT'),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('TEST_DB_NAME'),
        'USER': os.environ.get('TEST_DB_USER'),
        'PASSWORD': os.environ.get('TEST_DB_PASSWORD'),
        'HOST': os.environ.get('TEST_DB_HOST'),
        'PORT': os.environ.get('TEST_DB_PORT'),
    }
}





LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"

# Switch off timezone support, so Django only uses naive local times.
# This makes it much easier to work with machines reporting timestamps. They can send us naive local times as well,
# and it should work (tm). No need to implement timezones across the entire production system.
USE_TZ = False


STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = os.environ.get("STATIC_URL", "/static/")
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)


# Allow larger form submissions than the default.
# This lets us handle large numbers of selected barcodes.
# The limit may need to be raised again in future.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

LOGIN_URL = "/admin/"
LOGIN_REDIRECT_URL = "/"
SECURE_SSL_REDIRECT = not DEBUG

DEBUG_PROPAGATE_EXCEPTIONS = True

# Custom functionality settings.
# The maximum number of Events that can be turned into a CSV - either of event data or of logs.
MAX_CSV_EVENT_COUNT = 100000

# Activate Django-Heroku.
django_heroku.settings(locals())

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

