from typing import Dict
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse as date_parser
from apiflask import APIBlueprint
from flask import render_template
import pytz
from logging import error as log_error, info as log_info

from app._shared.schemas import SuccessMessage, UserTypes, LoginSchema, CurriculumTypes
from app._shared.api_errors import (
    response_builder,
    unauthorized_request,
    success_response,
    not_found,
    bad_request,
    unapproved_account,
    permissioned_denied
)
from app._shared.decorators import token_auth
from app._shared.services import check_password, generate_access_token, get_current_user

from app.student.schemas import (
    StudentRegister,
    ApproveStudentSchema,
    GetStudentListSchema,
    BatchListSchema,
    Responses,
    Requests,
    StudentQuerySchema,
    StudentAveragesQuerySchema,
)
from app.student.operations import student_manager, batch_manager, stusublvl_manager
from app.student.services import (
    transform_data_for_averages,
    add_batch_to_student_data,
    sort_results,
)
from app.analytics.operations import ssm_manager
from app.subscriptions.constants import SubscriptionLimits, Features

from app.school.operations import school_manager
from app.staff.operations import staff_manager
from app.app_admin.operations import subject_manager
from app.test.operations import test_manager
from app.notifications.operations import recipient_manager

from app.integrations.pusher import pusher
from app.integrations.mailer import mailer
import os


student = APIBlueprint("student", __name__)


# region STUDENTS
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
        school = school_manager.get_school_by_id(student.school_id)

        if school.is_suspended:
            return permissioned_denied("Your institution's account is suspended. Please contact  your school administrator or support.")

        access_token = generate_access_token(
            student.id,
            UserTypes.student,
            student.email,
            student.school_id,
            is_school_suspended=school.is_suspended,
            school_package=school.subscription_package,
        )

        school_data = school.to_json()
        school_data.pop("code")
        
        student_json = student.to_json()
        student_json["tests_completed"] = len(test_manager.get_tests_by_student_ids([student.id]))

        # Generate weekly goals on first login of the week
        week_start_date = None
        try:
            from app.goals.services import GenerateGoalsService, find_active_week_start
            from app.goals.operations import (
                calculate_subject_averages,
                calculate_max_streak_30d,
                select_subjects_for_goals,
                get_weekly_wins_message
            )
            
            # Get current date in Africa/Accra timezone
            accra_tz = pytz.timezone('Africa/Accra')
            current_date = datetime.now(accra_tz).date()
            
            # Calculate subject averages from last 5 tests
            subjects_data = calculate_subject_averages(student.id)
            
            if subjects_data:
                # Select subjects for goals (handles random selection if needed)
                selected_subjects = select_subjects_for_goals(subjects_data)
                
                # Calculate max streak in last 30 days
                max_streak_30d = calculate_max_streak_30d(student.id, current_date)
                
                # Generate weekly goals
                goal_service = GenerateGoalsService()
                goal_result = goal_service.run(
                    student_id=student.id,
                    login_date=current_date,
                    subjects=selected_subjects,
                    student_max_streak_30d=max_streak_30d
                )
                
                if goal_result.get("skipped"):
                    log_info(f"Weekly goals skipped for student {student.id}: {goal_result.get('reason')}")
                    # Get the existing week start date
                    week_start_date = find_active_week_start(student.id, current_date)
                else:
                    log_info(f"Weekly goals generated for student {student.id}: {goal_result.get('summary')}")
                    # Use the newly created week start date
                    week_start_date = current_date
            else:
                log_info(f"No subjects found for student {student.id}, skipping goal generation")
                
        except Exception as e:
            # Log error but don't fail the login
            log_error(f"Error generating weekly goals for student {student.id}: {str(e)}")
        
        # Check for weekly wins (achieved goals from last week)
        if week_start_date:
            try:
                from app.goals.operations import get_weekly_wins_message

                weekly_wins = get_weekly_wins_message(student.id, week_start_date, week_offset=-1)

                if weekly_wins["has_wins"]:
                    student_json["weekly_wins"] = weekly_wins
                    log_info(f"Weekly wins found for student {student.id}: {len(weekly_wins['achievements'])} achievements")

            except Exception as e:
                # Log error but don't fail the login
                log_error(f"Error generating weekly wins message for student {student.id}: {str(e)}")

        return success_response(
            data={
                "user": student_json,
                "auth_token": access_token,
                "school": school_data,
                "user_type": UserTypes.student,
            }
        )

    return unauthorized_request("Invalid Login")


@student.post("/students/approve/")
@student.output(SuccessMessage)
@student.input(ApproveStudentSchema)
@token_auth([UserTypes.school_admin])
def approve_student(json_data):
    # do a prior check here to see if there's a limit hihi
    school_id = get_current_user()["school_id"]
    school = school_manager.get_school_by_id(school_id)
    student_number = len(student_manager.get_active_students_by_school(school_id))

    if (
        student_number
        >= SubscriptionLimits.get_limits(school.subscription_package)[
            Features.StudentLimit
        ]
    ):
        return bad_request("You have reached your student limit!")

    for student_id in json_data["student_ids"]:
        student = student_manager.get_student_by_id(student_id)
        if student:
            student.is_approved = True
            student.save()

            context = {
                "student_name": student.first_name,
                "school_name": school.name,
                "guide_link": os.getenv("FRONTEND_URL", "https://preppee.online") + "/docs/student-guide",
                "login_url": os.getenv("FRONTEND_URL", "https://preppee.online") + "/login",
                "phone_number": "+233 24 142 3514",
            }
            html = mailer.generate_email_text("student_signup.html", context)
            mailer.send_email(
                [student.email],
                "You're In- Let's Get You Exam Ready With Preppee",
                html,
                html=html,
            )
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
@student.input(Requests.StudentQueryParams, location="query")
@student.output(GetStudentListSchema)
@token_auth([UserTypes.school_admin])
def get_student_list(query_data):
    school_id = get_current_user()["school_id"]
    pending_students = query_data.get("pending", None)
    pending_only = True if pending_students == "true" else False
    no_batch = query_data.get("no_batch", None)
    no_batch_only = True if no_batch == "true" else False

    if query_data.get("batch_id", None) is not None:
        batch = batch_manager.get_batch_by_id(query_data["batch_id"])
        if batch:
            students = batch.to_json(include_students=True).get("students", [])
            return success_response(data=students)
        
    student = student_manager.get_student_by_school(school_id, pending_only=pending_only)
    

    if no_batch_only:
        student_data = [st.to_json(include_batch=True) for st in student] if student else []
        student_data = [st for st in student_data if len(st.get("batches", [])) == 0]
    else:
        student_data = [st.to_json() for st in student] if student else []
    return success_response(data=student_data)


@student.get("/students/<int:student_id>/")
@student.output(Responses.StudentSchema)
@token_auth(["*"])
def get_student_details(student_id):
    student = student_manager.get_student_by_id(student_id)
    if student:
        return success_response(data=student.to_json())
    return not_found("Student does not exist!")


@student.put("/students/<int:student_id>/")
@student.input(Requests.UpdateStudentSchema)
@student.output(Responses.StudentSchema)
@token_auth([UserTypes.school_admin, UserTypes.staff])
def update_student(student_id, json_data):
    student = student_manager.get_student_by_id(student_id)
    if not student:
        return not_found("Student does not exist!")
    
    data = json_data.get("data", json_data)
    
    # Update basic student fields
    if "first_name" in data:
        student.first_name = data["first_name"]
    if "surname" in data:
        student.surname = data["surname"]
    if "email" in data:
        student.email = data["email"]
    if "other_names" in data:
        student.other_names = data["other_names"]
    if "gender" in data:
        student.gender = data["gender"]
    
    # Update batch assignments if provided (max 1 batch)
    if "batch_ids" in data and data["batch_ids"] is not None:
        batch_ids = data["batch_ids"]
        if batch_ids and len(batch_ids) > 1:
            return bad_request("Only one batch can be assigned to a student.")
        batches = batch_manager.get_batches_by_ids(batch_ids) if batch_ids else []
        student.batches = batches
    
    student.save()
    return success_response(data=student.to_json())


@student.post("/students/end-session/")
@student.input(Requests.EndSessionSchema)
@student.output(SuccessMessage)
@token_auth(["*"])
def end_student_session(json_data):
    json_data = json_data["data"]

    current_user_type = get_current_user()["user_type"]
    if current_user_type == UserTypes.student:
        for data in json_data:
            session = ssm_manager.select_student_session_history(
                data["student_id"], date=data["date"]
            )

            if session:
                session.end_time = session.created_at + timedelta(seconds=data["duration"] / 1000)
                session.duration = data["duration"] / 1000
                session.save()
            else:
                ssm_manager.add_new_student_session(data["student_id"], data["date"], data["duration"] / 1000)
    return success_response()


# endregion STUDENTS


# region BATCH
@student.post("/batches/")
@student.input(Requests.CreateBatchSchema)
@student.output(Responses.BatchSchema)
@token_auth([UserTypes.school_admin])
def create_batch(json_data):
    school_id = get_current_user()["school_id"]
    data = json_data["data"]
    staff_ids = data.pop("staff")

    if data["curriculum"] not in CurriculumTypes.get_curriculum_types():
        raise bad_request(
            f"{data['curriculum']} is not a valid curriculum: {CurriculumTypes.get_curriculum_types()}"
        )

    new_batch = batch_manager.create_batch(**data, school_id=school_id)
    if staff_ids:
        new_batch.staff = [
            staff_id for staff_id in staff_manager.get_staff_by_ids(staff_ids)
        ]
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
        batch.students = [
            student for student in student_manager.get_students_by_ids(data["students"])
        ]
        batch.staff = [staff for staff in staff_manager.get_staff_by_ids(data["staff"])]
        batch.save()

    return success_response(data=batch.to_json())


@student.get("/batches/")
@student.output(BatchListSchema)
@token_auth([UserTypes.admin, UserTypes.school_admin, UserTypes.staff, UserTypes.student])
def get_batches():
    current_user = get_current_user()
    school_id = current_user["school_id"]
    user_type = current_user["user_type"]

    # Get all batches for the school (or all if admin)
    if school_id:
        all_batches = batch_manager.get_batches_by_school_id(school_id)
    else:
        all_batches = batch_manager.get_all_batches()

    # Filter batches based on user type
    if user_type == UserTypes.student:
        # Students only see batches they belong to
        student = student_manager.get_student_by_id(current_user["user_id"])
        if student:
            user_batch_ids = {batch.id for batch in student.batches}
            batches = [batch for batch in all_batches if batch.id in user_batch_ids]
        else:
            batches = []
    elif user_type == UserTypes.staff:
        # Staff only see batches they belong to
        staff = staff_manager.get_staff_by_id(current_user["user_id"])
        if staff:
            user_batch_ids = {batch.id for batch in staff.batches}
            batches = [batch for batch in all_batches if batch.id in user_batch_ids]
        else:
            batches = []
    else:
        # Admins see all batches
        batches = all_batches

    batches = (
        [batch.to_json(include_students=True) for batch in batches] if batches else []
    )

    for batch in batches:
        batch_subjects = subject_manager.get_subject_by_curriculum(batch["curriculum"])
        batch["subjects"] = [{
            "id": subject.id,
            "name": subject.name,
            "short_name": subject.short_name
        } for subject in batch_subjects]

    return success_response(data=batches)


# endregion BATCH

#region LEVELS
@student.get("/students/subject-levels/")
@student.input(StudentQuerySchema, location="query")
@student.output(Responses.StudentSubjectLevelSchema)
@token_auth([UserTypes.student, UserTypes.staff, UserTypes.school_admin])
def student_subject_levels(query_data):
    current_user = get_current_user()

    if current_user["user_type"] == UserTypes.student:
        student_id = current_user["user_id"]
    else:
        try:
            student_id = query_data["student_id"]        
        except:
            return bad_request("'student_id' is required query param")
        

    subject_levels = stusublvl_manager.get_student_subject_level(student_id)

    response = []

    for subject_level in subject_levels:
        response.append({
            "subject_name": subject_manager.get_subject_by_id(subject_level.subject_id).name,
            "level": subject_level.level
        })

    return success_response(data=response)
# endregion LEVELS


# region ANALYTICS

@student.get("/students/dashboard/total-tests/")
@student.input(StudentQuerySchema, location="query")
@student.output(Responses.TotalTestsSchema)
@token_auth([UserTypes.student, UserTypes.staff, UserTypes.school_admin])
def total_tests(query_data):
    current_user = get_current_user()

    if current_user["user_type"] == UserTypes.student:
        student_id = current_user["user_id"]
    else:
        try:
            student_id = query_data["student_id"]
        except:
            return bad_request("'student_id' is required query param")
    total_completed = test_manager.get_tests_by_student_ids([student_id])
    return success_response(data={"tests_completed": len(total_completed)})


@student.get("/students/dashboard/line-chart/")
@student.input(StudentQuerySchema, location="query")
@student.output(Responses.LineChartSchema)
@token_auth([UserTypes.student, UserTypes.staff, UserTypes.school_admin])
def line_chart(query_data):
    """
    Gets the line chart data for a student's dashboard, given the student's id.
    :return: A list of dictionaries containing the subject name and a list of scores from recent tests (max 7).
    """
    current_user = get_current_user()

    if current_user["user_type"] == UserTypes.student:
        student_id = current_user["user_id"]
    else:
        try:
            student_id = query_data["student_id"]
        except:
            return bad_request("'student_id' is required query param")

    line_data = []

    student = student_manager.get_student_by_id(student_id)
    subjects = []

    for batch in student.batches:
        subjects += subject_manager.get_subject_by_curriculum(batch.curriculum)

    subject_scored = []
    for subject in subjects:
        if subject.short_name not in subject_scored:
            recent_tests = test_manager.get_student_recent_tests(
                student.id, subject_id=subject.id, limit=7
            )
            data = {"subject": subject.short_name}
            count = 0
            for test in recent_tests:
                count += 1
                data["score" + str(count)] = test.score_acquired

            line_data.append(data)

            subject_scored.append(subject.short_name)

    return success_response(data=line_data)


@student.get("/students/dashboard/pie-chart/")
@student.input(StudentQuerySchema, location="query")
@student.output(Responses.PieChartSchema)
@token_auth([UserTypes.student, UserTypes.staff, UserTypes.school_admin])
def pie_chart(query_data):
    current_user = get_current_user()

    if current_user["user_type"] == UserTypes.student:
        student_id = current_user["user_id"]
    else:
        try:
            student_id = query_data["student_id"]
        except:
            return bad_request("'student_id' is required query param")

    pie_data = []

    student = student_manager.get_student_by_id(student_id)
    subjects = []

    for batch in student.batches:
        subjects += subject_manager.get_subject_by_curriculum(batch.curriculum)

    subject_scored = []
    for subject in subjects:
        if subject.short_name not in subject_scored:
            tests_taken = test_manager.get_tests_by_subject_and_student(
                student.id, subject.id
            )
            percent_average = (
                round(
                    sum([test.score_acquired for test in tests_taken])
                    / len(tests_taken),
                    1,
                )
                if len(tests_taken) > 0
                else 0.0
            )

            pie_data.append(
                {
                    "subject": subject.short_name,
                    "tests_taken": len(tests_taken),
                    "percent_average": percent_average,
                }
            )
            subject_scored.append(subject.short_name)
    return success_response(data=pie_data)


@student.get("/students/dashboard/bar-chart/")
@student.input(StudentQuerySchema, location="query")
@student.output(Responses.BarChartSchema)
@token_auth([UserTypes.student, UserTypes.staff, UserTypes.school_admin])
def bar_chart(query_data):
    current_user = get_current_user()

    if current_user["user_type"] == UserTypes.student:
        student_id = current_user["user_id"]
    else:
        try:
            student_id = query_data["student_id"]
        except:
            return bad_request("'student_id' is required query param")

    bar_data = []

    student = student_manager.get_student_by_id(student_id)
    subjects = []

    for batch in student.batches:
        subjects += subject_manager.get_subject_by_curriculum(batch.curriculum)

    subject_scored = []

    for subject in subjects:
        if subject.short_name not in subject_scored:
            tests = test_manager.get_tests_by_subject_and_student(
                student.id, subject.id
            )

            new_score = tests[0].score_acquired if len(tests) > 0 else 0.0
            average_score = (
                round(sum([test.score_acquired for test in tests]) / len(tests), 1)
                if len(tests) > 0
                else 0.0
            )

            bar_data.append(
                {
                    "subject": subject.short_name,
                    "new_score": new_score,
                    "average_score": average_score,
                }
            )
            subject_scored.append(subject.short_name)

    return success_response(data=bar_data)


@student.get("/students/averages/")
@student.input(StudentAveragesQuerySchema, location="query")
@student.output(Responses.StudentAverageSchema, 200)
@token_auth(
    [UserTypes.school_admin, UserTypes.staff, UserTypes.student]
)  # TODO: update to allow for students and staff
def student_averages(query_data):
    school_id = get_current_user()["school_id"]
    subject_id = query_data.get("subject_id", None)

    if subject_id:
        subject_name = subject_manager.get_subject_by_id(subject_id).short_name
    else:
        subject_name = "All Subjects"

    # fetch one or all students
    if query_data.get("student_id", None) is not None:
        student_data = [
            student_manager.get_student_by_id(query_data["student_id"]).to_json(
                include_batch=True
            )
        ]
    else:
        if query_data.get("batch_id", None) is not None:
            batch_data = batch_manager.get_batch_by_id(query_data["batch_id"])
            if batch_data:
                batch_data = batch_data.to_json(include_students=True)
                student_data = [student for student in batch_data["students"]]
                student_data = add_batch_to_student_data(
                    student_data, batch_data["batch_name"]
                )
            else:
                return bad_request(
                    f"Batch with ID:{query_data['batch_id']} does not exist!"
                )
        else:
            student_data = [
                student.to_json()
                for student in student_manager.get_active_students_by_school(school_id)
            ]

    student_ids = [student["id"] for student in student_data]
    student_data = {student["id"]: student for student in student_data}

    students_tests = test_manager.get_tests_by_student_ids(
        student_ids, subject_id=subject_id
    )
    students_tests = [test.to_json() for test in students_tests]

    results = transform_data_for_averages(
        student_data, students_tests, subject_name=subject_name
    )

    # apply performance filters if any
    performance_filter = query_data.get("performance_filter", None)
    if performance_filter:
        results = sort_results(results, performance_filter)

    # apply num limit if any
    num_limit = query_data.get("num_limit", None)
    if num_limit:
        results = results[:num_limit]

    return success_response(data=results)


# endregion ANALYTICS
