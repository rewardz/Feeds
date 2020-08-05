from .default import *

EXTERNAL_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'easy_thumbnails',
    'image_cropping',
)

INTERNAL_APPS = (
    'news_feed.tests.profiles',
    'feeds',
)

INSTALLED_APPS = EXTERNAL_APPS + INTERNAL_APPS

ROOT_URLCONF = 'news_feed.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

REST_FRAMEWORK = {
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S',
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

AUTH_USER_MODEL = 'profiles.CustomUser'
CUSTOM_USER_MODEL = 'news_feed.tests.profiles.models.CustomUser'
ORGANIZATION_MODEL = 'news_feed.tests.profiles.models.Organization'
DEPARTMENT_MODEL = 'news_feed.tests.profiles.models.Department'
PROFILE_IMAGE_PROPERTY = 'thumbnail_img_url'
NO_PROFILE_IMAGE = ''
PENDING_EMAIL = 'news_feed.tests.profiles.models.PendingEmail'
PUSH_NOTIFICATION = 'news_feed.tests.profiles.models.PushNotification'
POST_NOTIFICATION_OBJECT_TYPE = 'news_feed.tests.profiles.constants.NOTIFICATION_OBJECTS'
