from apiflask import APIBlueprint
from flask import request

from app._shared.schemas import SuccessMessage, UserTypes
from app._shared.api_errors import (
    response_builder,
    unauthorized_request,
    success_response,
    not_found,
)
from app._shared.decorators import token_auth
from app._shared.services import get_current_user

from app.notifications.schemas import (
    RecipientSchema,
    RecipientListSchema,
    NotificationSchema,
    NotificationListSchema,
    DeviceIDSchema,
    ReadNotificationsSchema
)
from app.notifications.operations import notification_manager, recipient_manager

from app.integrations.pusher import pusher


notification = APIBlueprint("notifications", __name__)


@notification.get("/notifications/")
@notification.output(NotificationListSchema)
@token_auth([UserTypes.staff, UserTypes.student, UserTypes.school_admin])
def get_notifications():
    user_email = get_current_user()["user_email"]
    recipient = recipient_manager.get_recipient_by_email(
        user_email, get_current_user()["user_type"]
    )

    if recipient:
        notifications = notification_manager.get_recipient_notifications(recipient.id)
        return success_response(data=[n.to_json() for n in notifications])
    return success_response(data=[])


@notification.put("/notifications/read/")
@notification.input(ReadNotificationsSchema)
@notification.output(SuccessMessage, 200)
@token_auth([UserTypes.staff, UserTypes.student, UserTypes.school_admin])
def read_notifications(json_data):
    notification_manager.update_read_status(json_data["data"]["notification_ids"])
    return success_response()


@notification.post("/device-ids/")
@notification.input(DeviceIDSchema)
@notification.output(RecipientSchema, 201)
@token_auth([UserTypes.staff, UserTypes.student, UserTypes.school_admin])
def add_device_ids(json_data):
    curr_user = get_current_user()
    data = json_data["data"]

    title = "Welcome To Preppee!"
    content = "You have subscribed to our notifications system. You can now receive notifications from us."

    recipient = recipient_manager.get_recipient_by_email(
        curr_user["user_email"], curr_user["user_type"]
    )
    if recipient:
        new_device = []
        for id in data["device_ids"]:
            new_device.append(id)

        recipient.device_ids = new_device
        recipient.save()

        pusher.notify_devices(title, content, emails=[recipient.email])
        return success_response(data=recipient.to_json(), status_code=201)

    new_device = recipient_manager.create_recipient(
        curr_user["user_type"], data["device_ids"], curr_user["user_email"], None
    )
    pusher.notify_devices(title, content, emails=[new_device.email])
    return success_response(data=new_device.to_json(), status_code=201)


@notification.get("/test-notifications/")
def test_notifications():
    if request.args.get("all"):
        recipients = recipient_manager.get_recipients()
    else:
        staff = recipient_manager.get_recipient_by_email(
            "naruto@testora.online", UserTypes.staff
        )
        student = recipient_manager.get_recipient_by_email(
            "bortuo@testora.online", UserTypes.student
        )

        recipients = [staff, student]

    for recipient in recipients:
        if recipient:
            pusher.notify_devices(
                request.args.get("title", "Test Notification"),
                request.args.get("message", "This is a test notification"),
                emails=[recipient.email],
            )

            notification_manager.create_notification(
                request.args.get("title", "Test Notification"),
                request.args.get("message", "This is a test notification"),
                "test",
                recipient.id,
            )
    return success_response()
