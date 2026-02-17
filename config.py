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
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    CORS_METHODS = ["POST", "PUT", "GET", "OPTIONS", "DELETE"]
    CORS_ORIGIN = ["http://localhost:3000", "http://localhost:3050"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
    CORS_AUTOMATIC_OPTIONS = True


class StagingConfig(BaseConfig):
    FLASK_ENV = "production"
    ITEMS_PER_PAGE = 1000
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("POSTGRES_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 15,
        "max_overflow": 30,
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    CORS_METHODS = ["POST", "PUT", "GET", "OPTIONS", "DELETE"]
    CORS_ORIGIN = ["https://staging.preppee.online"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
    CORS_AUTOMATIC_OPTIONS = True


class ProductionConfig(BaseConfig):
    FLASK_ENV = "production"
    ITEMS_PER_PAGE = 1000
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("POSTGRES_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 20,
        "max_overflow": 40,
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    CORS_METHODS = ["POST", "PUT", "GET", "OPTIONS", "DELETE"]
    CORS_ORIGIN = ["https://preppee.online", "https://www.preppee.online"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
    CORS_AUTOMATIC_OPTIONS = True


class TestingConfig(BaseConfig):
    DEBUG = True
    FLASK_ENV = "testing"
