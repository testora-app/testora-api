from apiflask.fields import String, List, Nested, Date
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



class Responses:
    SchoolBillingHistorySchema = make_response_schema(SchoolBillingHistorySchema, is_list=True)

