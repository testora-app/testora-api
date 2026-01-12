from app.staff.models import Staff
from app._shared.operations import BaseManager
from app._shared.services import hash_password

from typing import List


class StaffManager(BaseManager):
    def create_staff(
        self,
        first_name,
        surname,
        email,
        password,
        school_id,
        is_admin=False,
        is_approved=False,
        other_names=None,
        gender="other",
    ) -> Staff:
        new_staff = Staff(
            first_name=first_name,
            surname=surname,
            email=email,
            password_hash=hash_password(password),
            school_id=school_id,
            is_approved=is_approved,
            other_names=other_names,
            is_admin=is_admin,
            gender=gender,
        )

        self.save(new_staff)
        return new_staff

    def get_staff_by_id(self, staff_id) -> Staff:
        return Staff.query.get(staff_id)

    def get_staff_by_ids(self, staff_ids) -> List[Staff]:
        return Staff.query.filter(Staff.id.in_(staff_ids)).all()

    def get_staff_by_email(self, email) -> Staff:
        return Staff.query.filter_by(email=email).first()

    def get_staff(self) -> List[Staff]:
        return Staff.query.all()

    def get_staff_by_school(self, school_id, approved_only=True) -> List[Staff]:
        if approved_only:
            return Staff.query.filter_by(
                school_id=school_id, is_deleted=False
            ).all()
        return Staff.query.filter_by(school_id=school_id, is_deleted=False).all()


staff_manager = StaffManager()
