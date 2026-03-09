from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional, Dict, Any

from app.school.operations import school_manager
from app.student.operations import student_manager
from app.subscriptions.constants import (
    TierNames,
    PackagePrices,
    BillingCycles,
    SubscriptionPackages,
    FREE_DEFAULT_SEATS,
    TRIAL_DEFAULT_SEATS,
)
from app.integrations.mailer import (
    send_trial_expiry_email,
    send_downgrade_confirmation_email,
    send_cycle_change_confirmation_email,
)


@dataclass
class CurrentPlan:
    school_id: int
    school_name: str
    tier: str
    total_seats: int
    seats_used: int
    billing_cycle: Optional[str]
    price_per_seat: float
    start_date: Optional[date]
    end_date: Optional[date]
    scheduled_reduction: Optional[int] = None
    scheduled_reduction_date: Optional[date] = None
    scheduled_downgrade: bool = False
    scheduled_downgrade_date: Optional[date] = None
    scheduled_billing_cycle: Optional[str] = None
    scheduled_billing_cycle_date: Optional[date] = None

    def to_json(self) -> Dict[str, Any]:
        return {
            "school_id": self.school_id,
            "school_name": self.school_name,
            "tier": self.tier,
            "total_seats": self.total_seats,
            "seats_used": self.seats_used,
            "billing_cycle": self.billing_cycle,
            "price_per_seat": self.price_per_seat,
            "start_date": str(self.start_date) if self.start_date else None,
            "end_date": str(self.end_date) if self.end_date else None,
            "scheduled_reduction": self.scheduled_reduction,
            "scheduled_reduction_date": (
                str(self.scheduled_reduction_date) if self.scheduled_reduction_date else None
            ),
            "scheduled_downgrade": self.scheduled_downgrade,
            "scheduled_downgrade_date": (
                str(self.scheduled_downgrade_date) if self.scheduled_downgrade_date else None
            ),
            "scheduled_billing_cycle": self.scheduled_billing_cycle,
            "scheduled_billing_cycle_date": (
                str(self.scheduled_billing_cycle_date) if self.scheduled_billing_cycle_date else None
            ),
        }


def compute_seats_used(school_id: int) -> int:
    # approved + not archived + not deleted
    return len(student_manager.get_active_students_by_school(school_id, only_approved=True))


def get_current_plan(school_id: int) -> CurrentPlan:
    school = school_manager.get_school_by_id(school_id)
    seats_used = compute_seats_used(school_id)

    tier = getattr(school, "subscription_tier", TierNames.free) or TierNames.free
    total_seats = int(getattr(school, "total_seats", FREE_DEFAULT_SEATS) or FREE_DEFAULT_SEATS)
    billing_cycle = getattr(school, "billing_cycle", None)
    price_per_seat = float(getattr(school, "price_per_seat", 0) or 0)

    # Keep end_date aligned with existing renewal date
    end_date = getattr(school, "subscription_expiry_date", None)

    # Derive start_date from cycle length (best-effort)
    start_date = None
    if end_date and billing_cycle:
        try:
            start_date = end_date.fromordinal(end_date.toordinal() - PackagePrices.get_days_in_cycle(billing_cycle))
        except Exception:
            start_date = None

    return CurrentPlan(
        school_id=school.id,
        school_name=school.name,
        tier=tier,
        total_seats=total_seats,
        seats_used=seats_used,
        billing_cycle=billing_cycle,
        price_per_seat=price_per_seat,
        start_date=start_date,
        end_date=end_date,
        scheduled_reduction=getattr(school, "scheduled_seat_reduction", None),
        scheduled_reduction_date=getattr(school, "scheduled_reduction_date", None),
        scheduled_downgrade=bool(getattr(school, "scheduled_downgrade", False)),
        scheduled_downgrade_date=getattr(school, "scheduled_downgrade_date", None),
        scheduled_billing_cycle=getattr(school, "scheduled_billing_cycle", None),
        scheduled_billing_cycle_date=getattr(school, "scheduled_billing_cycle_date", None),
    )


def schedule_downgrade_to_free(school_id: int) -> Dict[str, Any]:
    school = school_manager.get_school_by_id(school_id)

    if school.subscription_tier == TierNames.free:
        raise ValueError("School is already on the Free tier")

    if school.subscription_tier == TierNames.trial:
        raise ValueError("Trial accounts cannot schedule downgrades. They automatically convert to Free on expiry.")

    school.scheduled_downgrade = True
    school.scheduled_downgrade_date = school.subscription_expiry_date
    school.save()

    return {
        "scheduled_downgrade": True,
        "effective_date": str(school.scheduled_downgrade_date) if school.scheduled_downgrade_date else None,
    }


def cancel_scheduled_downgrade(school_id: int) -> None:
    school = school_manager.get_school_by_id(school_id)
    school.scheduled_downgrade = False
    school.scheduled_downgrade_date = None
    school.save()


def add_seats(school_id: int, seats_to_add: int) -> Dict[str, Any]:
    if seats_to_add <= 0:
        raise ValueError("seats_to_add must be > 0")

    school = school_manager.get_school_by_id(school_id)
    if school.scheduled_downgrade:
        raise ValueError("Downgrade is scheduled. Cancel it before adding seats.")

    if school.subscription_tier in [TierNames.free, TierNames.trial]:
        raise ValueError("Cannot add seats on Free or Trial tier")

    if not school.billing_cycle:
        raise ValueError("billing_cycle is required for paid tiers")

    prorated = PackagePrices.calculate_proration(
        tier=school.subscription_tier,
        cycle=school.billing_cycle,
        new_seats=seats_to_add,
        end_date=school.subscription_expiry_date,
    )

    school.total_seats = int(school.total_seats or 0) + int(seats_to_add)
    school.save()

    return {
        "added_seats": int(seats_to_add),
        "prorated_amount": float(prorated),
        "total_seats": int(school.total_seats),
    }


def schedule_seat_reduction(school_id: int, seats_to_remove: int) -> Dict[str, Any]:
    if seats_to_remove <= 0:
        raise ValueError("seats_to_remove must be > 0")

    school = school_manager.get_school_by_id(school_id)
    if school.scheduled_downgrade:
        raise ValueError("Downgrade is scheduled. Cancel it before reducing seats.")

    seats_used = compute_seats_used(school_id)
    total_seats = int(school.total_seats or 0)
    unassigned = max(total_seats - seats_used, 0)

    if seats_to_remove > unassigned:
        raise ValueError("Cannot remove more seats than are unassigned")

    school.scheduled_seat_reduction = int(seats_to_remove)
    school.scheduled_reduction_date = school.subscription_expiry_date
    school.save()

    return {
        "scheduled_reduction": int(seats_to_remove),
        "effective_date": str(school.scheduled_reduction_date) if school.scheduled_reduction_date else None,
    }


def cancel_scheduled_changes(school_id: int) -> Dict[str, Any]:
    school = school_manager.get_school_by_id(school_id)
    school.scheduled_seat_reduction = None
    school.scheduled_reduction_date = None
    school.scheduled_downgrade = False
    school.scheduled_downgrade_date = None
    school.scheduled_billing_cycle = None
    school.scheduled_billing_cycle_date = None
    school.save()
    return {"success": True}


def schedule_cycle_change(school_id: int, new_cycle: str) -> Dict[str, Any]:
    """Schedule billing cycle change for next renewal.

    Validates:
    - School is on paid tier (not free or trial)
    - new_cycle is valid (monthly/termly/yearly)
    - No downgrade scheduled

    Returns: scheduled_cycle, scheduled_date, new_price_per_seat
    """
    valid_cycles = [BillingCycles.monthly, BillingCycles.termly, BillingCycles.yearly]
    if new_cycle not in valid_cycles:
        raise ValueError(f"Invalid billing cycle. Must be one of: {valid_cycles}")

    school = school_manager.get_school_by_id(school_id)

    if school.subscription_tier in [TierNames.free, TierNames.trial]:
        raise ValueError("Cannot change billing cycle on Free or Trial tier")

    if school.scheduled_downgrade:
        raise ValueError("Downgrade is scheduled. Cancel it before changing billing cycle.")

    if school.billing_cycle == new_cycle:
        raise ValueError(f"School is already on {new_cycle} billing cycle")

    new_price_per_seat = PackagePrices.get_price_per_seat(school.subscription_tier, new_cycle)

    school.scheduled_billing_cycle = new_cycle
    school.scheduled_billing_cycle_date = school.subscription_expiry_date
    school.save()

    return {
        "scheduled_billing_cycle": new_cycle,
        "scheduled_billing_cycle_date": str(school.scheduled_billing_cycle_date) if school.scheduled_billing_cycle_date else None,
        "new_price_per_seat": float(new_price_per_seat),
    }


def cancel_scheduled_cycle_change(school_id: int) -> None:
    """Clear scheduled_billing_cycle and scheduled_billing_cycle_date"""
    school = school_manager.get_school_by_id(school_id)
    school.scheduled_billing_cycle = None
    school.scheduled_billing_cycle_date = None
    school.save()


def apply_renewal_if_due(today: Optional[date] = None) -> int:
    """Apply renewal actions for all schools whose renewal date is today.

    Returns number of schools processed.
    """
    if today is None:
        today = datetime.now(timezone.utc).date()

    schools = school_manager.get_schools_with_expired_subscriptions(today)
    processed = 0
    for school in schools:
        # 1. Check if trial expired (highest priority)
        if school.subscription_tier == TierNames.trial:
            school.subscription_tier = TierNames.free
            school.subscription_package = SubscriptionPackages.free
            school.total_seats = FREE_DEFAULT_SEATS
            school.billing_cycle = None
            school.price_per_seat = 0

            seats_used = compute_seats_used(school.id)
            if seats_used > FREE_DEFAULT_SEATS:
                send_trial_expiry_email(school, seats_used)

            school.save()
            processed += 1
            continue

        # 2. Downgrade takes precedence over other changes
        if getattr(school, "scheduled_downgrade", False):
            scheduled_date = school.scheduled_downgrade_date
            school.subscription_tier = TierNames.free
            school.subscription_package = SubscriptionPackages.free
            school.billing_cycle = None
            school.price_per_seat = 0
            school.total_seats = FREE_DEFAULT_SEATS
            school.scheduled_downgrade = False
            school.scheduled_downgrade_date = None

            school.scheduled_seat_reduction = None
            school.scheduled_reduction_date = None
            school.scheduled_billing_cycle = None
            school.scheduled_billing_cycle_date = None
            school.save()

            seats_used = compute_seats_used(school.id)
            if seats_used > FREE_DEFAULT_SEATS:
                send_trial_expiry_email(school, seats_used)
            send_downgrade_confirmation_email(school, scheduled_date)

            processed += 1
            continue

        # 3. Apply scheduled billing cycle change
        if school.scheduled_billing_cycle:
            new_cycle = school.scheduled_billing_cycle
            scheduled_date = school.scheduled_billing_cycle_date
            school.billing_cycle = new_cycle
            school.price_per_seat = PackagePrices.get_price_per_seat(
                school.subscription_tier,
                new_cycle,
            )
            school.scheduled_billing_cycle = None
            school.scheduled_billing_cycle_date = None
            school.save()
            send_cycle_change_confirmation_email(school, new_cycle, scheduled_date)
            processed += 1
            continue

        # 4. Apply scheduled seat reduction (re-validate at apply time)
        reduction = getattr(school, "scheduled_seat_reduction", None)
        if reduction:
            seats_used = compute_seats_used(school.id)
            new_total = max(int(school.total_seats or 0) - int(reduction), 0)
            if new_total < seats_used:
                school.scheduled_seat_reduction = None
                school.scheduled_reduction_date = None
                school.save()
            else:
                school.total_seats = new_total
                school.scheduled_seat_reduction = None
                school.scheduled_reduction_date = None
                school.save()
            processed += 1

    return processed
