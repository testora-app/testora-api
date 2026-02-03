from functools import wraps
from typing import List

import jwt
from flask import current_app as app
from flask import request
from sqlalchemy import func

from app._shared.api_errors import unauthorized_request, permissioned_denied
from app._shared.services import set_current_user, get_current_user
from app._shared.schemas import UserTypes
from threading import Thread
import os


def require_params_by_usertype(param_rules):
    """
    param_rules: dict mapping user_type -> list of required params
    Example:
    {
        "admin": ["school_id", "term_id"],
        "teacher": ["class_id", "subject_id"],
        "student": ["student_id"]
    }
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Example: Get user_type from query param or header
            user_type = get_current_user()["user_type"]

            if not user_type:
                return permissioned_denied("Missing user type")

            required_params = param_rules.get(user_type)
            if not required_params:
                return f(*args, **kwargs)

            missing = [p for p in required_params if p not in request.args]
            if missing:
                return permissioned_denied(f"Missing query parameters for {user_type}")

            return f(*args, **kwargs)

        return wrapper

    return decorator


def can_access_info():
    user = get_current_user()
    student_id = request.view_args.get("student_id")
    batch_id = request.args.get("batch_id")

    if not student_id or not batch_id:
        return True

    if user["user_type"] in [UserTypes.admin, UserTypes.school_admin, UserTypes.staff]:
        if student_id:
            from app.student.operations import student_manager
            student = student_manager.get_student_by_id(student_id)
            if student and student.school_id == user["school_id"]:
                return True
        elif batch_id:
            from app.student.operations import BatchManager
            batch = BatchManager().get_batch_by_id(batch_id)
            if batch and batch.school_id == user["school_id"]:
                return True
        else:
            return True
        
    else:
        if student_id and student_id == user["user_id"]:
            return True
    return False


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

            access_granted = can_access_info()
            if not access_granted:
                return permissioned_denied("You do not have permission to access this resource.")
            return func(*args, **kwargs)

        return wrapper

    return decorator

def public_protected(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization")
        if not header:
            return unauthorized_request("No Authorization Present")

        user_token = header.split()[1]

        try:
            app_token = os.getenv("APP_ACCESS_TOKEN")
            if app_token != user_token:
                return unauthorized_request("Invalid App Access Token")
        except jwt.ExpiredSignatureError:
            return unauthorized_request("Token has expired")
        except jwt.InvalidTokenError:
            return unauthorized_request("Invalid Token")

        return func(*args, **kwargs)

    return wrapper


def premium_feature(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user and "premium" in user["school_package"]:
            return func(*args, **kwargs)
        return permissioned_denied(
            "You need a premium subscription to access this feature."
        )

    return wrapper


def async_method(f):
    def wrapper(*args, **kwargs):
        current_app = app._get_current_object()
        def inner():
            with current_app.app_context():  # Ensure Flask context is available
                try:
                    f(*args, **kwargs)
                except Exception as e:
                    # Handle exceptions that occur in the thread
                    print(f"Error in async method: {e}")

        thr = Thread(target=inner)
        thr.start()
        return thr  # Optionally return the thread object if you need to join it or track it

    return wrapper
