import os
from dotenv import load_dotenv
from urllib.parse import urlparse

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'

    # ФИКС: правильная обработка DATABASE_URL для Railway
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Проверяем, если это Railway MySQL URL (он может начинаться с mysql://)
        if database_url.startswith('mysql://'):
            # Заменяем mysql:// на mysql+pymysql:// для pymysql драйвера
            database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)

        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Локальная база по умолчанию
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'backend/app/static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

    # Email/SMTP
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ('1', 'true', 'yes')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME
    MAIL_ADMIN_TO = os.environ.get('MAIL_ADMIN_TO') or os.environ.get('MAIL_DEFAULT_SENDER')