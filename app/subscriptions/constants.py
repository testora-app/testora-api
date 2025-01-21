class Features:
    StudentLimit = "student_limit"
    SubjectsAllowedForBECE = "subjects_allowed_for_bece"
    StaffLimit = "staff_limit"
    TestHistoryLimit = "test_history_limit"
    ExamMode = "exam_mode"


class FeatureStatus:
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLIMITED = "unlimited"


class SubscriptionPackages:
    free = "free"
    premium = "premium"


class PaymentStatus:
    pending = "pending"
    success = "success"
    failed = "failed"


class PackagePrices:
    prices = {SubscriptionPackages.free: 0, SubscriptionPackages.premium: 55}

    discount_threshold = 15  # number of students per threshold for discount of 10 cedis
    discount = 10

    @staticmethod
    def calculate_subscription_price(package, student_number):
        discount_groups = student_number // PackagePrices.discount_threshold
        total_discount = discount_groups * PackagePrices.discount

        charge = PackagePrices.prices[package] * student_number

        charge -= total_discount
        return charge


class SubscriptionLimits:
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
    }

    @staticmethod
    def get_limits(package):
        return SubscriptionLimits.PackageLimits[package]
