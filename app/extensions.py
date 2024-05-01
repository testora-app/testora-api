'''
This is a where all the extensions in use a placed
'''

from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
cors = CORS()
migrate = Migrate()
bcrypt = Bcrypt()