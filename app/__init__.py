import traceback
from logging import error as log_error
from logging import info as log_info
from logging.config import dictConfig
from logging import getLogger, basicConfig

from apiflask import APIFlask, HTTPError
from apiflask.schemas import validation_error_detail_schema
from dotenv import load_dotenv
from flask import jsonify, request
from flask_migrate import upgrade
from marshmallow.exceptions import ValidationError
from sqlalchemy.exc import IntegrityError

from app._shared.api_errors import BaseError
from app._shared.services import (
    is_in_staging_environment,
    is_in_development_environment,
)
from app.errorhandlers import (
    forbidden,
    internal_server_error,
    method_not_allowed,
    page_not_found,
)
from app.extensions import cors, db, migrate

# importing the routes
from .routes import main
from app.admin.routes import admin
from app.school.routes import school
from app.staff.routes import staff
from app.student.routes import student
from app.test.routes import testr
from app.notifications.routes import notification
from app.analytics.routes import analytics
from app.subscriptions.routes import subscription
from app.achievements.routes import achievements
from app.qa.routes import qa


load_dotenv()


def create_super_admin_if_not_exists():
    import os

    from app.admin.operations import admin_manager

    admin_email, admin_username, admin_password = (
        os.getenv("ADMIN_EMAIL"),
        os.getenv("ADMIN_USERNAME"),
        os.getenv("ADMIN_PASSWORD"),
    )

    if admin_email and not admin_manager.get_admin_by_email(admin_email):
        admin_manager.create_admin(
            admin_username, admin_email, admin_password, is_super_admin=True
        )


def create_app():

    # dictConfig({
    #     'version': 1,
    #     'formatters': {'default': {
    #         'format': '[%(asctime)s] %(levelname)s : %(message)s',
    #     }},
    #     'handlers': {'wsgi': {
    #         'class': 'logging.StreamHandler',
    #         'stream': 'ext://flask.logging.wsgi_errors_stream',
    #         'formatter': 'default'
    #     }},
    #     'root': {
    #         'level': 'INFO',
    #         'handlers': ['wsgi']
    #     }
    # })

    # setting the logging level
    basicConfig()
    getLogger().setLevel("DEBUG")

    # schema for validation error response
    validation_error_schema = {
        "properties": {
            "error_detail": validation_error_detail_schema,
            "error_message": {"type": "string"},
            "status_code": {"type": "integer"},
        },
        "type": "object",
    }
    app = APIFlask(__name__)

    if is_in_staging_environment():
        app.config.from_object("config.StagingConfig")
    elif is_in_development_environment():
        app.config.from_object("config.DevelopmentConfig")
    else:
        app.config.from_object("config.DevelopmentConfig")

    # initialize the extensions
    cors.init_app(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)

    # security settings
    app.security_schemes = {  # equals to use config SECURITY_SCHEMES
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
        }
    }

    with app.app_context():
        # run the necessary migrations
        upgrade()
        create_super_admin_if_not_exists()

        # register errorhandlers
        app.register_error_handler(403, forbidden)
        app.register_error_handler(404, page_not_found)
        app.register_error_handler(405, method_not_allowed)
        app.register_error_handler(500, internal_server_error)

        # registering blueprints
        app.register_blueprint(main)
        app.register_blueprint(admin)
        app.register_blueprint(school)
        app.register_blueprint(staff)
        app.register_blueprint(student)
        app.register_blueprint(testr)
        app.register_blueprint(notification)
        app.register_blueprint(analytics)
        app.register_blueprint(subscription)
        app.register_blueprint(achievements)
        app.register_blueprint(qa, url_prefix='/api/qa')

        app.config["VALIDATION_ERROR_SCHEMA"] = validation_error_schema

        
        @app.errorhandler(BaseError)
        def handle_base_errors(error: BaseError):
            db.session.rollback()
            db.session.close()
            log_error(traceback.format_exc())
            """
            Handler for all errors in the API
            """
            error_as_dict = error.to_dict()
            # so that we can see the error in the app engine logs
            return error_as_dict, error.error_code

        @app.errorhandler(ValidationError)
        def handle_validation_error(error: ValidationError):
            db.session.rollback()
            db.session.close()
            log_error(traceback.format_exc())
            return (
                jsonify(
                    {
                        "message": error.messages,
                        "data": error.data,
                    }
                ),
                422,
            )

        @app.errorhandler(IntegrityError)
        def handle_integrity_error(error: IntegrityError):
            db.session.rollback()
            db.session.close()
            log_error(traceback.format_exc())
            return jsonify({"error": str(error), "message": error._message()}), 500
        

        @app.errorhandler(Exception)
        def handle_exceptions(exception):
            db.session.rollback()
            db.session.close()
            log_error(traceback.format_exc())
            return (
                jsonify(
                    {
                        "error": str(exception),
                        "message": "Something went wrong! Our Developers are working on it!",
                    }
                ),
                500,
            )

        @app.before_request
        def log_request_body():
            if request.method != "GET" and request.method != "OPTIONS":
                log_info("Logging Request Body")
                log_info(request.get_json())

        @app.teardown_appcontext
        def teardown_context(e):
            # db.session.commit()
            db.session.close()

    return app
