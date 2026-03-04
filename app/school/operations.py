from app.school.models import School
from app.school.services import create_school_code
from app._shared.operations import BaseManager
from app.subscriptions.constants import SubscriptionPackages
from app.subscriptions.constants import (
    TierNames,
    BillingCycles,
    FeatureStatus,
    TRIAL_DEFAULT_SEATS,
    TRIAL_DURATION_DAYS,
    FREE_DEFAULT_SEATS,
)

from typing import List
from datetime import datetime, timezone, timedelta


class SchoolManager(BaseManager):
    def create_school(
        self,
        name,
        location,
        short_name=None,
        logo=None,
        is_package_school=False,
        phone_number=None,
        email=None,
    ) -> School:
        MAX_TRIES = 10_000

        for _ in range(MAX_TRIES):
            code = create_school_code()
            if not self.get_school_by_code(code):
                break
        else:
            raise RuntimeError("Could not generate a unique school code after many attempts.")

        new_school = School(
            name=name,
            location=location,
            short_name=short_name,
            logo=logo,
            is_package_school=is_package_school,
            phone_number=phone_number,
            email=email,
            code=code,
        )

        new_school.subscription_expiry_date = (
            datetime.now(timezone.utc) + timedelta(days=TRIAL_DURATION_DAYS)
        ).date()

        # New schools start on a 30-day trial with 100 seats
        new_school.subscription_package = SubscriptionPackages.premium
        new_school.subscription_tier = TierNames.trial
        new_school.billing_cycle = None
        new_school.price_per_seat = 0
        new_school.total_seats = TRIAL_DEFAULT_SEATS

        self.save(new_school)
        return new_school

    def get_schools(self) -> List[School]:
        return School.query.all()

    def get_school_by_id(self, school_id) -> School:
        return School.query.get(school_id)

    def get_school_by_code(self, code) -> School:
        return School.query.filter_by(code=code).first()

    def get_schools_with_expired_subscriptions(
        self, subscription_expiry_date
    ) -> List[School]:
        return School.query.filter_by(
            subscription_expiry_date=subscription_expiry_date, is_deleted=False
        ).all()

    def suspend_schools(self, school_ids: List[int]) -> None:
        School.query.filter(School.id.in_(school_ids)).update({"is_suspended": True})
        self.commit()

    def demote_schools(self, school_ids: List[int]) -> None:
        School.query.filter(School.id.in_(school_ids)).update({
            "subscription_package": SubscriptionPackages.free,
            "subscription_tier": TierNames.free,
            "billing_cycle": None,
            "price_per_seat": 0,
            "total_seats": FREE_DEFAULT_SEATS,
            "scheduled_downgrade": False,
            "scheduled_downgrade_date": None,
            "scheduled_billing_cycle": None,
            "scheduled_billing_cycle_date": None,
            "scheduled_seat_reduction": None,
            "scheduled_reduction_date": None,
        })
        self.commit()


school_manager = SchoolManager()
