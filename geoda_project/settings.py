"""
Django settings for geoda_project project.

Generated by 'django-admin startproject' using Django 2.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/

Default Django settings are defined in the module
django/conf/global_settings.py

To make sure settings are suitable for production see
https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', False) == 'True'
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY', 'o+^%z1pkglqpsxjhdaj_u)9pfpybx0l7ko$x!d=j+y0x8qn*c)'
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [h for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')]

# Internationalization - https://docs.djangoproject.com/en/4.0/topics/i18n/
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = os.environ.get('TZ', 'Europe/Madrid')
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'es-es'
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(BASE_DIR / 'locale')]

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.mysql'),  # Database engine
        'NAME': os.environ.get('DB_NAME'),  # Database name
        'USER': os.environ.get('DB_USER'),  # Database user
        'PASSWORD': os.environ.get('DB_PASSWORD'),  # Database password
        'HOST': os.environ.get('DB_HOST'),  # Set to empty string for localhost.
        'PORT': '',  # Set to empty string for default.
        # Additional database options
        'OPTIONS': {'charset': os.environ.get('DB_CHARSET', 'utf8mb4')},
    }
}
# https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = 'geoda_project.urls'
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'geoda_project.wsgi.application'
# Necesario para LOGIN_URL
SITE_URL = os.environ.get('SITE_URL')

# APPS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local
    'geo.apps.GeoConfig',
    'accounts.apps.AccountsConfig',
    # 3rd Party
    'crispy_forms',  # https://github.com/django-crispy-forms/django-crispy-forms
    'crispy_bootstrap5',  # https://pypi.org/project/crispy-bootstrap5/
    'django_filters',  # https://pypi.org/project/django-filter/
    'django_tables2',  # https://github.com/jieter/django-tables2
    'social_django',  # https://github.com/python-social-auth/social-app-django
]

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = (
    'social_core.backends.saml.SAMLAuth',
    'django.contrib.auth.backends.ModelBackend',
)
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = 'accounts.CustomUser'
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = 'mis_cursos'
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = '/login/saml/?idp=lord'
LOGOUT_REDIRECT_URL = 'home'

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# STATIC FILES (CSS, Javascript, images)
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/4.0/howto/static-files/

# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(BASE_DIR / 'staticfiles')
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [BASE_DIR / 'static']

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # https://docs.djangoproject.com/en/dev/ref/settings/#dirs
        'DIRS': [BASE_DIR / 'templates'],
        # https://docs.djangoproject.com/en/dev/ref/settings/#app-dirs
        'APP_DIRS': True,
        'OPTIONS': {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ]
        },
    }
]

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# SECURITY
# ------------------------------------------------------------------------------
# Tell the browser to send the cookies under an HTTPS connection only.
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', False) == 'True'
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', False) == 'True'
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = 'DENY'

# Enable when behind a load balancer or proxy. Otherwise OneLogin SAML may not work.
# The load balancer or proxy should be configured to add this header.
USE_X_FORWARDED_PORT = os.environ.get('USE_X_FORWARDED_PORT', False) == 'True'

# Tell Django to check this header to determine whether the request came in via HTTPS.
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'root@localhost')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.environ.get('EMAIL_PORT', 587)
EMAIL_USE_LOCALTIME = True
EMAIL_USE_TLS = True

# ADMIN
# ------------------------------------------------------------------------------
# A list of all the people who get code error notifications.
# When `DEBUG=False` and `AdminEmailHandler` is configured in `LOGGING` (done by default),
# Django emails these people the details of exceptions raised in the request/response cycle.
# See <https://docs.djangoproject.com/en/3.2/howto/error-reporting/>
ADMIN_NAMES = [n for n in os.environ.get('ADMIN_NAMES', '').split(',')]
ADMIN_MAILS = [m for m in os.environ.get('ADMIN_MAILS', '').split(',')]
ADMINS = list(zip(ADMIN_NAMES, ADMIN_MAILS))
# A list that specifies who should get broken link notifications
# when `BrokenLinkEmailsMiddleware` is enabled.
MANAGERS = ADMINS


# SAML with Python Social Auth
# ----------------------------
# https://python-social-auth.readthedocs.io/en/latest/backends/saml.html

# When using PostgreSQL,
# it’s recommended to use the built-in JSONB field to store the extracted extra_data.
# To enable it define the setting:
# SOCIAL_AUTH_POSTGRES_JSONFIELD = True
# Identifier of the SP entity (must be a URI)
SOCIAL_AUTH_SAML_SP_ENTITY_ID = os.environ.get(
    'SOCIAL_AUTH_SAML_SP_ENTITY_ID', 'http://localhost:8001/accounts/metadata'
)
SOCIAL_AUTH_SAML_SP_PUBLIC_CERT = os.environ.get('SOCIAL_AUTH_SAML_SP_PUBLIC_CERT')
SOCIAL_AUTH_SAML_SP_PRIVATE_KEY = os.environ.get('SOCIAL_AUTH_SAML_SP_PRIVATE_KEY')
SOCIAL_AUTH_SAML_ORG_INFO = {
    'en-US': {
        'name': 'geoda2',
        'displayname': 'Gestión de la Enseñanza Online',
        'url': f'{SITE_URL}',
    }
}
SOCIAL_AUTH_SAML_TECHNICAL_CONTACT = {
    'givenName': os.environ.get('SOCIAL_AUTH_SAML_TECHNICAL_CONTACT_NAME'),
    'emailAddress': os.environ.get('SOCIAL_AUTH_SAML_TECHNICAL_CONTACT_MAIL'),
}
SOCIAL_AUTH_SAML_SUPPORT_CONTACT = {
    'givenName': os.environ.get('SOCIAL_AUTH_SAML_SUPPORT_CONTACT_NAME'),
    'emailAddress': os.environ.get('SOCIAL_AUTH_SAML_SUPPORT_CONTACT_MAIL'),
}
# Si se cambia el backend de autenticación, actualizar `clean()` en `InvitacionForm`
IDP = os.environ.get('IDENTITY_PROVIDER')
SOCIAL_AUTH_SAML_ENABLED_IDPS = {
    # SIR: Servicio de Federación de Identidades de RedIRIS <https://www.rediris.es/sir2/>
    'lord': {
        'entity_id': os.environ.get('IDP_ENTITY_ID'),
        'url': f'{IDP}/saml2/idp/SSOService.php',
        'slo_url': f'{IDP}/saml2/idp/SingleLogoutService.php',
        'x509cert': os.environ.get('X509CERT'),
        'attr_user_permanent_id': 'urn:oid:0.9.2342.19200300.100.1.1',  # 'uid',
        'attr_full_name': 'cn',  # 'urn:oid:2.5.4.3'
        'attr_first_name': 'givenName',  # 'urn:oid:2.5.4.42'
        'attr_last_name': 'sn',  # 'urn:oid:2.5.4.4'
        'attr_username': 'urn:oid:0.9.2342.19200300.100.1.1',  # 'uid',
        # 'attr_email': 'email',  # 'urn:oid:0.9.2342.19200300.100.1.3'
    }
}

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    # 'social_core.pipeline.mail.mail_validation',
    # 'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    # Actualizar con los datos de Gestión de Identidades
    'accounts.pipeline.get_identidad',
)

SOCIAL_AUTH_URL_NAMESPACE = 'social'

if DEBUG:
    # DJANGO-DEBUG-TOOLBAR - <https://github.com/jazzband/django-debug-toolbar>
    # ------------------------------------------------------------------------------
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
    INSTALLED_APPS += ['debug_toolbar', 'django_fastdev']  # noqa F405
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

# WEB SERVICE de GESTIÓN DE IDENTIDADES
WSDL_IDENTIDAD = os.environ.get('WSDL_IDENTIDAD')
USER_IDENTIDAD = os.environ.get('USER_IDENTIDAD')
PASS_IDENTIDAD = os.environ.get('PASS_IDENTIDAD')

# WEB SERVICE de GESTIÓN DE IDENTIDADES para vincular usuarios externos
WSDL_VINCULACIONES = os.environ.get('WSDL_VINCULACIONES')
USER_VINCULACIONES = os.environ.get('USER_VINCULACIONES')
PASS_VINCULACIONES = os.environ.get('PASS_VINCULACIONES')
