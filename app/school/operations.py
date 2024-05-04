from app.school.models import School
from app._shared.operations import BaseManager

from typing import List

class SchoolManager(BaseManager):
    def create_school(self, name, location, short_name=None, logo=None, is_package_school=False,
                      phone_number=None, email=None) -> School:
        new_school = School(
            name=name,
            location=location,
            short_name=short_name,
            logo=logo,
            is_package_school=is_package_school,
            phone_number=phone_number,
            email=email
        )

        self.save(new_school)
        return new_school
    

    def get_schools() -> List[School]:
        return School.query.all()
    
    def get_school_by_id(school_id) -> School:
        return School.query.get(school_id)
    

school_manager = SchoolManager()
