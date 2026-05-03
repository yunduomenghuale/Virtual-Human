"""Django settings for 数字人 / 实验室消防安全 AI 系统."""
import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

# 国内访问 huggingface.co 不稳定时,通过 HF_ENDPOINT 改走镜像(如 https://hf-mirror.com)
# 需要在 sentence-transformers / huggingface_hub 被导入前写入 os.environ
_hf_endpoint = config('HF_ENDPOINT', default='')
if _hf_endpoint:
    os.environ.setdefault('HF_ENDPOINT', _hf_endpoint)

SECRET_KEY = config('DJANGO_SECRET_KEY', default='dev-insecure-key-change-me')
DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='*', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',

    'apps.users',
    'apps.knowledge',
    'apps.reports',
    'apps.hazards',
    'apps.analytics',
    'apps.skill_permissions',
    'apps.agent',
    'apps.common',
    'apps.labs',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 6}},
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = DATA_DIR

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== DRF =====
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ===== CORS =====
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ===== LLM 配置 =====
TEXT_LLM_BASE_URL = config('TEXT_LLM_BASE_URL',
                           default='https://dashscope.aliyuncs.com/compatible-mode/v1')
TEXT_LLM_API_KEY = config('TEXT_LLM_API_KEY', default='')
TEXT_LLM_MODEL = config('TEXT_LLM_MODEL', default='qwen-plus')
FAST_LLM_MODEL = config('FAST_LLM_MODEL', default='')

VISION_LLM_BASE_URL = config('VISION_LLM_BASE_URL',
                             default='https://dashscope.aliyuncs.com/compatible-mode/v1')
VISION_LLM_API_KEY = config('VISION_LLM_API_KEY', default='')
VISION_LLM_MODEL = config('VISION_LLM_MODEL', default='qwen-vl-plus')

EMBEDDING_MODEL = config('EMBEDDING_MODEL', default='text-embedding-v3')
EMBEDDING_LOCAL_MODEL = config('EMBEDDING_LOCAL_MODEL', default='BAAI/bge-small-zh-v1.5')
EMBEDDING_API_KEY = config('EMBEDDING_API_KEY', default='')
EMBEDDING_BASE_URL = config('EMBEDDING_BASE_URL',
                            default='https://dashscope.aliyuncs.com/compatible-mode/v1')
USE_MOCK_EMBEDDING = config('USE_MOCK_EMBEDDING', default=False, cast=bool)

# ===== RAG =====
VECTOR_STORE_PATH = DATA_DIR / 'vector_store' / 'index.json'
KNOWLEDGE_BASE_DIR = DATA_DIR / 'knowledge_base'

# ===== 上传 / 报告 / 隐患 输出目录 =====
UPLOAD_DIR = DATA_DIR / 'uploads'
REPORTS_DIR = DATA_DIR / 'reports'
HAZARDS_DIR = DATA_DIR / 'hazards'
for _d in (VECTOR_STORE_PATH.parent, KNOWLEDGE_BASE_DIR, UPLOAD_DIR, REPORTS_DIR, HAZARDS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
