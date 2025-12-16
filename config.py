import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Database configuration
    db_uri = os.environ.get('DATABASE_URL') or 'sqlite:///medica.db'
    if 'postgres' in db_uri:
        db_uri = 'postgresql+pg8000://' + db_uri.split('://', 1)[1]
    SQLALCHEMY_DATABASE_URI = db_uri
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)


class ProductionConfig(Config):
    DEBUG = False
    # Database configuration for production
    db_uri = os.environ.get('DATABASE_URL')
    if db_uri and 'postgres' in db_uri:
        db_uri = 'postgresql+pg8000://' + db_uri.split('://', 1)[1]
    SQLALCHEMY_DATABASE_URI = db_uri


class DevelopmentConfig(Config):
    DEBUG = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

