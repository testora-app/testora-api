import secrets
import string
from datetime import datetime

from apiflask import APIBlueprint
from flask import request
from sqlalchemy.exc import IntegrityError

from app._shared.schemas import UserTypes
from app._shared.api_errors import (
    success_response,
    not_found,
    bad_request,
)
from app._shared.decorators import token_auth
from app._shared.services import hash_password, generate_and_send_reset_password_email

from app.school.schemas import GetSchoolListSchema
from app.school.operations import school_manager

school = APIBlueprint("school", __name__)


def _generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


@school.get("/schools/")
@school.output(GetSchoolListSchema)
@token_auth([UserTypes.admin])
def get_schools():
    from app.extensions import db
    from sqlalchemy import func
    from app.staff.models import Staff
    from app.student.models import Student

    schools = school_manager.get_schools()
    data = [school.to_json() for school in schools]

    staff_counts = dict(
        db.session.query(Staff.school_id, func.count(Staff.id))
        .filter(Staff.is_deleted == False)
        .group_by(Staff.school_id)
        .all()
    )
    student_counts = dict(
        db.session.query(Student.school_id, func.count(Student.id))
        .filter(Student.is_deleted == False)
        .group_by(Student.school_id)
        .all()
    )
    seats_used_counts = dict(
        db.session.query(Student.school_id, func.count(Student.id))
        .filter(
            Student.is_deleted == False,
            Student.is_approved == True,
            Student.is_archived == False,
        )
        .group_by(Student.school_id)
        .all()
    )

    for entry in data:
        entry["staff_count"] = staff_counts.get(entry["id"], 0)
        entry["student_count"] = student_counts.get(entry["id"], 0)
        entry["seats_used"] = seats_used_counts.get(entry["id"], 0)

    return success_response(data=data)


@school.get("/schools/<int:school_id>/")
@token_auth([UserTypes.admin])
def get_school(school_id):
    from app.staff.operations import staff_manager
    from app.student.operations import student_manager

    sch = school_manager.get_school_by_id(school_id)
    if not sch:
        return not_found("School not found")

    data = sch.to_json()
    data["staff_count"] = len(staff_manager.get_staff_by_school(school_id))
    data["student_count"] = len(student_manager.get_student_by_school(school_id))
    data["seats_used"] = len(
        student_manager.get_active_students_by_school(school_id, only_approved=True)
    )
    return success_response(data=data)


@school.put("/schools/<int:school_id>/")
@token_auth([UserTypes.admin])
def edit_school(school_id):
    sch = school_manager.get_school_by_id(school_id)
    if not sch:
        return not_found("School not found")

    body = request.get_json() or {}
    data = body.get("data", body)

    for field in ("name", "short_name", "location", "phone_number", "email"):
        if field in data and data[field] is not None:
            setattr(sch, field, data[field])

    if "is_suspended" in data and data["is_suspended"] is not None:
        sch.is_suspended = bool(data["is_suspended"])

    if data.get("subscription_tier"):
        sch.subscription_tier = data["subscription_tier"]

    if data.get("total_seats") is not None:
        try:
            sch.total_seats = int(data["total_seats"])
        except (TypeError, ValueError):
            return bad_request("total_seats must be a number")

    if data.get("subscription_expiry_date"):
        try:
            sch.subscription_expiry_date = datetime.strptime(
                data["subscription_expiry_date"], "%Y-%m-%d"
            ).date()
        except (TypeError, ValueError):
            return bad_request("subscription_expiry_date must be in YYYY-MM-DD format")

    sch.save()
    return success_response(data=sch.to_json())


@school.get("/schools/<int:school_id>/staff/")
@token_auth([UserTypes.admin])
def get_school_staff(school_id):
    from app.staff.operations import staff_manager

    staff = staff_manager.get_staff_by_school(school_id)
    return success_response(data=[member.to_json() for member in staff])


@school.get("/schools/<int:school_id>/students/")
@token_auth([UserTypes.admin])
def get_school_students(school_id):
    from app.student.operations import student_manager

    students = student_manager.get_student_by_school(school_id)
    return success_response(data=[student.to_json(include_batch=False) for student in students])


@school.get("/schools/<int:school_id>/billing-history/")
@token_auth([UserTypes.admin])
def get_school_billing(school_id):
    from app.subscriptions.operations import sb_history_manager

    history = sb_history_manager.get_school_billing_history(school_id)
    return success_response(data=[bill.to_json() for bill in history])


@school.post("/schools/reset-user-password/")
@token_auth([UserTypes.admin])
def reset_user_password():
    from app.staff.operations import staff_manager
    from app.student.operations import student_manager

    body = request.get_json() or {}
    data = body.get("data", body)

    user_type = data.get("user_type")
    user_id = data.get("user_id")
    mode = data.get("mode", "set")

    if user_type not in ("staff", "student"):
        return bad_request("user_type must be 'staff' or 'student'")
    if not user_id:
        return bad_request("user_id is required")
    if mode not in ("set", "email"):
        return bad_request("mode must be 'set' or 'email'")

    user = (
        staff_manager.get_staff_by_id(user_id)
        if user_type == "staff"
        else student_manager.get_student_by_id(user_id)
    )
    if not user:
        return not_found("User not found")

    if mode == "email":
        generate_and_send_reset_password_email(
            user.id, user_type, user.email, user.school_id, user.first_name
        )
        return success_response(data={"mode": "email", "email": user.email})

    temp_password = _generate_temp_password()
    user.password_hash = hash_password(temp_password)
    user.save()
    return success_response(
        data={"mode": "set", "temporary_password": temp_password, "email": user.email}
    )


@school.put("/schools/staff/<int:staff_id>/")
@token_auth([UserTypes.admin])
def admin_edit_staff(staff_id):
    from app.extensions import db
    from app.staff.operations import staff_manager

    staff = staff_manager.get_staff_by_id(staff_id)
    if not staff:
        return not_found("Staff not found")

    body = request.get_json() or {}
    data = body.get("data", body)

    for field in ("first_name", "surname", "other_names", "email"):
        if field in data and data[field] is not None:
            setattr(staff, field, data[field])
    if data.get("is_admin") is not None:
        staff.is_admin = bool(data["is_admin"])
    if data.get("is_approved") is not None:
        staff.is_approved = bool(data["is_approved"])

    try:
        staff.save()
    except IntegrityError:
        db.session.rollback()
        return bad_request("That email is already in use.")
    return success_response(data=staff.to_json())


@school.put("/schools/students/<int:student_id>/")
@token_auth([UserTypes.admin])
def admin_edit_student(student_id):
    from app.extensions import db
    from app.student.operations import student_manager

    student = student_manager.get_student_by_id(student_id)
    if not student:
        return not_found("Student not found")

    body = request.get_json() or {}
    data = body.get("data", body)

    for field in ("first_name", "surname", "other_names", "email"):
        if field in data and data[field] is not None:
            setattr(student, field, data[field])
    if data.get("is_approved") is not None:
        student.is_approved = bool(data["is_approved"])
    if data.get("is_archived") is not None:
        student.is_archived = bool(data["is_archived"])

    try:
        student.save()
    except IntegrityError:
        db.session.rollback()
        return bad_request("That email is already in use.")
    return success_response(data=student.to_json(include_batch=False))
