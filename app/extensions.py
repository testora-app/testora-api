"""
This is a where all the extensions in use a placed
"""

from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_admin import Admin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
cors = CORS()
migrate = Migrate()
bcrypt = Bcrypt()
admin = Admin()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])
