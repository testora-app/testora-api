from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, LoginSchema, UserTypes
from app._shared.api_errors import (
    response_builder,
    unauthorized_request,
    success_response,
    not_found,
)
from app._shared.services import check_password, generate_access_token
from app._shared.decorators import public_protected

from app.app_admin.operations import (
    admin_manager,
    subject_manager,
    topic_manager,
    theme_manager,
)
from app.app_admin.schemas import (
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

app_admin = APIBlueprint("app_admin", __name__)


# region admin
@app_admin.get("/app-admins/")
@app_admin.output(AdminListSchema)
@public_protected
def get_admins():
    admins = admin_manager.get_admins()
    return success_response(data=[admin.to_json() for admin in admins])


@app_admin.post("/app-admins/")
@app_admin.input(Requests.AddAdminSchema)
@app_admin.output(Responses.AdminResponseSchema)
@public_protected
def add_admin(json_data):
    if admin_manager.get_admin_by_email(json_data["email"]):
        return response_builder(400, "Admin with that email already exists!")

    new_admin = admin_manager.create_admin(**json_data)
    return success_response(data=new_admin.to_json())


@app_admin.post("/app-admins/authenticate/")
@app_admin.input(LoginSchema)
@app_admin.output(Responses.VerifiedAdminResponse)
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

@app_admin.get('/curriculum/')
@app_admin.output(Responses.CurriculumSchema)
def get_curriculums():
    data = [{
        'name': 'bece',
        'display_name': 'BECE'
    }]
    return success_response(data=data)

@app_admin.get("/subjects/")
@app_admin.output(SubjectSchemaList)
def get_subjects():
    subjects = subject_manager.get_subjects()
    data = [subject.to_json() for subject in subjects]

    for subject in data:
        subject["themes"] = [theme.to_json() for theme in theme_manager.get_theme_by_subject(subject["id"])]
        for theme in subject["themes"]:
            theme["topics"] = [topic.to_json() for topic in topic_manager.get_topic_by_theme(theme["id"])]
    return success_response(data=data)


@app_admin.get("/subjects/<string:curriculum>/")
@app_admin.output(SubjectSchemaList)
def get_subjects_by_curriculum(curriculum):
    subjects = subject_manager.get_subject_by_curriculum(curriculum)
    return success_response(data=[subject.to_json() for subject in subjects])


@app_admin.post("/subjects/")
@app_admin.input(AddSubjectSchemaPost)
@app_admin.output(SubjectSchemaList)
@public_protected
def add_subjects(json_data):
    for subject in json_data["data"]:
        if subject["curriculum"] != "bece":
            return response_builder(
                422, f'{subject["curriculum"]} is not a valid curriculum!'
            )
    new_subjects = subject_manager.create_subjects(json_data["data"])
    return success_response(data=[s.to_json() for s in new_subjects])


@app_admin.put("/subjects/<int:subject_id>/")
@app_admin.input(Requests.EditSubjectSchema)
@app_admin.output(Responses.SubjectSchema)
@public_protected
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


@app_admin.delete("/subjects/<int:subject_id>/")
@app_admin.output(SuccessMessage)
@public_protected
def delete_subject(subject_id):
    subject = subject_manager.get_subject_by_id(subject_id)
    if subject:
        subject.delete()
        return success_response()
    return not_found()


@app_admin.get("/subjects/<int:subject_id>/topics")
@app_admin.output(TopicSchemaList)
def get_subject_topics(subject_id):
    topics = topic_manager.get_topic_by_subject(subject_id)
    return success_response(data=[topic.to_json() for topic in topics])


# endregion subjects


# region themes


@app_admin.get("/themes/")
@app_admin.output(ThemeSchemaList)
def get_themes():
    themes = theme_manager.get_themes()
    return success_response(data=[theme.to_json() for theme in themes])


@app_admin.post("/themes/")
@app_admin.input(AddThemeSchemaPost)
@app_admin.output(ThemeSchemaList)
@public_protected
def add_themes(json_data):
    new_themes = theme_manager.create_themes(json_data["data"])
    return success_response(data=[theme.to_json() for theme in new_themes])


@app_admin.put("/themes/<int:theme_id>/")
@app_admin.input(Requests.EditThemeSchema)
@app_admin.output(Responses.ThemeSchema)
@public_protected
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


@app_admin.delete("/themes/<int:theme_id>/")
@app_admin.output(SuccessMessage)
@public_protected
def delete_theme(theme_id):
    theme = theme_manager.get_theme_by_id(theme_id)
    if theme:
        theme.delete()
        return success_response()
    return not_found()


# endregion themes


# region topics


@app_admin.get("/topics/")
@app_admin.output(TopicSchemaList)
def get_topics():
    topics = topic_manager.get_topics()
    return success_response(data=[topic.to_json() for topic in topics])


@app_admin.post("/topics/")
@app_admin.input(AddTopicSchemaPost)
@app_admin.output(TopicSchemaList)
@public_protected
def add_topics(json_data):
    new_topics = topic_manager.create_topics(json_data["data"])
    return success_response(data=[topic.to_json() for topic in new_topics])


@app_admin.put("/topics/<int:topic_id>/")
@app_admin.input(Requests.EditTopicSchema)
@app_admin.output(Responses.TopicSchema)
@public_protected
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


@app_admin.delete("/topics/<int:topic_id>/")
@app_admin.output(SuccessMessage)
@public_protected
def delete_topic(topic_id):
    topic = topic_manager.get_topic_by_id(topic_id)
    if topic:
        topic.delete()
        return success_response()
    return not_found()


# endregion topics
