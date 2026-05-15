import os
from datetime import timedelta

class Config:
    # Em produção, defina SESSION_SECRET no ambiente. O fallback existe só para teste local.
    SECRET_KEY = os.environ.get('SESSION_SECRET') or os.environ.get('SECRET_KEY') or 'serviceflow-dev-secret-change-me'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///serviceflow_dev.sqlite3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

    JSON_SORT_KEYS = False

    # Upload de avatar/perfil — limite conservador para teste e produção.
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    PROFILE_UPLOAD_FOLDER = 'uploads/profiles'
    PROFILE_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
