
class SubscriptionPackages:
    free = 'free'
    premium = 'premium'


class PaymentStatus:
    pending = 'pending'
    success = 'success'
    failed  = 'failed'

class PackagePrices:
    prices = {
        SubscriptionPackages.free: 0,
        SubscriptionPackages.premium: 55
    }

    discount_threshold = 15 # number of students per threshold for discount of 10 cedis
    discount = 10
        
    @staticmethod
    def calculate_subscription_price(package, student_number):
        discount_groups = student_number // PackagePrices.discount_threshold
        total_discount = discount_groups * PackagePrices.discount
        
        charge = PackagePrices.prices[package] * student_number

        charge -= total_discount
        return charge 