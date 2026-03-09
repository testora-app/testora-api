class Features:
    StudentLimit = "student_limit"
    SubjectsAllowedForBECE = "subjects_allowed_for_bece"
    StaffLimit = "staff_limit"
    TestHistoryLimit = "test_history_limit"
    ExamMode = "exam_mode"


class FeatureStatus:
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLIMITED = 100000


class SubscriptionPackages:
    # NOTE: These are user-facing values stored on School.subscription_package
    # (kept for backward compatibility with other parts of the app).
    free = "Free"
    premium = "Premium"
    premium_plus = "Premium Plus"


class TierNames:
    # Canonical internal identifiers for the new subscription manager
    trial = "trial"
    free = "free"
    premium = "premium"
    premium_plus = "premium_plus"


class BillingCycles:
    monthly = "monthly"
    termly = "termly"
    yearly = "yearly"


class PaymentStatus:
    pending = "pending"
    success = "success"
    failed = "failed"


class PackagePrices:
    """Legacy helper (kept for now).

    The new subscription manager uses seat-based billing with explicit billing
    cycles. The old implementation billed per-student and applied discounts.

    Some existing code paths (older billing history / tests) still import
    PackagePrices, so we keep this class but implement it on top of the new
    pricing rules.
    """

    # Prices are per-seat for the given billing cycle
    seat_prices = {
        TierNames.trial: {BillingCycles.monthly: 0, BillingCycles.termly: 0, BillingCycles.yearly: 0},
        TierNames.free: {BillingCycles.monthly: 0, BillingCycles.termly: 0, BillingCycles.yearly: 0},
        TierNames.premium: {
            BillingCycles.monthly: 75,
            BillingCycles.termly: 210,
            BillingCycles.yearly: 600,
        },
        TierNames.premium_plus: {
            BillingCycles.monthly: 110,
            BillingCycles.termly: 385,
            BillingCycles.yearly: 1100,
        },
    }

    @staticmethod
    def get_days_in_cycle(cycle: str) -> int:
        if cycle == BillingCycles.monthly:
            return 30
        if cycle == BillingCycles.termly:
            return 105
        if cycle == BillingCycles.yearly:
            return 365
        raise KeyError(f"Invalid billing cycle: {cycle}")

    @staticmethod
    def get_price_per_seat(tier: str, cycle: str) -> float:
        return float(PackagePrices.seat_prices[tier][cycle])

    @staticmethod
    def calculate_seat_total(tier: str, cycle: str, seats: int) -> float:
        return PackagePrices.get_price_per_seat(tier, cycle) * int(seats)

    @staticmethod
    def calculate_proration(tier: str, cycle: str, new_seats: int, end_date) -> float:
        """Prorated cost for adding seats mid-cycle.

        end_date is a datetime.date.
        """
        from datetime import datetime, timezone

        if new_seats <= 0:
            return 0

        today = datetime.now(timezone.utc).date()
        days_remaining = max((end_date - today).days, 0)
        days_in_cycle = PackagePrices.get_days_in_cycle(cycle)

        if days_in_cycle <= 0:
            return 0

        full = PackagePrices.calculate_seat_total(tier, cycle, new_seats)
        return float(full) * (float(days_remaining) / float(days_in_cycle))

    @staticmethod
    def calculate_subscription_price(package, student_number):
        """Deprecated: kept only to reduce breakage.

        Maps Free/Premium to new premium monthly per-seat pricing.
        """
        pkg = str(package or "").lower()
        if "free" in pkg:
            return 0
        # Assume premium monthly
        return PackagePrices.calculate_seat_total(TierNames.premium, BillingCycles.monthly, student_number)


class SubscriptionLimits:
    #TODO: remove the free and premium keys
    PackageLimits = {
        SubscriptionPackages.free: {
            Features.StudentLimit: 10,
            Features.StaffLimit: 2,
            Features.ExamMode: FeatureStatus.DISABLED,
            Features.SubjectsAllowedForBECE: ["RME", "Computing"],
            Features.TestHistoryLimit: 10,
        },
        SubscriptionPackages.premium: {
            Features.StudentLimit: FeatureStatus.UNLIMITED,
            Features.StaffLimit: FeatureStatus.UNLIMITED,
            Features.ExamMode: FeatureStatus.ENABLED,
            Features.SubjectsAllowedForBECE: FeatureStatus.UNLIMITED,
            Features.TestHistoryLimit: FeatureStatus.UNLIMITED,
        },
        'trial': {
            Features.StudentLimit: 100,
            Features.StaffLimit: FeatureStatus.UNLIMITED,
            Features.TestHistoryLimit: FeatureStatus.UNLIMITED,
            Features.ExamMode: FeatureStatus.ENABLED,
            Features.SubjectsAllowedForBECE: FeatureStatus.UNLIMITED,
        },
        'free': {
            Features.StudentLimit: 10,
            Features.StaffLimit: 2,
            Features.ExamMode: FeatureStatus.DISABLED,
            Features.SubjectsAllowedForBECE: ["RME", "Computing"],
            Features.TestHistoryLimit: 10,
        },
        'premium': {
            Features.StudentLimit: FeatureStatus.UNLIMITED,
            Features.StaffLimit: FeatureStatus.UNLIMITED,
            Features.ExamMode: FeatureStatus.ENABLED,
            Features.SubjectsAllowedForBECE: FeatureStatus.UNLIMITED,
            Features.TestHistoryLimit: FeatureStatus.UNLIMITED,
        },

    }

    @staticmethod
    def get_limits(package):
        return SubscriptionLimits.PackageLimits[package]


# Trial tier configuration
TRIAL_DEFAULT_SEATS = 100
TRIAL_DURATION_DAYS = 30

# Free tier configuration
FREE_DEFAULT_SEATS = 10
