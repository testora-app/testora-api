import jwt
from functools import wraps
from flask import request, current_app as app

from app._shared.api_errors import PermissionDeniedError, AuthenticationFailedError
from app._shared.services import set_current_user

# we are going to have a wrapper to check tokens
def token_auth(user_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            header = request.headers.get('Authorization')
            if not header:
                raise AuthenticationFailedError()
            
            bearer_token = header.split()[1]

            try:
                payload = jwt.decode(bearer_token, app.config['SECRET_KEY'],  algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                raise AuthenticationFailedError('Token has expired')
            except jwt.InvalidTokenError:
                raise AuthenticationFailedError('Invalid Token')
            
            if payload['user_type'] != user_type:
                raise PermissionDeniedError()
            
            set_current_user(**payload)
        return wrapper
    return decorator