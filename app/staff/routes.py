from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, UserTypes, Login as LoginSchema
from app._shared.api_errors import error_response, unauthorized_request, success_response, not_found, bad_request
from app._shared.decorators import token_auth
from app._shared.services import check_password, generate_access_token

from app.staff.schemas import SchoolAdminRegister, StaffRegister, VerifiedStaffSchema
from app.staff.operations import staff_manager

from app.school.operations import school_manager

staff = APIBlueprint('staff', __name__)


@staff.post("/school-admin/register/")
@staff.input(SchoolAdminRegister)
@staff.output(SuccessMessage, 201)
def register_school_admin(json_data):
    new_school = school_manager.create_school(**json_data["school"])
    json_data["staff"].pop('school_code')
    staff_manager.create_staff(**json_data["staff"], is_admin=True, school_id=new_school.id, is_approved=True)
    return success_response()


@staff.post("/staff/register/")
@staff.input(StaffRegister, 201)
@staff.output(SuccessMessage)
def register_staff(json_data):
    existing = staff_manager.get_staff_by_email(json_data["email"])
    if existing:
        return bad_request("User with the email already exists!")

    code = json_data.pop("school_code")
    school = school_manager.get_school_by_code(code)
    if school:
        staff_manager.create_staff(**json_data, is_admin=False, school_id=school.id)
        return success_response()
    return unauthorized_request("Invalid School Code")


@staff.post("/staff/authenticate/")
@staff.input(LoginSchema)
@staff.output(VerifiedStaffSchema)
def login(json_data):
    staff = staff_manager.get_staff_by_email(json_data["email"])

    if staff and check_password(staff.password_hash, json_data["password"]):
        user_type = UserTypes.school_admin if staff.is_admin else UserTypes.staff
        access_token = generate_access_token(staff.id, user_type=user_type, school_id=staff.school_id)
        return success_response(data={'staff': staff.to_json(), 'auth_token': access_token})
    
    return unauthorized_request("Invalid Login")


# an endpoint to verify the staff