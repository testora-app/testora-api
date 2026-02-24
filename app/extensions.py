"""
This is a where all the extensions in use are placed
"""

from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_admin import Admin

db = SQLAlchemy()
cors = CORS()
migrate = Migrate()
bcrypt = Bcrypt()
admin = Admin()
