from app.student.models import StudentSubjectLevel
from app.student.operations import level_history_manager
from app._shared.schemas import LevelLimitPoints
from collections import defaultdict
from statistics import mean


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
                level_to=new_level,
            )
            # TODO: push notifications to frontend

        stu_sub_level.level = new_level
        stu_sub_level.save()


def add_batch_to_student_data(student_data, batch_name):
    for student in student_data:
        student["batches"] = [{"batch_name": batch_name}]

    return student_data


def transform_data_for_averages(students, test_scores, subject_name="All Subjects"):
    # Aggregate scores by student_id
    scores_by_student = defaultdict(list)
    for score in test_scores:
        scores_by_student[score["student_id"]].append(score["score_acquired"])

    # Compute the desired output
    result = [
        {
            "student_name": f"{students[student_id]['surname']}  {students[student_id]['first_name']}  {students[student_id]['other_names']}",
            "subject_name": subject_name,  # Handle optional subject_name
            "average_score": mean(scores) if scores else 0,  # Compute average score
            "batch_name": students[student_id]["batches"][0]["batch_name"],
        }
        for student_id, scores in scores_by_student.items()
        if student_id in students
    ]

    return result


def sort_results(results, order="best"):
    """
    Sorts the results by average_score in ascending or descending order.

    :param results: List of dictionaries containing student data and scores.
    :param order: Either 'best' or 'worst' to determine sorting order.
    :return: Sorted list of results.
    """
    if order not in ["best", "worst"]:
        raise ValueError("Invalid order. Allowed values are 'best' or 'worst'.")

    reverse = True if order == "best" else False
    return sorted(results, key=lambda x: x["average_score"], reverse=reverse)
