from apiflask import APIBlueprint
from flask import jsonify

from app._shared.schemas import SuccessMessage, LoginSchema, UserTypes
from app._shared.api_errors import error_response, unauthorized_request, success_response
from app._shared.services import check_password, generate_access_token
from app._shared.decorators import token_auth

from app.admin.operations import admin_manager, subject_manager, topic_manager
from app.admin.schemas import (AddAdminSchema, AdminListSchema, AdminSchema, VerifiedAdminSchema, SubjectSchemaList, TopicSchemaList, AddSubjectSchemaPost, AddTopicSchemaPost)

admin = APIBlueprint('admin', __name__)



@admin.get('/admins/')
@admin.output(AdminListSchema)
@token_auth([UserTypes.admin])
def get_admins():
    admins = admin_manager.get_admins()
    return success_response(data=[admin.to_json() for admin in admins])


@admin.post('/admins/')
@admin.input(AddAdminSchema)
@admin.output(AdminSchema)
@token_auth([UserTypes.admin])
def add_admin(json_data):
    if admin_manager.get_admin_by_email(json_data["email"]):
        return error_response(400, "Admin with that email already exists!")
    
    new_admin = admin_manager.create_admin(**json_data)
    return new_admin.to_json()


@admin.post('/admins/authenticate/')
@admin.input(LoginSchema)
@admin.output(VerifiedAdminSchema)
def admin_login(json_data):
    admin = admin_manager.get_admin_by_email(json_data["email"])
    if not admin:
        return unauthorized_request("Invalid Login Details")
    
    if check_password(admin.password_hash, json_data["password"]):
        auth_token = generate_access_token(admin.id, 'admin', None, None)
        return success_response(data={'auth_token': auth_token, 'user': admin.to_json()})
    return unauthorized_request("Invalid Login Details")



@admin.get('/subjects/')
@admin.output(SubjectSchemaList)
def get_subjects():
    return subject_manager.get_subjects()

@admin.post('/subjects/')
@admin.input(AddSubjectSchemaPost)
@admin.output(SubjectSchemaList)
def add_subjects(json_data):
    new_subjects = subject_manager.create_subjects(json_data)
    return success_response(data=[s.to_json() for s in new_subjects])

@admin.get('/subjects/<int: subject_id>/topics')
@admin.output(TopicSchemaList)
def get_subject_topics(subject_id):
    topics = topic_manager.get_topic_by_subject(subject_id)
    return success_response(data=[topic.to_json() for topic in topics])


@admin.get('/topics/')
@admin.output(TopicSchemaList)
def get_topics():
    return topic_manager.get_topics()

@admin.post('/topics/')
@admin.input(AddTopicSchemaPost)
@admin.output(TopicSchemaList)
def add_topics(json_data):
    new_topics = topic_manager.create_topics(json_data)
    return [topic.to_json() for topic in new_topics]
