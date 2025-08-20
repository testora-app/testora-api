from apiflask import Schema
from apiflask.fields import Float, String, Integer, Nested, List, DateTime
from apiflask.validators import OneOf, Range

from app._shared.schemas import BaseSchema, make_response_schema


class WeeklyReportSchema(BaseSchema):
    hours_spent = Float(required=True)
    percentage = Float(required=True)


class TopicPerformanceSchema(BaseSchema):
    topic_name = String(required=True)
    subject_name = String(required=True)
    severity = String(required=False)


class TopicPerformanceQuerySchema(Schema):
    student_id = Integer(required=False, allow_none=False)
    subject_id = Integer(required=False, allow_none=False)
    batch_id = Integer(required=False, allow_none=False)

class PerformanceCategorySchema(BaseSchema):
    student_number = Integer(required=True)
    percent_number = Float(required=True)


class StudentPerformanceSchema(BaseSchema):
    passing = Nested(PerformanceCategorySchema, required=True)
    credit = Nested(PerformanceCategorySchema, required=True)
    failing = Nested(PerformanceCategorySchema, required=True)


class PerformanceSummarySchema(BaseSchema):
    batch_average = Float(required=True)
    test_completion = Float(required=True)
    failing_student_ids = List(Integer(), required=True)


class TopicMasteryItemSchema(BaseSchema):
    topic_name = String(required=True)
    average = Float(required=True)


class TopicMasteryDataSchema(BaseSchema):
    strong_topics = List(Nested(TopicMasteryItemSchema), required=True)
    weak_topics = List(Nested(TopicMasteryItemSchema), required=True)


class PracticeRateQuerySchema(BaseSchema):
    subject_id = Integer(required=False, allow_none=True)
    batch_id = Integer(required=True, allow_none=False)
    time_range = String(required=True, allow_none=False, validate=[OneOf(['this_week', 'this_month', 'all_time'])])


class AnalyticsQuerySchema(BaseSchema):
    batch_id = Integer(required=True, allow_none=False)
    subject_id = Integer(required=False, allow_none=True)


class BandStatSchema(Schema):
    class Meta:
        ordered = True
    count = Integer(required=True, example=25, description="Number of students in this band")
    percentage = Float(required=True, example=62.5, description="Percent of students in this band")


class ValueUnitSchema(Schema):
    class Meta:
        ordered = True
    value = Float(required=True, example=3.2)
    unit = String(required=True, example="/week")


class PracticeTierBucketSchema(Schema):
    number = Integer(required=True, validate=Range(min=0), example=42)
    percent = Float(required=True, validate=Range(min=0, max=100), example=37.5)

# ---------- Groups ----------
class TierDistributionSchema(Schema):
    class Meta:
        ordered = True
    highly_proficient = Nested(BandStatSchema, required=True)
    proficient = Nested(BandStatSchema, required=True)
    approaching = Nested(BandStatSchema, required=True)  # per your key
    developing = Nested(BandStatSchema, required=True)
    emerging = Nested(BandStatSchema, required=True)

class SummaryDistributionSchema(Schema):
    class Meta:
        ordered = True
    proficiency_above = Nested(BandStatSchema, required=True)
    at_risk = Nested(BandStatSchema, required=True)
    average_tests = Nested(ValueUnitSchema, required=True)        # e.g., {"value": 12, "unit": "/week"}
    average_time_spent = Nested(ValueUnitSchema, required=True)   # e.g., {"value": 15.4, "unit": "min/student"}


class PracticeTierDistributionSchema(Schema):
    no_practice = Nested(PracticeTierBucketSchema, required=True)
    minimal_practice = Nested(PracticeTierBucketSchema, required=True)
    consistent_practice = Nested(PracticeTierBucketSchema, required=True)
    high_practice = Nested(PracticeTierBucketSchema, required=True)


# ---------- Top-level ----------
class PerformanceDistributionDataSchema(BaseSchema):
    class Meta:
        ordered = True

    subject_name = String(required=True, example="Mathematics")
    proficiency_percent = Float(required=True, example=71.3)
    proficiency_status = String(
        required=True,
        validate=OneOf(["highly_proficient", "proficient", "approaching", "developing", "emerging"]),
        example="proficient"
    )
    tier_distribution = Nested(TierDistributionSchema, required=True)
    summary_distribution = Nested(SummaryDistributionSchema, required=True)
    last_updated = DateTime(required=False, allow_none=True, example="2025-08-14T22:10:00Z")


class PracticeRateDataSchema(BaseSchema):
    rate = Float(required=True, validate=Range(min=0), example=2.8)  # tests per student
    unit = String(required=True, validate=OneOf(["tests/student"]), dump_default="tests/student", example="tests/student")
    change_from = Float(required=True, example=0.3)  # delta vs prior period
    change_direction = String(required=True, validate=OneOf(["up", "down"]), example="up")
    total_students = Integer(required=True, validate=Range(min=0), example=120)

    practiced_percent = Float(required=True, validate=Range(min=0, max=100), example=72.0)
    practiced_number = Integer(required=True, validate=Range(min=0), example=86)
    not_practiced_percent = Float(required=True, validate=Range(min=0, max=100), example=28.0)
    not_practiced_number = Integer(required=True, validate=Range(min=0), example=34)

    tier_distribution = Nested(PracticeTierDistributionSchema, required=True)


class SubjectPerformanceDataSchema(BaseSchema):
    class Meta:
        ordered = True
    subject_name = String(required=True, example="Mathematics")
    student_readiness_number = Integer(required=True, validate=Range(min=0), example=86)
    student_readiness_percent = Float(required=True, validate=Range(min=0, max=100), example=28.0)
    status = String(required=True, validate=OneOf(["highly_proficient", "proficient", "approaching", "developing", "emerging"]), example="proficient")


class RecentTestActivitiesSchema(BaseSchema):
    class Meta:
        ordered = True
    description = String(required=True, example="John Doe completed a test in 'Mathematics'")
    time = Integer(required=True, example=2)
    type = String(required=True, example="user_activity")


class ProficiencyDistributionDataSchema(BaseSchema):
    name = String(required=True, example="Highly Proficient")
    students = Integer(required=True, validate=Range(min=0), example=86)
    percentage = Float(required=True, validate=Range(min=0, max=100), example=28.0)
    

class AverageScoreTrendSchema(BaseSchema):
    class Meta:
        ordered = True
    average_score = Float(required=True, example=28.0)
    month = String(required=True, example="August")

class Responses:
    WeeklyReportSchema = make_response_schema(WeeklyReportSchema)
    TopicPerformanceSchema = make_response_schema(TopicPerformanceSchema, is_list=True)
    StudentPerformanceSchema = make_response_schema(StudentPerformanceSchema)
    PerformanceSummarySchema = make_response_schema(PerformanceSummarySchema)
    TopicMasteryDataSchema = make_response_schema(TopicMasteryDataSchema)
    PracticeRateDataSchema = make_response_schema(PracticeRateDataSchema)
    PerformanceDistributionDataSchema = make_response_schema(PerformanceDistributionDataSchema)
    SubjectPerformanceDataSchema = make_response_schema(SubjectPerformanceDataSchema, is_list=True)
    RecentTestActivitiesSchema = make_response_schema(RecentTestActivitiesSchema, is_list=True)
    ProficiencyDistributionDataSchema = make_response_schema(ProficiencyDistributionDataSchema, is_list=True)
    AverageScoreTrendSchema = make_response_schema(AverageScoreTrendSchema, is_list=True)
    

class Requests:
    TopicPerformanceQuerySchema = TopicPerformanceQuerySchema
    RateDistributionQuerySchema = PracticeRateQuerySchema
    AnalyticsQuerySchema = AnalyticsQuerySchema
