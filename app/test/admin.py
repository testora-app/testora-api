from app.extensions import admin, db
from app.test.models import Question
from app.app_admin.models import Topic
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2Field
from wtforms import Form, TextAreaField, SelectField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional

class QuestionForm(Form):
    text = TextAreaField('Text', validators=[DataRequired()])
    correct_answer = TextAreaField('Correct Answer', validators=[Optional()])
    possible_answers = TextAreaField('Possible Answers', validators=[Optional()])
    topic_id = SelectField('Topic', coerce=int, validators=[DataRequired()])
    points = IntegerField('Points', validators=[Optional()])
    school_id = IntegerField('School ID', validators=[Optional()])
    is_flagged = BooleanField('Is Flagged', validators=[Optional()])
    flag_reason = TextAreaField('Flag Reason', validators=[Optional()])
    year = IntegerField('Year', validators=[Optional()])
    
class CustomFormQuestionView(ModelView):
    can_edit = True
    can_delete = True
    can_create = True
    
    # Use a custom form
    form = QuestionForm
    
    def create_form(self):
        form = super(CustomFormQuestionView, self).create_form()
        # Populate topic_id choices
        form.topic_id.choices = [(topic.id, topic.name) for topic in Topic.query.all()]
        return form
        
    def edit_form(self, obj):
        form = super(CustomFormQuestionView, self).edit_form(obj)
        # Populate topic_id choices
        form.topic_id.choices = [(topic.id, topic.name) for topic in Topic.query.all()]
        return form
    
    def on_model_change(self, form, model, is_created):
        """Handle possible_answers conversion"""
        if model.possible_answers:
            # Ensure it's a valid string representation of a list
            if not (model.possible_answers.startswith('[') and model.possible_answers.endswith(']')):
                model.possible_answers = str([item.strip() for item in model.possible_answers.split(',')])

# Register the view
admin.add_view(CustomFormQuestionView(Question, db.session, name="QuestionsForms"))