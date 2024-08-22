from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, UserTypes
from app._shared.api_errors import response_builder, unauthorized_request, success_response, not_found
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.notifications.schemas import RecipientSchema, RecipientListSchema, NotificationSchema, NotificationListSchema, DeviceIDSchema
from app.notifications.operations import notification_manager, recipient_manager


notification = APIBlueprint('notifications', __name__)


@notification.get('/notifications/')
@notification.output(NotificationListSchema)
@token_auth([UserTypes.staff, UserTypes.student, UserTypes.school_admin])
def get_notifications():
    user_email = get_current_user()['user_email']
    recipient = recipient_manager.get_recipient_by_email(user_email)

    notifications = notification_manager.get_recipient_notifications(recipient.id)
    
    return success_response(data=[n.to_json() for n in notifications])


@notification.post('/device-ids/')
@notification.input(DeviceIDSchema)
@notification.output(RecipientSchema, 201)
def add_device_ids(json_data):
    curr_user = get_current_user()
    data = json_data['data']

    recipient = recipient_manager.get_recipient_by_email(curr_user['user_email'])
    if recipient:
        devices = recipient.device_ids
        for id in data['device_ids']:
            devices.append(id)
        
        recipient.device_ids = devices
        recipient.save()

    
    new_device = recipient_manager.create_recipient(
        curr_user['user_type'],
        data['device_ids'],
        curr_user['user_email'],
        None
    )
    return success_response(data=new_device.to_json(), status_code=201)