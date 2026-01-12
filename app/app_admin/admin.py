from app.app_admin.models import Subject, Theme, Topic
from flask_admin.contrib.sqla import ModelView
from app.extensions import admin, db

class SubjectAdmin(ModelView):
    form_columns = ['name', 'short_name', 'curriculum', 'max_duration']
    form_choices = {
        'curriculum': [
            ('bece', 'BECE'),
            ('igcse', 'IGCSE'),
        ]
    }

class ThemeAdmin(ModelView):
    form_columns = ['name', 'short_name', 'subject_id']  # Explicitly list fields

class TopicAdmin(ModelView):
    form_columns = ['name', 'short_name', 'level', 'theme_id', 'subject_id']

admin.add_view(SubjectAdmin(Subject, db.session, name="Subjects"))
admin.add_view(ThemeAdmin(Theme, db.session, name="Themes"))
admin.add_view(TopicAdmin(Topic, db.session, name="Topics"))