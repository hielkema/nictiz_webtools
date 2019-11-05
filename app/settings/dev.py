from app.settings.base import *


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+kbl$5-%8x4dn$l_cf%^^6kjb0+f5lm3rvlt56+z!)*#_^-5gm'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ('debug_toolbar',)
MIDDLEWARE     += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
INTERNAL_IPS = [
    '127.0.0.1',
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