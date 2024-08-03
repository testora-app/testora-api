from typing import Dict
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse as date_parser
from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, UserTypes, LoginSchema, CurriculumTypes
from app._shared.api_errors import response_builder, unauthorized_request, success_response, not_found, bad_request, unapproved_account
from app._shared.decorators import token_auth
from app._shared.services import check_password, generate_access_token, get_current_user

from app.student.schemas import StudentRegister, ApproveStudentSchema, GetStudentListSchema, BatchListSchema, Responses, Requests
from app.student.operations import student_manager, batch_manager
from app.analytics.operations import ssm_manager

from app.school.operations import school_manager

student = APIBlueprint('student', __name__)


#region STUDENTS
@student.post("/students/register/")
@student.input(StudentRegister)
@student.output(SuccessMessage, 201)
def student_register(json_data: Dict):
    existing_student = student_manager.get_student_by_email(json_data["email"].strip())
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
    student = student_manager.get_student_by_email(json_data["email"].strip())

    if student and not student.is_approved:
        return unapproved_account()

    if student and check_password(student.password_hash, json_data["password"]):
        access_token = generate_access_token(student.id, UserTypes.student, student.school_id)
        school = school_manager.get_school_by_id(student.id)
        school_data = school.to_json()
        school_data.pop("code")


        # handle streak
        current_login_time = datetime.now(timezone.utc)
        if student.last_login and current_login_time.date().day - student.last_login.date().day == 1:
            student.current_streak += 1
            student.highest_streak = student.current_streak if student.current_streak > student.highest_streak else student.highest_streak
            #TODO: send them a message of increase of streak
        else:
            # this is their first time or they lost the streak
            student.last_login = current_login_time
            student.current_streak = 1
            student.highest_streak = 1

            #TODO: if they lost streak send them a message

        student.last_login = current_login_time
        student.save()

        # handle session
        current_session = ssm_manager.select_student_session_history(student.id, current_login_time.date())
        if not current_session:
            ssm_manager.add_new_student_session(student.id, current_login_time.date())

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
    student_data = [st.to_json() for st in student] if student else []
    return success_response(data=student_data)


@student.get("/students/<int:student_id>/")
@student.output(Responses.StudentSchema)
@token_auth()
def get_student_details(student_id):
    student = student_manager.get_student_by_id(student_id)
    if student:
        return success_response(data=student.to_json())
    return not_found("Student does not exist!")


@student.post("/students/end-session/")
@student.input(Requests.EndSessionSchema)
@student.output(SuccessMessage)
def end_student_session(json_data):
    data = json_data["data"]
    date_parsed = date_parser(data['date']).date() if type(data['date']) != datetime else data['date'].date()
    session = ssm_manager.select_student_session_history(data['student_id'], date=date_parsed)
    
    if session:
        session.end_time = session.created_at + timedelta(seconds=data['duration'])
        session.duration = data['duration']
        session.save()
    return success_response()


#endregion STUDENTS


#region BATCH
@student.post("/batches/")
@student.input(Requests.CreateBatchSchema)
@student.output(Responses.BatchSchema)
@token_auth([UserTypes.school_admin])
def create_batch(json_data):
    school_id = get_current_user()["school_id"]
    data = json_data["data"]

    if data['curriculum'] not in CurriculumTypes.get_curriculum_types():
        raise bad_request(f"{data['curriculum']} is not a valid curriculum: {CurriculumTypes.get_curriculum_types()}")
    
    new_batch = batch_manager.create_batch(**data, school_id=school_id)
    return success_response(data=new_batch.to_json())



@student.put("/batches/<int:batch_id>/")
@student.input(Requests.CreateBatchSchema)
@student.output(Responses.BatchSchema)
@token_auth([UserTypes.school_admin])
def edit_batch(batch_id, json_data):
    batch = batch_manager.get_batch_by_id(batch_id)
    data = json_data["data"]
    if batch:
        batch.batch_name = data["batch_name"]
        batch.curriculum = data["curriculum"]
        batch.students = [student for student in student_manager.get_students_by_ids(data["students"])]
        batch.save()
    
    return success_response(data=batch.to_json())



@student.get("/batches/")
@student.output(BatchListSchema)
@token_auth([UserTypes.school_admin, UserTypes.admin])
def get_batches():
    school_id = get_current_user()["school_id"]

    if school_id:
        batches = batch_manager.get_batches_by_school_id(school_id)
    else:
        batches = batch_manager.get_all_batches()

    batches = [batch.to_json() for batch in batches] if batches else []
    return success_response(data=batches)

#endregion BATCH