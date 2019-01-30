import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

### SETTINGS FOR DEVELOPMENT

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'vyjrAgfwutopdFx2ot7VGgjcsB2RAE2TKbocQjWJTHVjybekAg'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'orpheus',
        'USER': 'orpheus',
        'PASSWORD': 'QEjoMUE9FkuKxSxjSkY8FPb2fVtPY2',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
