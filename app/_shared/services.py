import datetime
import os
import jwt
from flask import current_app as app, g
from app.extensions import bcrypt

from app._shared.api_errors import AuthenticationFailedError


def generate_access_token(user_id, user_type, school_id=None, permissions=None):
    payload_data = {
        'user_id': user_id,
        'user_type': user_type,
        'permissions': permissions,
        'school_id': school_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=7200),
        'iat': datetime.datetime.utcnow()
    }

    token = jwt.encode(
        payload=payload_data,
        key = app.config['SECRET_KEY']
    )
    return token


def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(hashed_password, password):
    return bcrypt.check_password_hash(hashed_password, password)



def is_in_development_environment():
    '''
    Return True if code is running in a development environment
    '''
    return os.getenv('ENVIRONMENT', 'naah').lower().startswith('dev')


def is_in_staging_environment():
    '''
    Return true if code is running in the staging environment
    '''
    return os.getenv('ENVIRONMENT', 'naah').lower().startswith('staging')



#TODO: change this to an auth user object, so you can just get the properties without worrying about dicts breaking.
# and then we can use type hinting

def set_current_user(user_type='admin', user_id=-1, school_id=-1, **kwargs):
    """ Set the currently logged in user for a session """
    user_data = {'user_id': user_id, 'user_type':user_type, 'school_id': school_id, 'permissions': kwargs.get('permissions', None)}
    if user_id == -1 or school_id == -1 and is_in_development_environment():
        print('Adding a user with negative school-id or user-id')
    user_data.update(kwargs)
    setattr(g, 'current_user_data', user_data)


def get_current_user():
    '''
    Get the currently logged in user.
    This AuthUser object would have been stored in the global g object of flask

    :returns (AuthUser): An instance of AuthUser that represents the currently logged in user

    :raises: :AuthenticationFailedError:, if no user data has been attached to the global g object
    '''
    try:
        user_data = getattr(g, 'current_user_data')
    except Exception as error:
        print(error)
        # no user data has been attached to g yet. This means no user has been authenticated for this session
        raise AuthenticationFailedError()
    return user_data
