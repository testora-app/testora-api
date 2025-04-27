"""
Routes for the Q&A feature using ChatGPT
"""
from apiflask import APIBlueprint
from flask import jsonify, current_app

from app._shared.api_errors import (
    bad_request,
    not_found,
    success_response,
    server_error,
)
from app.student.operations import student_manager
from app.integrations.openai_integrations import openai_integration
from app.qa.schemas import (
    QuestionRequestSchema,
    QuestionResponseSchema,
    QuestionsListResponseSchema,
)
from app.qa.models import StudentQuestion

qa = APIBlueprint("qa", __name__)


@qa.get("/test")
def test_route():
    return jsonify({"message": "QA route is working!"})


@qa.post("/ask-question/")
@qa.input(QuestionRequestSchema)
@qa.output(QuestionResponseSchema, 200)
def ask_question(json_data):
    """
    Endpoint to ask a question to ChatGPT and get an educational response
    """
    print("Endpoint is called!")
    data = json_data["data"]
    
    # Validate that the student exists
    student = student_manager.get_student_by_id(data["student_id"])
    if not student:
        return bad_request("Student not found")
    
    # Optional: Fetch relevant curriculum content for context
    curriculum_content = None
    
    
    # Generate answer using ChatGPT
    response = openai_integration.ask_question(
        data["subject"],
        data["topic"],
        data["question"],
        curriculum_content
    )
    
    if not response.get("status", False):
        return server_error(response.get("message", "Failed to generate response"))
    
    # Save the interaction to database
    new_question = StudentQuestion(
        student_id=data["student_id"],
        school_id=data["school_id"],
        subject=data["subject"],
        topic=data["topic"],
        question=data["question"],
        answer=response["data"]["answer"]
    )
    
    try:
        new_question.save()
    except Exception as e:
        current_app.logger.error(f"Error saving question: {str(e)}")
        return server_error("Failed to save interaction")
    
    # Return the response
    return success_response(data={
        "answer": response["data"]["answer"],
        "topic": data["topic"],
        "timestamp": new_question.created_at.isoformat()
    })


@qa.get("/questions/<int:student_id>/")
@qa.output(QuestionsListResponseSchema, 200)
def get_student_questions(student_id):
    """
    Endpoint to retrieve all questions asked by a specific student
    """
    questions = StudentQuestion.query.filter_by(student_id=student_id).order_by(
        StudentQuestion.created_at.desc()
    ).all()
    
    return success_response(data=[question.to_dict() for question in questions])