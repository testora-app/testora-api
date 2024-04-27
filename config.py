import os


class BaseConfig(object):
    basedir = os.path.abspath(os.path.dirname(__file__))
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    FLASK_ENV = 'development'
    SECRET_KEY = "app-secret-key"

class TestingConfig(BaseConfig):
    DEBUG = True
    FLASK_ENV = 'testing'


