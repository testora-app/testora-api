from apiflask import APIBlueprint

from app._shared.schemas import UserTypes
from app._shared.api_errors import success_response
from app._shared.decorators import token_auth

from app.school.schemas import GetSchoolListSchema
from app.school.operations import school_manager

school = APIBlueprint('school', __name__)


@school.get('/schools/')
@school.output(GetSchoolListSchema)
@token_auth([UserTypes.admin])
def get_schools():
    schools = school_manager.get_schools()
    return success_response(data=[school.to_json() for school in schools])



