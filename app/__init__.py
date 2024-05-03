from apiflask import APIFlask
from app.extensions import db, migrate, cors
from app.errorhandlers import (page_not_found, method_not_allowed, internal_server_error, forbidden)

#importing the routes
from .routes import main
from app.admin.routes import admin

# importing models or else the migrations won't find them wai
from app.admin.models import Admin, Subject, Topic

def create_app():
    app = APIFlask(__name__)

    app.config.from_object('config.DevelopmentConfig')

    #initialize the extensions
    cors.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)



    with app.app_context():
        # register errorhandlers
        app.register_error_handler(403, forbidden)
        app.register_error_handler(404, page_not_found)
        app.register_error_handler(405, method_not_allowed)
        app.register_error_handler(500, internal_server_error)

        #registering blueprints
        app.register_blueprint(main)
        app.register_blueprint(admin)


        


    return app