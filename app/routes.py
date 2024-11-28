import jwt
from apiflask import APIBlueprint
from flask import jsonify, request, current_app as app

from app._shared.schemas import SuccessMessage, ResetPasswordSchema, ChangePasswordSchema, ContactUsSchema
from app._shared.api_errors import bad_request, not_found, success_response, unauthorized_request
from app._shared.services import generate_and_send_reset_password_email, hash_password, generate_and_send_password_changed
from app.student.operations import student_manager
from app.staff.operations import staff_manager

from app.integrations.mailer import mailer

main = APIBlueprint('main', __name__)

#routes
@main.get("/")
@main.output(SuccessMessage, 200)
def index():
    return jsonify({'message': 'Hello from your friends at Testora or is it?!!!'})


@main.post("/contact-us/")
@main.input(ContactUsSchema)
@main.output(SuccessMessage, 200)
def contact_us(json_data):
    data = json_data['data']

    html = mailer.generate_email_text('support_response.html')

    mailer.send_email([data['email']], "We've Received Your Email ", html, html=html)

    contact_html = mailer.generate_email_text('new_contact.html', data)

    mailer.send_email(['support@wedidtech.com', 'info@wedidtech.com'], "We Have A New Contact!", contact_html, html=contact_html)
    return success_response()

@main.post('/account/reset-password/')
@main.input(ResetPasswordSchema)
@main.output(SuccessMessage, 200)
def reset_password(json_data):
    user_type = request.args.get('user_type')

    data = json_data['data']

    if not user_type:
        return bad_request(f" 'user_type' is a required args. it should be either 'staff' or 'student' ")
    
    user = None
    if user_type == 'student':
        user = student_manager.get_student_by_email(data['email'])

    elif user_type == 'staff':
        user = staff_manager.get_staff_by_email(data['email'])
    
    if user:
        generate_and_send_reset_password_email(user.id, user_type, user.school_id, user.first_name, user.email)
    return success_response()
    

@main.post('/account/change-password/')
@main.input(ChangePasswordSchema)
@main.output(SuccessMessage, 200)
def change_password(json_data):
    data = json_data['data']

    try:
        confirmed_user = jwt.decode(data['confirmation_code'], app.config['SECRET_KEY'],  algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return unauthorized_request('Token has expired')
    except jwt.InvalidTokenError:
        return unauthorized_request('Invalid Token')
    
    user_type = confirmed_user['user_type']

    user = None

    if user_type == 'staff':
        user = staff_manager.get_staff_by_id(confirmed_user['user_id'])
    elif user_type == 'student':
        user = student_manager.get_student_by_id(confirmed_user['user_id'])

    if user:
        user.password_hash = hash_password(data['new_password'])
        user.save()
        generate_and_send_password_changed(user.email, user.first_name)
    return success_response()
    


