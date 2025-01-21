from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, LoginSchema, UserTypes
from app._shared.api_errors import (
    response_builder,
    unauthorized_request,
    success_response,
    not_found,
)
from app._shared.services import check_password, generate_access_token
from app._shared.decorators import token_auth

from app.admin.operations import (
    admin_manager,
    subject_manager,
    topic_manager,
    theme_manager,
)
from app.admin.schemas import (
    AdminListSchema,
    SubjectSchemaList,
    TopicSchemaList,
    AddSubjectSchemaPost,
    AddTopicSchemaPost,
    AddThemeSchemaPost,
    ThemeSchemaList,
    Responses,
    Requests,
)

admin = APIBlueprint("admin", __name__)


# region admin
@admin.get("/admins/")
@admin.output(AdminListSchema)
# @token_auth([UserTypes.admin]))
def get_admins():
    admins = admin_manager.get_admins()
    return success_response(data=[admin.to_json() for admin in admins])


@admin.post("/admins/")
@admin.input(Requests.AddAdminSchema)
@admin.output(Responses.AdminResponseSchema)
# @token_auth([UserTypes.admin]))
def add_admin(json_data):
    if admin_manager.get_admin_by_email(json_data["email"]):
        return response_builder(400, "Admin with that email already exists!")

    new_admin = admin_manager.create_admin(**json_data)
    return success_response(data=new_admin.to_json())


@admin.post("/admins/authenticate/")
@admin.input(LoginSchema)
@admin.output(Responses.VerifiedAdminResponse)
def admin_login(json_data):
    admin = admin_manager.get_admin_by_email(json_data["email"])
    if not admin:
        return unauthorized_request("Invalid Login Details")

    if check_password(admin.password_hash, json_data["password"]):
        auth_token = generate_access_token(
            admin.id, UserTypes.admin, admin.email, None, None
        )
        return success_response(
            data={"auth_token": auth_token, "user": admin.to_json()}
        )
    return unauthorized_request("Invalid Login Details")


# endregion admin


# region subjects


@admin.get("/subjects/")
@admin.output(SubjectSchemaList)
# @token_auth(['*'])
def get_subjects():
    subjects = subject_manager.get_subjects()
    return success_response(data=[subject.to_json() for subject in subjects])


@admin.get("/subjects/<string:curriculum>/")
@admin.output(SubjectSchemaList)
# @token_auth(['*'])
def get_subjects_by_curriculum(curriculum):
    subjects = subject_manager.get_subject_by_curriculum(curriculum)
    return success_response(data=[subject.to_json() for subject in subjects])


@admin.post("/subjects/")
@admin.input(AddSubjectSchemaPost)
@admin.output(SubjectSchemaList)
# @token_auth([UserTypes.admin]))
def add_subjects(json_data):
    for subject in json_data["data"]:
        if subject["curriculum"] != "bece":
            return response_builder(
                422, f'{subject["curriculum"]} is not a valid curriculum!'
            )
    new_subjects = subject_manager.create_subjects(json_data["data"])
    return success_response(data=[s.to_json() for s in new_subjects])


@admin.put("/subjects/<int:subject_id>/")
@admin.input(Requests.EditSubjectSchema)
@admin.output(Responses.SubjectSchema)
# @token_auth([UserTypes.admin]))
def edit_subject(subject_id, json_data):
    json_data = json_data["data"]
    subject = subject_manager.get_subject_by_id(subject_id)
    if subject:
        subject.curriculum = json_data["curriculum"]
        subject.name = json_data["name"]
        subject.short_name = json_data["short_name"]
        subject.save()
        return success_response(data=subject.to_json())
    return not_found()


@admin.delete("/subjects/<int:subject_id>/")
@admin.output(SuccessMessage)
# @token_auth([UserTypes.admin]))
def delete_subject(subject_id):
    subject = subject_manager.get_subject_by_id(subject_id)
    if subject:
        subject.delete()
        return success_response()
    return not_found()


@admin.get("/subjects/<int:subject_id>/topics")
@admin.output(TopicSchemaList)
# @token_auth(['*'])
def get_subject_topics(subject_id):
    topics = topic_manager.get_topic_by_subject(subject_id)
    return success_response(data=[topic.to_json() for topic in topics])


# endregion subjects


# region themes


@admin.get("/themes/")
@admin.output(ThemeSchemaList)
# @token_auth(['*'])
def get_themes():
    themes = theme_manager.get_themes()
    return success_response(data=[theme.to_json() for theme in themes])


@admin.post("/themes/")
@admin.input(AddThemeSchemaPost)
@admin.output(ThemeSchemaList)
# @token_auth([UserTypes.admin]))
def add_themes(json_data):
    new_themes = theme_manager.create_themes(json_data["data"])
    return success_response(data=[theme.to_json() for theme in new_themes])


@admin.put("/themes/<int:theme_id>/")
@admin.input(Requests.EditThemeSchema)
@admin.output(Responses.ThemeSchema)
# @token_auth([UserTypes.admin]))
def edit_theme(theme_id, json_data):
    json_data = json_data["data"]
    theme = theme_manager.get_theme_by_id(theme_id)
    if theme:
        theme.name = json_data["name"]
        theme.short_name = json_data["short_name"]
        theme.subject_id = json_data["subject_id"]
        theme.save()
        return success_response(data=theme.to_json())
    return not_found()


@admin.delete("/themes/<int:theme_id>/")
@admin.output(SuccessMessage)
# @token_auth([UserTypes.admin]))
def delete_theme(theme_id):
    theme = theme_manager.get_theme_by_id(theme_id)
    if theme:
        theme.delete()
        return success_response()
    return not_found()


# endregion themes


# region topics


@admin.get("/topics/")
@admin.output(TopicSchemaList)
# @token_auth(['*'])
def get_topics():
    topics = topic_manager.get_topics()
    return success_response(data=[topic.to_json() for topic in topics])


@admin.post("/topics/")
@admin.input(AddTopicSchemaPost)
@admin.output(TopicSchemaList)
# @token_auth([UserTypes.admin]))
def add_topics(json_data):
    new_topics = topic_manager.create_topics(json_data["data"])
    return success_response(data=[topic.to_json() for topic in new_topics])


@admin.put("/topics/<int:topic_id>/")
@admin.input(Requests.EditTopicSchema)
@admin.output(Responses.TopicSchema)
# @token_auth([UserTypes.admin]))
def edit_topic(topic_id, json_data):
    json_data = json_data["data"]
    topic = topic_manager.get_topic_by_id(topic_id)
    if topic:
        topic.name = json_data["name"]
        topic.short_name = json_data["short_name"]
        topic.subject_id = json_data["subject_id"]
        topic.save()
        return success_response(data=topic.to_json())
    return not_found()


@admin.delete("/topics/<int:topic_id>/")
@admin.output(SuccessMessage)
# @token_auth([UserTypes.admin]))
def delete_topic(topic_id):
    topic = topic_manager.get_topic_by_id(topic_id)
    if topic:
        topic.delete()
        return success_response()
    return not_found()


# endregion topics
