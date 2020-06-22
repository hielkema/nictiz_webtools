from app.settings.base import *


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+kbl$5-%8x4dn$l_cf%^^6kjb0+f5lm3rvlt56+z!)*#_^-5gm'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
SESSION_COOKIE_DOMAIN = "localhost"
CSRF_COOKIE_DOMAIN = 'localhost'


CORS_ORIGIN_WHITELIST = [
    "http://localhost:9123",
    "http://127.0.0.1:9123"
]
# CORS_ORIGIN_ALLOW_ALL = True
CORS_SUPPORTS_CREDENTIALS = True
CORS_ALLOW_CREDENTIALS = True
SESSION_COOKIE_SAMESITE=None

def show_toolbar(request):
    return True
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK" : show_toolbar,
}

INSTALLED_APPS = ('debug_toolbar',) + INSTALLED_APPS
MIDDLEWARE     = ('debug_toolbar.middleware.DebugToolbarMiddleware',) + MIDDLEWARE
INTERNAL_IPS = [
    '127.0.0.1',
    '0.0.0.0',
    'localhost',
]

DATABASES = {
   'default': {
       'ENGINE': 'django.db.backends.postgresql_psycopg2',
       'NAME': 'tickets',
       'USER': 'tickets',
       'PASSWORD': 'tickets',
       'HOST': 'postgres',
       'PORT': '5432',
   }
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # }
}