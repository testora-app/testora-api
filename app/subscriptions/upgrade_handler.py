from datetime import datetime, timezone, timedelta

from app.subscriptions.constants import PackagePrices, SubscriptionPackages, TierNames


def handle_successful_upgrade(school, tier: str, billing_cycle: str, seats: int) -> None:
    """Apply a confirmed upgrade payment to a school.

    Trial schools: expiry = trial_expiry + cycle_days  (trial benefit preserved)
    Free/other:    expiry = today + cycle_days
    Clears all scheduled flags.
    """
    cycle_days = PackagePrices.get_days_in_cycle(billing_cycle)
    today = datetime.now(timezone.utc).date()

    paid_tiers = (TierNames.trial, TierNames.premium, TierNames.premium_plus)
    if (
        school.subscription_tier in paid_tiers
        and school.subscription_expiry_date
        and school.subscription_expiry_date > today
    ):
        new_expiry = school.subscription_expiry_date + timedelta(days=cycle_days)
    else:
        new_expiry = today + timedelta(days=cycle_days)

    school.subscription_tier = tier
    school.billing_cycle = billing_cycle
    school.price_per_seat = PackagePrices.get_price_per_seat(tier, billing_cycle)
    school.total_seats = int(seats)
    school.subscription_expiry_date = new_expiry
    school.subscription_package = SubscriptionPackages.premium

    school.scheduled_downgrade = False
    school.scheduled_downgrade_date = None
    school.scheduled_billing_cycle = None
    school.scheduled_billing_cycle_date = None
    school.scheduled_seat_reduction = None
    school.scheduled_reduction_date = None

    school.save()
