"""
Django settings for geoda_project project.

Generated by 'django-admin startproject' using Django 2.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "xk6ujnt_zj7xlnt@c&$jc9f_=u3io5e!87imbqz4)=li*$tu%w"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", False) == "True"

ALLOWED_HOSTS = []  # ['*']


DEFAULT_FROM_EMAIL = "La Maestra <leocricia@manhattan.local>"
# Production value: 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = "smtp.manhattan.local"
EMAIL_HOST_USER = "mls"
EMAIL_HOST_PASSWORD = "plaff"
EMAIL_PORT = 587
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
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "geoda_project.urls"

SITE_URL = "http://geoda.local/"

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
        "ENGINE": "django.db.backends.mysql",  # Database engine
        "NAME": os.environ.get("DB_NAME"),  # Database name
        "USER": os.environ.get("DB_USER"),  # Database user
        "PASSWORD": os.environ.get("DB_PASSWORD"),  # Database password
        "HOST": os.environ.get("DB_HOST"),  # Set to empty string for localhost.
        "PORT": "",  # Set to empty string for default.
        # Additional database options
        "OPTIONS": {
            "charset": "utf8mb4"  # Requires `innodb_default_row_format = dynamic`
        },
    },
    "identidades": {
        "ENGINE": "django.db.backends.oracle",  # Database engine
        "NAME": "DELFOS",  # Database name
        "USER": "dodona",  # Database user
        "PASSWORD": "PopolWuj",  # Database password
        "HOST": "oraculo.unizar.es",  # Set to empty string for localhost.
        "PORT": "1521",  # Set to empty string for default.
        # Additional database options
        # "OPTIONS": {
        #     "charset": "WE8ISO8859P1",
        # }
    },
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"  # noqa: E501
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "es-es"

TIME_ZONE = "Europe/Madrid"

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
LOGIN_URL = f"{SITE_URL}login/saml/?idp=lord"
LOGIN_REDIRECT_URL = "mis-cursos"
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
SOCIAL_AUTH_SAML_SP_ENTITY_ID = "https://manhattan.local/accounts/metadata"
SOCIAL_AUTH_SAML_SP_PUBLIC_CERT = """Spam, ham and eggs"""
SOCIAL_AUTH_SAML_SP_PRIVATE_KEY = """Spam, sausages and bacon"""
SOCIAL_AUTH_SAML_ORG_INFO = {
    "en-US": {
        "name": "geoda2",
        "displayname": "Gestión de la Enseñanza Online",
        "url": "http://geoda.local",
    }
}
SOCIAL_AUTH_SAML_TECHNICAL_CONTACT = {
    "givenName": "Quique",
    "emailAddress": "quique@geoda.local",
}
SOCIAL_AUTH_SAML_SUPPORT_CONTACT = {
    "givenName": "Unidad de Calidad y Racionalización",
    "emailAddress": "calidad@geoda.local",
}
# Si se cambia el backend de autenticación, actualizar clean() en InvitacionForm
SOCIAL_AUTH_SAML_ENABLED_IDPS = {
    "lord": {
        "entity_id": "https://FIXME.idp.com/saml2/idp/metadata.php",
        "url": "https://FIXME.idp.com/saml2/idp/SSOService.php",
        "x509cert": "Lovely spam, wonderful spam",
        "attr_user_permanent_id": "uid",
        "attr_full_name": "cn",  # "urn:oid:2.5.4.3"
        "attr_first_name": "givenName",  # "urn:oid:2.5.4.42"
        "attr_last_name": "sn",  # "urn:oid:2.5.4.4"
        "attr_username": "uid",  # "urn:oid:0.9.2342.19200300.100.1.1"
        # "attr_email": "email",            # "urn:oid:0.9.2342.19200300.100.1.3"
    }
}

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    # Actualizar con los datos de Gestión de Identidades
    "accounts.pipeline.get_identidad",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

SOCIAL_AUTH_URL_NAMESPACE = "social"

# CRISPY FORMS
CRISPY_TEMPLATE_PACK = "bootstrap4"

# DATOS DE LA PLATAFORMA
URL_PLATAFORMA = "https://moodle.local"
GEO_TOKEN = "fabadabaca1a0cafecaca0"
GEODAWS_TOKEN = "1acebadaacabad3c0d1f1cada"
API_URL = f"{URL_PLATAFORMA}/webservice/rest/server.php"
