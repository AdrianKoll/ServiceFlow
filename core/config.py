import os
from datetime import timedelta

class Config:
    ENV = os.environ.get('SERVICEFLOW_ENV', os.environ.get('FLASK_ENV', 'development')).lower()
    SECRET_KEY = os.environ.get('SESSION_SECRET') or os.environ.get('SECRET_KEY')
    if not SECRET_KEY and ENV != 'production':
        SECRET_KEY = 'serviceflow-local-development-only'
    if ENV == 'production' and not SECRET_KEY:
        raise RuntimeError('SESSION_SECRET deve ser definida em produção.')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///serviceflow_dev.sqlite3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_NAME = 'serviceflow_session'
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_HEADERS_ENABLED = True

    JSON_SORT_KEYS = False

    PROFILE_UPLOAD_FOLDER = 'uploads/profiles'
    PROFILE_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
