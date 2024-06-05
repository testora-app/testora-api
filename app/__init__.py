import traceback
from logging import error as log_error
from logging import info as log_info
from logging.config import dictConfig

from apiflask import APIFlask, HTTPError
from apiflask.schemas import validation_error_detail_schema
from dotenv import load_dotenv
from flask import jsonify, request
from flask_migrate import upgrade
from marshmallow.exceptions import ValidationError

from app._shared.api_errors import BaseError
from app._shared.services import is_in_staging_environment, is_in_development_environment
from app.errorhandlers import (forbidden, internal_server_error,
                               method_not_allowed, page_not_found)
from app.extensions import cors, db, migrate

#importing the routes
from .routes import main
from app.admin.routes import admin
from app.school.routes import school
from app.staff.routes import staff
from app.student.routes import student
from app.test.routes import testr


load_dotenv()

def create_super_admin_if_not_exists():
    import os

    from app.admin.operations import admin_manager

    admin_email, admin_username, admin_password = os.getenv('ADMIN_EMAIL'), os.getenv('ADMIN_USERNAME'), os.getenv('ADMIN_PASSWORD')

    if admin_email and not admin_manager.get_admin_by_email(admin_email):
        admin_manager.create_admin(admin_username, admin_email, admin_password, is_super_admin=True)

def create_app():
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s : %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })

    # schema for validation error response
    validation_error_schema = {
        "properties": {
            "error_detail": validation_error_detail_schema,
            "error_message": {
                "type": "string"
            },
            "status_code": {
                "type": "integer"
            }
        },
        "type": "object"
    }
    app = APIFlask(__name__)

    if is_in_staging_environment():
        app.config.from_object('config.StagingConfig')
    elif is_in_development_environment():
        app.config.from_object('config.DevelopmentConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')

    #initialize the extensions
    cors.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    # security settings
    app.security_schemes = {  # equals to use config SECURITY_SCHEMES
        'ApiKeyAuth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
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

        #registering blueprints
        app.register_blueprint(main)
        app.register_blueprint(admin)
        app.register_blueprint(school)
        app.register_blueprint(staff)
        app.register_blueprint(student)
        app.register_blueprint(testr)

        app.config['VALIDATION_ERROR_SCHEMA'] = validation_error_schema

        @app.errorhandler(HTTPError)
        def handle_http_error(e):
            db.session.rollback()
            log_error(traceback.format_exc())
            return jsonify({
                "status_code": e.status_code,
                "message": e.message
            }), e.status_code, e.headers

        @app.errorhandler(BaseError)
        def handle_base_errors(error: BaseError):
            db.session.rollback()
            log_error(traceback.format_exc())
            '''
            Handler for all errors in the API
            '''
            error_as_dict = error.to_dict()
            # so that we can see the error in the app engine logs
            return error_as_dict.get_json(), 422
        
        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            log_error(traceback.format_exc())
            return jsonify({
                "message": error.message,
                "data": error.data,
            })
        
        @app.errorhandler(Exception)
        def handle_exceptions(exception):
            db.session.rollback()
            log_error(traceback.format_exc())
            return jsonify({
                'error': str(exception),
                'message': 'Something went wrong! Our Developers are workig on it!'
            })
                

        @app.before_request
        def log_request_body():
            if request.method != "GET" and request.method != "OPTIONS":
                log_info("Logging Request Body")
                log_info(request.get_json())


        @app.teardown_appcontext
        def teardown_context(e):
            db.session.commit()
            db.session.close()
        

    return app