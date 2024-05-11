from typing import Dict

from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, UserTypes,LoginSchema
from app._shared.api_errors import error_response, unauthorized_request, success_response, not_found, bad_request, unapproved_account
from app._shared.decorators import token_auth
from app._shared.services import check_password, generate_access_token, get_current_user

from app.student.schemas import StudentRegister, ApproveStudentSchema, GetStudentListSchema, Responses
from app.student.operations import student_manager

from app.school.operations import school_manager

student = APIBlueprint('student', __name__)


@student.post("/students/register/")
@student.input(StudentRegister)
@student.output(SuccessMessage, 201)
def student_register(json_data: Dict):
    existing_student = student_manager.get_student_by_email(json_data["email"])
    if existing_student:
        return bad_request("Student with this email already exists!")
    
    school = school_manager.get_school_by_code(json_data.pop("school_code"))

    if school:
        student_manager.create_student(**json_data, school_id=school.id)
        return success_response()
    return bad_request("Invalid School Code")


@student.post("/students/authenticate/")
@student.input(LoginSchema)
@student.output(Responses.VerifiedStudentSchema)
def login(json_data):
    student = student_manager.get_student_by_email(json_data["email"])

    if student and not student.is_approved:
        return unapproved_account()

    if student and check_password(student.password_hash, json_data["password"]):
        access_token = generate_access_token(student.id, UserTypes.student, student.school_id)
        school = school_manager.get_school_by_id(student.id)
        school_data = school.to_json()
        school_data.pop("code")
        return success_response(data={'user': student.to_json(), 'auth_token': access_token, 'school': school_data, 'user_type': UserTypes.student})

    return unauthorized_request("Invalid Login")


@student.post("/students/approve/")
@student.output(SuccessMessage)
@student.input(ApproveStudentSchema)
@token_auth([UserTypes.school_admin])
def approve_student(json_data):
    for student_id in json_data["student_ids"]:
        student = student_manager.get_student_by_id(student_id)
        if student:
            student.is_approved = True
            student.save()
    return success_response()


@student.post("/students/unapprove/")
@student.output(SuccessMessage)
@student.input(ApproveStudentSchema)
@token_auth([UserTypes.school_admin])
def unapprove_student(json_data):
    for student_id in json_data["student_ids"]:
        student = student_manager.get_student_by_id(student_id)
        if student:
            student.is_approved = False
            student.save()
    return success_response()



@student.get("/students/")
@student.output(GetStudentListSchema)
@token_auth([UserTypes.school_admin])
def get_student_list():
    school_id = get_current_user()["school_id"]
    student = student_manager.get_student_by_school(school_id)
    return success_response(data=[st.to_json() for st in student])