from functools import wraps
from typing import List

import jwt
from flask import current_app as app
from flask import request

from app._shared.api_errors import (unauthorized_request, permissioned_denied)
from app._shared.services import set_current_user


# we are going to have a wrapper to check tokens
def token_auth(user_types: List[str]):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            header = request.headers.get('Authorization')
            if not header:
                return unauthorized_request("No Authorization Present")
            
            bearer_token = header.split()[1]

            try:
                payload = jwt.decode(bearer_token, app.config['SECRET_KEY'],  algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return unauthorized_request('Token has expired')
            except jwt.InvalidTokenError:
                return unauthorized_request('Invalid Token')
            
            if payload['user_type'] not in user_types:
                return permissioned_denied()
            
            set_current_user(**payload)
            return func(*args, **kwargs)
        return wrapper
    return decorator