from flask import Flask
from .extensions import *

#importing the routes
from .routes import main
from app.app_admin.routes import app_admin
from app.school.routes import school
from app.staff.routes import staff
from app.student.routes import student
from app.test.routes import testr
from app.notifications.routes import notification
from app.analytics.routes import analytics
from app.subscriptions.routes import subscription
from app.achievements.routes import achievements


load_dotenv()


def create_super_admin_if_not_exists():
    import os

    from app.app_admin.operations import admin_manager

    admin_email, admin_username, admin_password = (
        os.getenv("ADMIN_EMAIL"),
        os.getenv("ADMIN_USERNAME"),
        os.getenv("ADMIN_PASSWORD"),
    )

    if admin_email and not admin_manager.get_admin_by_email(admin_email):
        admin_manager.create_admin(
            admin_username, admin_email, admin_password, is_super_admin=True
        )


def run_migrations_once():
    # Any consistent lock key (bigint). Keep it constant for this app.
    lock_key = 987654321  

    db.session.execute(text("SELECT pg_advisory_lock(:k)"), {"k": lock_key})
# try:
    upgrade()
    # except Exception as e:
    #     log_error(f"Error during migrations: {e}")
    #     print(f"Error during migrations: {e}")
    # finally:
    db.session.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": lock_key})
    db.session.commit()

def create_app():
    app = Flask(__name__)

    app.config.from_object('config.DevelopmentConfig')

    #initialize the extensions

    #registering blueprints
    app.register_blueprint(main)


    return app