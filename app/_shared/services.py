import datetime
import random
import os
import jwt
from flask import current_app as app, g
from flask import render_template

from globals import FRONTEND_BASE_URL

from app.extensions import bcrypt
from app.integrations.mailer import mailer
from app._shared.api_errors import AuthenticationFailedError


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




def generate_and_send_reset_password_email(user_id, user_type, user_email, school_id,  name, email):
    payload_data = {
        'user_id': user_id,
        'user_type': user_type,
        'user_email': user_email,
        'school_id': school_id,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=0, seconds=3600),
        'iat': datetime.datetime.now(datetime.timezone.utc)
    }
    reset_code = FRONTEND_BASE_URL + '/change-password/?confirmationCode=' + jwt.encode(
        payload=payload_data,
        key=app.config['SECRET_KEY']
    )

    html_body = render_template('html_reset_password.html', reset_code=reset_code, name=name)
    text_body = render_template('text_reset_password.txt', reset_code=reset_code, name=name)

    if is_in_development_environment() or is_in_staging_environment():
        print(text_body)

    mailer.send_email(
        [email],
        'Password Reset',
        text_body,
        html= html_body
    )


def generate_access_token(user_id, user_type, user_email, school_id=None, permissions=None):
    payload_data = {
        'user_id': user_id,
        'user_type': user_type,
        'user_email': user_email,
        'permissions': permissions,
        'school_id': school_id,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=0, seconds=7200),
        'iat': datetime.datetime.now(datetime.timezone.utc)
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



#TODO: change this to an auth user object, so you can just get the properties without worrying about dicts breaking.
# and then we can use type hinting

def set_current_user(user_type='admin', user_id=-1, user_email=None, school_id=-1, **kwargs):
    """ Set the currently logged in user for a session """
    user_data = {'user_id': user_id, 'user_type':user_type, 'user_email': user_email, 
                 'school_id': school_id, 'permissions': kwargs.get('permissions', None)}
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
