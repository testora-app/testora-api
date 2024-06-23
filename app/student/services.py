from app.student.models import StudentSubjectLevel
from app.student.operations import level_history_manager
from app._shared.schemas import LevelLimitPoints

class SubjectLevelManager:

    @staticmethod
    def check_and_level_up(stu_sub_level: StudentSubjectLevel):
        new_level = LevelLimitPoints.get_points_level(stu_sub_level.points)

        if new_level != stu_sub_level.level:
            # we're levelling up or down
            level_history_manager.add_new_history(
                student_id=stu_sub_level.student_id,
                subject_id=stu_sub_level.subject_id,
                level_from=stu_sub_level.level,
                level_to=new_level
            )
            #TODO: push notifications to frontend

        stu_sub_level.level = new_level
        stu_sub_level.save()

        
    
