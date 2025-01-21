from functools import wraps
from typing import List

import jwt
from flask import current_app as app
from flask import request

from app._shared.api_errors import unauthorized_request, permissioned_denied
from app._shared.services import set_current_user, get_current_user
from threading import Thread


# we are going to have a wrapper to check tokens
def token_auth(user_types: List[str] = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization")
            if not header:
                return unauthorized_request("No Authorization Present")

            bearer_token = header.split()[1]

            try:
                payload = jwt.decode(
                    bearer_token, app.config["SECRET_KEY"], algorithms=["HS256"]
                )
            except jwt.ExpiredSignatureError:
                return unauthorized_request("Token has expired")
            except jwt.InvalidTokenError:
                return unauthorized_request("Invalid Token")

            if "*" not in user_types and (
                user_types and payload["user_type"] not in user_types
            ):
                return permissioned_denied()

            if payload["is_school_suspended"]:
                return permissioned_denied(
                    "Your school account has been suspended. Please contact your school admin."
                )

            set_current_user(**payload)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def premium_feature():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user and user["school_package"] == "premium":
                return func(*args, **kwargs)
            return permissioned_denied(
                "You need a premium subscription to access this feature."
            )

        return wrapper

    return decorator


def async_method(f):
    def wrapper(*args, **kwargs):
        def inner():
            with app.app_context():  # Ensure Flask context is available
                try:
                    f(*args, **kwargs)
                except Exception as e:
                    # Handle exceptions that occur in the thread
                    app.logger.error(f"Error in async method: {e}")

        thr = Thread(target=inner)
        thr.start()
        return thr  # Optionally return the thread object if you need to join it or track it

    return wrapper
