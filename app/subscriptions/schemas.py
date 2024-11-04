from apiflask.fields import String, List, Nested, Date, Boolean
from app._shared.schemas import BaseSchema, ID_FIELD, make_response_schema


class SchoolBillingHistorySchema(BaseSchema):
    id = ID_FIELD
    school_id = ID_FIELD
    amount_due = String(required=True, allow_none=False)
    date_due = Date(required=True, allow_none=False)
    billed_on = Date(required=True, allow_none=False)
    settled_on = Date(required=False, allow_none=True)
    payment_reference = String(required=False, allow_none=True)
    subscription_package = String(required=True, allow_none=False)
    subscription_start_date = Date(required=True, allow_none=False)
    subscription_end_date = Date(required=True, allow_none=False)


class PaymentInitSchema(BaseSchema):
    status = Boolean(required=True, allow_none=False)
    authorization_url = String(required=True, allow_none=False)
    reference = String(required=True, allow_none=False)
    access_code = String(required=True, allow_none=False)


class SchoolBillingPostSchema(BaseSchema):
    amount_due = String(required=True, allow_none=False)
    payment_reference = String(required=False, allow_none=True)
    subscription_package = String(required=True, allow_none=False)


class Responses:
    SingleSchoolBillingHistorySchema = make_response_schema(SchoolBillingHistorySchema)
    SchoolBillingHistorySchema = make_response_schema(SchoolBillingHistorySchema, is_list=True)
    PaymentInitSchema = make_response_schema(PaymentInitSchema)
    SchoolBillingPostSchema = make_response_schema(SchoolBillingPostSchema) 

