import os
import secrets

from dotenv import load_dotenv

load_dotenv()


class BaseConfig(object):
    basedir = os.path.abspath(os.path.dirname(__file__))
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    FLASK_ENV = "development"
    ITEMS_PER_PAGE = 1000
    SECRET_KEY = os.getenv("SECRET_KEY", str(secrets.token_hex()))
    SQLALCHEMY_DATABASE_URI = os.getenv("POSTGRES_URI", "sqlite:///site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_METHODS = ["POST", "PUT", "GET", "OPTIONS", "DELETE"]
    CORS_ORIGIN = ["http://localhost:3000", "*"]
    CORS_ALLOW_HEADERS = "*"
    CORS_AUTOMATIC_OPTIONS = True


class StagingConfig(BaseConfig):
    FLASK_ENV = "production"
    ITEMS_PER_PAGE = 1000
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("POSTGRES_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_METHODS = ["POST", "PUT", "GET", "OPTIONS", "DELETE"]
    CORS_ORIGIN = ["http://localhost:3000", "*"]
    CORS_ALLOW_HEADERS = "*"
    CORS_AUTOMATIC_OPTIONS = True


class TestingConfig(BaseConfig):
    DEBUG = True
    FLASK_ENV = "testing"
