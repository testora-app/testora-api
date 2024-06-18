from app.student.models import Student, Batch
from app._shared.operations import BaseManager
from app._shared.services import hash_password

from typing import List

class StudentManager(BaseManager):
    def create_student(self, first_name, surname, email, password,
                     school_id, is_approved=False, is_archived=False, other_names=None) -> Student:
        new_student = Student(
            first_name=first_name,
            surname=surname,
            email=email,
            password_hash=hash_password(password),
            school_id=school_id,
            is_approved=is_approved,
            other_names=other_names,
            is_archived=is_archived
        )
        
        self.save(new_student)
        return new_student
    

    def get_student_by_id(self, student_id) -> Student:
        return Student.query.get(student_id)

    def get_student_by_email(self, email) -> Student:
        return Student.query.filter_by(email=email).first()
    
    def get_student(self) -> List[Student]:
        return Student.query.all()
    
    def get_student_by_school(self, school_id) -> List[Student]:
        return Student.query.filter_by(school_id=school_id).all()
    


class BatchManager(BaseManager):
    def create_batch(self, batch_name, school_id, curriculum, students=[]):
        new_batch = Batch(
            batch_name=batch_name,
            school_id=school_id,
            curriculum=curriculum,
            students=students
        )

        self.save(new_batch)
        return new_batch
    
    def get_all_batches(self) -> List[Batch]:
        return Batch.query.all()

    def get_batch_by_id(self, batch_id) -> Batch:
        return Batch.query.get(batch_id)
    
    def get_batches_by_school_id(self, school_id) -> List[Batch]:
        return Batch.query.filter_by(school_id=school_id).all()
    
    def get_batch_by_curriculum(self, curriculum) -> List[Batch]:
        return Batch.query.filter_by(curriculum=curriculum).all()
    



student_manager = StudentManager()
batch_manager = BatchManager()