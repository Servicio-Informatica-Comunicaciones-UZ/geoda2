"""
Django settings for geoda_project project.

Generated by 'django-admin startproject' using Django 2.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import socket


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "o+^%z1pkglqpsxjhdaj_u)9pfpybx0l7ko$x!d=j+y0x8qn*c)"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", False) == "True"

ALLOWED_HOSTS = ["*"]  # []

# A list of all the people who get code error notifications.
# When `DEBUG=False` and `AdminEmailHandler` is configured in `LOGGING` (done by default),
# Django emails these people the details of exceptions raised in the request/response cycle.
# See <https://docs.djangoproject.com/en/3.2/howto/error-reporting/>
ADMINS = [('Root', 'root@localhost')]
# A list that specifies who should get broken link notifications
# when `BrokenLinkEmailsMiddleware` is enabled.
MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "root@localhost")
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_USE_LOCALTIME = True
EMAIL_USE_TLS = True


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local
    "geo.apps.GeoConfig",
    "accounts.apps.AccountsConfig",
    # 3rd Party
    "crispy_forms",  # https://github.com/django-crispy-forms/django-crispy-forms
    "django_filters",  # https://pypi.org/project/django-filter/
    "django_tables2",  # https://github.com/jieter/django-tables2
    "social_django",  # https://github.com/python-social-auth/social-app-django
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "geoda_project.urls"

SITE_URL = os.environ.get("SITE_URL")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ]
        },
    }
]

WSGI_APPLICATION = "geoda_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("ENGINE", "django.db.backends.mysql"),  # Database engine
        "NAME": os.environ.get("DB_NAME"),  # Database name
        "USER": os.environ.get("DB_USER"),  # Database user
        "PASSWORD": os.environ.get("DB_PASSWORD"),  # Database password
        "HOST": os.environ.get("DB_HOST"),  # Set to empty string for localhost.
        "PORT": "",  # Set to empty string for default.
        # Additional database options
        "OPTIONS": {"charset": os.environ.get("DB_CHARSET", "utf8mb4")},
    }
}
# https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "es-es"

TIME_ZONE = os.environ.get("TZ")

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

AUTH_USER_MODEL = "accounts.CustomUser"
LOGIN_URL = "/login/saml/?idp=lord"
LOGIN_REDIRECT_URL = "mis_cursos"
LOGOUT_REDIRECT_URL = "home"


# ## SAML with Python Social Auth ## #
# https://python-social-auth.readthedocs.io/en/latest/backends/saml.html

AUTHENTICATION_BACKENDS = (
    "social_core.backends.saml.SAMLAuth",
    "django.contrib.auth.backends.ModelBackend",
)
# When using PostgreSQL,
# it’s recommended to use the built-in JSONB field to store the extracted extra_data.
# To enable it define the setting:
# SOCIAL_AUTH_POSTGRES_JSONFIELD = True
# Identifier of the SP entity (must be a URI)
SOCIAL_AUTH_SAML_SP_ENTITY_ID = os.environ.get(
    "SOCIAL_AUTH_SAML_SP_ENTITY_ID", "http://localhost:8001/accounts/metadata"
)
SOCIAL_AUTH_SAML_SP_PUBLIC_CERT = os.environ.get("SOCIAL_AUTH_SAML_SP_PUBLIC_CERT")
SOCIAL_AUTH_SAML_SP_PRIVATE_KEY = os.environ.get("SOCIAL_AUTH_SAML_SP_PRIVATE_KEY")
SOCIAL_AUTH_SAML_ORG_INFO = {
    "en-US": {
        "name": "geoda2",
        "displayname": "Gestión de la Enseñanza Online",
        "url": f"{SITE_URL}",
    }
}
SOCIAL_AUTH_SAML_TECHNICAL_CONTACT = {
    "givenName": os.environ.get("SOCIAL_AUTH_SAML_TECHNICAL_CONTACT_NAME"),
    "emailAddress": os.environ.get("SOCIAL_AUTH_SAML_TECHNICAL_CONTACT_MAIL"),
}
SOCIAL_AUTH_SAML_SUPPORT_CONTACT = {
    "givenName": os.environ.get("SOCIAL_AUTH_SAML_SUPPORT_CONTACT_NAME"),
    "emailAddress": os.environ.get("SOCIAL_AUTH_SAML_SUPPORT_CONTACT_MAIL"),
}
# Si se cambia el backend de autenticación, actualizar clean() en InvitacionForm
IDP = os.environ.get("IDENTITY_PROVIDER")
SOCIAL_AUTH_SAML_ENABLED_IDPS = {
    "lord": {
        "entity_id": os.environ.get("IDP_ENTITY_ID"),
        "url": f"{IDP}/saml2/idp/SSOService.php",
        "slo_url": f"{IDP}/saml2/idp/SingleLogoutService.php",
        "x509cert": os.environ.get("X509CERT"),
        "attr_user_permanent_id": "urn:oid:0.9.2342.19200300.100.1.1",  # "uid",
        "attr_full_name": "cn",  # "urn:oid:2.5.4.3"
        "attr_first_name": "givenName",  # "urn:oid:2.5.4.42"
        "attr_last_name": "sn",  # "urn:oid:2.5.4.4"
        "attr_username": "urn:oid:0.9.2342.19200300.100.1.1",  # "uid",
        # "attr_email": "email",            # "urn:oid:0.9.2342.19200300.100.1.3"
    }
}

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    # "social_core.pipeline.mail.mail_validation",
    # "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    # Actualizar con los datos de Gestión de Identidades
    "accounts.pipeline.get_identidad",
)

SOCIAL_AUTH_URL_NAMESPACE = "social"

# CRISPY FORMS
CRISPY_TEMPLATE_PACK = "bootstrap4"

if DEBUG:
    # DJANGO-DEBUG-TOOLBAR - <https://github.com/jazzband/django-debug-toolbar>
    # ------------------------------------------------------------------------------
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
    INSTALLED_APPS += ['debug_toolbar']  # noqa F405
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa F405
    # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
    DEBUG_TOOLBAR_CONFIG = {
        'DISABLE_PANELS': ['debug_toolbar.panels.redirects.RedirectsPanel'],
        'SHOW_TEMPLATE_CONTEXT': True,
    }
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips

    import socket  # only if you haven't already imported this

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind('.')] + '.1' for ip in ips] + ['127.0.0.1', '10.0.2.2']

# DATOS DE LA PLATAFORMA
URL_PLATAFORMA = os.environ.get("URL_PLATAFORMA")
GEO_TOKEN = os.environ.get("GEO_TOKEN")
GEODAWS_TOKEN = os.environ.get("GEODAWS_TOKEN")
API_URL = f"{URL_PLATAFORMA}/webservice/rest/server.php"

# DATOS DE WS GESTIÓN DE IDENTIDADES
WSDL_IDENTIDAD = os.environ.get("WSDL_IDENTIDAD")
USER_IDENTIDAD = os.environ.get("USER_IDENTIDAD")
PASS_IDENTIDAD = os.environ.get("PASS_IDENTIDAD")

# DATOS DE WS GESTIÓN DE IDENTIDADES para vincular usuarios externos
WSDL_VINCULACIONES = os.environ.get("WSDL_VINCULACIONES")
USER_VINCULACIONES = os.environ.get("USER_VINCULACIONES")
PASS_VINCULACIONES = os.environ.get("PASS_VINCULACIONES")

# SECURITY
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# Enable when behind a load balancer or proxy. Otherwise OneLogin SAML may not work.
# The load balancer or proxy should be configured to add this header.
USE_X_FORWARDED_PORT = os.environ.get("USE_X_FORWARDED_PORT", False) == "True"

# Tell Django to check this header to determine whether the request came in via HTTPS.
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Tell the browser to send the cookies under an HTTPS connection only.
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", False) == "True"
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", False) == "True"
