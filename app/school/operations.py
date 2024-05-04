from app.school.models import School
from app.school.services import create_school_code
from app._shared.operations import BaseManager

from typing import List

class SchoolManager(BaseManager):
    def create_school(self, name, location, short_name=None, logo=None, is_package_school=False,
                      phone_number=None, email=None) -> School:
        
        if short_name:
            code = create_school_code(short_name)
        else:
            code = create_school_code(name[:3])
        new_school = School(
            name=name,
            location=location,
            short_name=short_name,
            logo=logo,
            is_package_school=is_package_school,
            phone_number=phone_number,
            email=email,
            code = code
        )

        self.save(new_school)
        return new_school
    

    def get_schools(self) -> List[School]:
        return School.query.all()
    
    def get_school_by_id(self, school_id) -> School:
        return School.query.get(school_id)
    
    def get_school_by_code(self, code) -> School:
        return School.query.filter_by(code=code).first()
    

school_manager = SchoolManager()
