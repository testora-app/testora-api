from apiflask import APIBlueprint

from app._shared.schemas import SuccessMessage, UserTypes
from app._shared.api_errors import response_builder, unauthorized_request, success_response, not_found
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.notifications.schemas import RecipientSchema, RecipientListSchema, NotificationSchema, NotificationListSchema
from app.notifications.operations import notification_manager, recipient_manager


notification = APIBlueprint('notifications', __name__)


@notification.get('/notifications/')
@notification.output(RecipientListSchema)
@token_auth([UserTypes.staff, UserTypes.student, UserTypes.school_admin])
def get_notifications():
    user_email = get_current_user()['user_email']
    recipient = recipient_manager.get_recipient_by_email(user_email)

    notifications = notification_manager.get_recipient_notifications(recipient.id)
    
    return success_response(data=[n.to_json() for n in notifications])



