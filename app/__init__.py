from flask import Flask
from .extensions import *

#importing the routes
from .routes import main

def create_app():
    app = Flask(__name__)

    app.config.from_object('config.DevelopmentConfig')

    #initialize the extensions

    #registering blueprints
    app.register_blueprint(main)


    return app