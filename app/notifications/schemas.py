from apiflask.fields import Integer, String, Boolean, List, Nested, Email
from app._shared.schemas import BaseSchema, ID_FIELD, make_response_schema


class NotificationSchema(BaseSchema):
    id = Integer(dump_only=True)
    title = String(required=True)
    content = String(required=True)
    alert_type = String(required=True)
    school_id = Integer(required=False, allow_none=True)
    recipient_id = Integer(required=True)


NotificationListSchema = make_response_schema(NotificationSchema, is_list=True)


class Recipient(BaseSchema):
    id = Integer(dump_only=True)
    category = String(required=True)
    device_ids = List(String(), required=True)
    email = Email(allow_none=True)
    phone_number = String(allow_none=True)


RecipientSchema = make_response_schema(Recipient)
RecipientListSchema = make_response_schema(Recipient, is_list=True)


class DeviceID(BaseSchema):
    device_ids = List(String(), required=True, allow_none=False)


DeviceIDSchema = make_response_schema(DeviceID)
