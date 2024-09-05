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
from app.admin.operations import subject_manager
from app.test.operations import test_manager

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
        access_token = generate_access_token(student.id, UserTypes.student, student.email, student.school_id)
        school = school_manager.get_school_by_id(student.school_id)
        school_data = school.to_json()
        school_data.pop("code")


        # handle streak
        current_login_time = datetime.now(timezone.utc)
        if student.last_login:
            # Calculate the difference in days between the current login and the last login
            days_difference = (current_login_time.date() - student.last_login.date()).days
            
            if days_difference == 1:
                # Logged in on the next day
                student.current_streak += 1
                student.highest_streak = max(student.current_streak, student.highest_streak)
                # TODO: send them a message of increase of streak
            else:
                # More than one day has passed, or same day login, reset streak
                student.current_streak = 1
        else:
            # First time login
            student.current_streak = 1
            student.highest_streak = 1

            #TODO: if they lost streak send them a message

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
    json_data = json_data["data"]

    for data in json_data:
        session = ssm_manager.select_student_session_history(data['student_id'], date=data['date'])
        
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


#region ANALYTICS
@student.get('/students/dashboard/total-tests/')
@student.output(Responses.TotalTestsSchema)
@token_auth([UserTypes.student])
def total_tests():
    student_id = get_current_user()['user_id']
    total_completed = test_manager.get_tests_by_student_ids([student_id])
    return success_response(data={'tests_completed': len(total_completed)})


@student.get('/students/dashboard/line-chart/')
@student.output(Responses.LineChartSchema)
@token_auth([UserTypes.student])
def line_chart():
    """
    Gets the line chart data for a student's dashboard, given the student's id.
    :return: A list of dictionaries containing the subject name and a list of scores from recent tests (max 7).
    """
    student_id = get_current_user()['user_id']

    line_data = []

    student = student_manager.get_student_by_id(student_id)
    subjects= []

    for batch in student.batches:
        subjects += subject_manager.get_subject_by_curriculum(batch.curriculum)

    for subject in subjects:
        recent_tests = test_manager.get_student_recent_tests(student.id, subject_id=subject.id, limit=7)
        data = {"subject": subject.short_name}
        count = 0
        for test in recent_tests:
            count +=1
            data["score" + str(count)] = test.score_acquired
        
        line_data.append(data)

    return success_response(data=line_data)

@student.get('/students/dashboard/pie-chart/')
@student.output(Responses.PieChartSchema)
@token_auth([UserTypes.student])
def pie_chart():
    student_id = get_current_user()['user_id']

    pie_data = []

    student = student_manager.get_student_by_id(student_id)
    subjects= []

    for batch in student.batches:
        subjects += subject_manager.get_subject_by_curriculum(batch.curriculum)

    for subject in subjects:
        tests_taken = test_manager.get_tests_by_subject_and_student(student.id, subject.id)
        percent_average = round(sum([test.score_acquired for test in tests_taken])/len(tests_taken), 1) if len(tests_taken) > 0 else 0.0

        pie_data.append({
            "subject": subject.short_name,
            "tests_taken": len(tests_taken),
            "percent_average": percent_average
        })
    return success_response(data=pie_data)


@student.get('/students/dashboard/bar-chart/')
@student.output(Responses.BarChartSchema)
@token_auth([UserTypes.student])
def bar_chart():
    student_id = get_current_user()['user_id']

    bar_data = []

    student = student_manager.get_student_by_id(student_id)
    subjects= []

    for batch in student.batches:
        subjects += subject_manager.get_subject_by_curriculum(batch.curriculum)

    for subject in subjects:
        tests = test_manager.get_tests_by_subject_and_student(student.id, subject.id)

        new_score = tests[0].score_acquired if len(tests) > 0 else 0.0
        average_score = round(sum([test.score_acquired for test in tests])/len(tests), 1) if len(tests) > 0 else 0.0

        bar_data.append({
            "subject": subject.short_name,
            "new_score": new_score,
            "average_score": average_score
        })

    return success_response(data=bar_data)

#endregion ANALYTICS