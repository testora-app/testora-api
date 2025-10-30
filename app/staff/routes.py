from apiflask import APIBlueprint
from datetime import datetime

from app._shared.schemas import SuccessMessage, UserTypes, LoginSchema
from app._shared.api_errors import (
    response_builder,
    unauthorized_request,
    success_response,
    not_found,
    bad_request,
    unapproved_account,
)
from app._shared.decorators import token_auth
from app._shared.services import check_password, generate_access_token, get_current_user

from app.app_admin.operations import subject_manager
from app.staff.schemas import (
    SchoolAdminRegister,
    StaffRegister,
    ApproveStaffSchema,
    GetStaffListSchema,
    Responses,
)
from app.staff.operations import staff_manager
from app.subscriptions.constants import SubscriptionLimits, Features
from app.integrations.mailer import mailer


from app.school.operations import school_manager

staff = APIBlueprint("staff", __name__)


@staff.post("/school-admin/register/")
@staff.input(SchoolAdminRegister)
@staff.output(SuccessMessage, 201)
def register_school_admin(json_data):
    existing = staff_manager.get_staff_by_email(
        json_data["school_admin"]["email"].strip()
    )
    if existing:
        return bad_request("User with the email already exists!")

    new_school = school_manager.create_school(**json_data["school"])

    json_data["school_admin"].pop("school_code")
    school_admin = staff_manager.create_staff(
        **json_data["school_admin"],
        is_admin=True,
        school_id=new_school.id,
        is_approved=True
    )
    context = {
        "school_name": new_school.name,
        "institutional_code": new_school.code,
        "email": school_admin.email,
        "year": datetime.now().year,
        "guide_link": "https://testora-web.onrender.com",
        "login_url": "https://testora-web.onrender.com",
        "phone_number": "+233240126470",
    }
    html_body = mailer.generate_email_text("school_admin_signup.html", context)

    mailer.send_email(
        [school_admin.email],
        "Your School Is All Set For Preppee - Here's Your Access Code",
        html_body,
        html=html_body,
    )
    return success_response()


@staff.post("/staff/register/")
@staff.input(StaffRegister)
@staff.output(SuccessMessage, 201)
def register_staff(json_data):
    existing = staff_manager.get_staff_by_email(json_data["email"].strip())
    if existing:
        return bad_request("User with the email already exists!")

    code = json_data.pop("school_code")
    school = school_manager.get_school_by_code(code)
    if school:
        teacher = staff_manager.create_staff(
            **json_data, is_admin=False, school_id=school.id
        )

        context = {
            "school_name": school.name,
            "teacher_name": teacher.first_name,
            "guide_link": "https://testora-web.onrender.com",
            "login_url": "https://testora-web.onrender.com",
            "phone_number": "+233240126470",
        }

        html = mailer.generate_email_text("staff_signup.html", context)
        mailer.send_email(
            [teacher.email],
            "You're In!  Welcome to Your Preppee Classroom ",
            html,
            html=html,
        )
        return success_response()
    return unauthorized_request("Invalid School Code")


@staff.post("/staff/authenticate/")
@staff.input(LoginSchema)
@staff.output(Responses.VerifiedStaffSchema)
def login(json_data):
    from app.student.operations import batch_manager

    staff = staff_manager.get_staff_by_email(json_data["email"].strip())
    if staff and not staff.is_approved:
        return unapproved_account()

    if staff and check_password(staff.password_hash, json_data["password"]):
        school = school_manager.get_school_by_id(staff.school_id)

        user_type = UserTypes.school_admin if staff.is_admin else UserTypes.staff
        access_token = generate_access_token(
            staff.id,
            user_type,
            staff.email,
            school_id=staff.school_id,
            is_school_suspended=school.is_suspended,
            school_package=school.subscription_package,
        )

        school_data = school.to_json()
        if user_type == UserTypes.staff:
            school_data.pop("code")
    
        return success_response(
            data={
                "user": staff.to_json(include_batches=True),
                "auth_token": access_token,
                "school": school_data,
                "user_type": user_type
            }
        )

    return unauthorized_request("Invalid Login")


@staff.post("/staff/approve/")
@staff.input(ApproveStaffSchema)
@staff.output(SuccessMessage)
@token_auth([UserTypes.school_admin])
def approve_staff(json_data):
    school_id = get_current_user()["school_id"]
    school = school_manager.get_school_by_id(school_id)

    staff_number = len(staff_manager.get_staff_by_school(school_id, approved_only=True))

    if (
        staff_number
        >= SubscriptionLimits.get_limits(school.subscription_package)[
            Features.StaffLimit
        ]
    ):
        return bad_request("You have reached your staff limit!")

    for staff_id in json_data["staff_ids"]:
        staff = staff_manager.get_staff_by_id(staff_id)
        if staff:
            staff.is_approved = True
            staff.save()
    return success_response()


@staff.post("/staff/unapprove/")
@staff.input(ApproveStaffSchema)
@staff.output(SuccessMessage)
@token_auth([UserTypes.school_admin])
def unapprove_staff(json_data):
    for staff_id in json_data["staff_ids"]:
        staff = staff_manager.get_staff_by_id(staff_id)
        if staff:
            staff.is_approved = False
            staff.save()
    return success_response()


@staff.get("/staff/")
@staff.output(GetStaffListSchema)
@token_auth([UserTypes.school_admin])
def get_staff_list():
    school_id = get_current_user()["school_id"]
    staff = staff_manager.get_staff_by_school(school_id)
    return success_response(data=[st.to_json() for st in staff])


@staff.get("/staff/<int:staff_id>/")
@staff.output(Responses.StaffResponseSchema)
@token_auth(["*"])
def get_staff_details(staff_id):
    staff = staff_manager.get_staff_by_id(staff_id)
    if staff:
        return success_response(data=staff.to_json(include_batches=True))
    return not_found(message="Staff does not exist")


@staff.put("/staff/<int:staff_id>/")
@staff.input(Responses.StaffSchema)
@staff.output(Responses.StaffResponseSchema)
@token_auth([UserTypes.school_admin])
def edit_staff_details(staff_id, json_data):
    staff = staff_manager.get_staff_by_id(staff_id)

    data = json_data["data"]
    subjects = data.pop("subjects", [])

    if staff:
        staff.first_name = data.get("first_name", staff.first_name)
        staff.surname = data.get("surname", staff.surname)
        staff.email = data.get("email", staff.email)
        staff.other_names = data.get("other_names", staff.other_names)
        staff.is_admin = data.get("is_admin", staff.is_admin)
        staff.save()

        if subjects:
            staff.subjects = [
                subject_manager.get_subject_by_id(subject_id) for subject_id in subjects
            ]
        staff.save()

        return success_response(data=staff.to_json(include_batches=True))
    return not_found(message="Staff does not exist")



#region ANALYTICS
@staff.get("/school-admin/dashboard-general/")
@staff.output(Responses.DashboardGeneralSchema)
@token_auth([UserTypes.school_admin])
def dashboard_general():
    from app.student.operations import student_manager, batch_manager
    from app.test.operations import test_manager
    '''
    Get the general dashboard data for the staff
    Returns:
        total_students (int): Total number of students
        total_staff (int): Total number of staff
        total_batches (int): Total number of batches
        total_tests (int): Total number of tests
        package_information (dict): Package information
            subscription_package (str): Subscription package
            subscription_expiry (str): Subscription expiry date
    '''

    school_id = get_current_user()["school_id"]
    students = student_manager.get_active_students_by_school(school_id)
    total_staff = len(staff_manager.get_staff_by_school(school_id))
    total_batches = len(batch_manager.get_batches_by_school_id(school_id))
    total_tests = len(test_manager.get_tests_by_school_id(school_id))
    school = school_manager.get_school_by_id(school_id)
    subscription_package = school.subscription_package
    subscription_expiry = school.subscription_expiry_date

    subscription_description = "You have full access to advanced analytics, unlimited student capacity, and dedicated support for your institution."
    if subscription_package == "free":
        subscription_description = "You have limited access to advanced analytics, 10 student capacity, and dedicated support for your institution."

    return success_response(
        data={
            "total_students": len(students),
            "total_staff": total_staff,
            "total_batches": total_batches,
            "total_tests": total_tests,
            "package_information": {
                "subscription_package": subscription_package,
                "subscription_expiry": subscription_expiry,
                "subscription_description": subscription_description,
            },
        }
    )