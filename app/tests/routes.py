from typing import Dict

from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, UserTypes,LoginSchema
from app._shared.api_errors import error_response, unauthorized_request, success_response, not_found, bad_request, unapproved_account
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.tests.operations import question_manager, test_manager


testr = APIBlueprint('testr', __name__)



@testr.get("/questions/")
def get_questions():
    return success_response()