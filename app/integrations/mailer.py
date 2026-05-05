import requests
from globals import SMTP2GO_API_KEY

from flask import render_template



class Mailer(object):
    def __init__(self):
        self.api_key = SMTP2GO_API_KEY
        self.api_url = "https://api.smtp2go.com/v3/email/send"

    from app._shared.decorators import async_method

    def generate_email_text(self, template_name, context={}):
        return render_template(template_name, **context)

    @async_method
    def send_email(
        self,
        recipients,
        subject,
        text,
        sender="Preppee Support <support@wedidtech.com>",
        html=False,
    ):
        """
        Sends an email using the SMTP2GO API.

        :param sender: Email address of the sender
        :param recipient: Email address of the recipient
        :param subject: Subject of the email
        :param body: Body of the email (plain text or HTML)
        :param html: Boolean indicating if the body is HTML
        :return: Response from the SMTP2GO API
        """

        try:
            headers = {"accept": "application/json", "Content-Type": "application/json"}
            payload = {
                "api_key": self.api_key,
                "to": recipients,
                "sender": sender,
                "subject": subject,
                "text_body": text if not html else None,
                "html_body": text if html else None,
            }

            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to send email: {e}")
            return None


mailer = Mailer()


# Subscription-specific email notifications

def send_trial_expiry_email(school, seats_used: int):
    """Send email when trial expires and school has students > free limit.

    Email content:
    - Trial has expired
    - Downgraded to Free (10 seats)
    - Currently have {seats_used} students
    - Action required: Upgrade or deactivate students
    """
    if not school.email:
        return

    subject = f"Trial Expired - Action Required for {school.name}"
    text = f"""
Hello {school.name},

Your 30-day trial period has expired and your account has been downgraded to the Free tier (10 seats).

Current Status:
- Active Students: {seats_used}
- Free Tier Limit: 10 students
- Action Required: You have {seats_used - 10} students over the limit

What You Need to Do:
1. Upgrade to a Premium plan to continue with all students, OR
2. Deactivate {seats_used - 10} students to stay within the free limit

Upgrade now: https://app.preppee.online/settings/subscription

If you have any questions, please contact our support team.

Best regards,
The Preppee Team
"""

    try:
        mailer.send_email(
            recipients=[school.email],
            subject=subject,
            text=text,
        )
    except Exception as e:
        print(f"Failed to send trial expiry email to {school.email}: {e}")


def send_downgrade_confirmation_email(school, scheduled_date):
    """Email confirmation when downgrade scheduled"""
    if not school.email:
        return

    subject = f"Downgrade Scheduled - {school.name}"
    text = f"""
Hello {school.name},

Your downgrade to the Free tier has been scheduled.

Scheduled Date: {scheduled_date}

After downgrade:
- Your account will be limited to 10 students
- Some premium features will be disabled

If you change your mind, you can cancel this downgrade from your subscription settings.

Manage Subscription: https://app.preppee.online/settings/subscription

Best regards,
The Preppee Team
"""

    try:
        mailer.send_email(
            recipients=[school.email],
            subject=subject,
            text=text,
        )
    except Exception as e:
        print(f"Failed to send downgrade confirmation email to {school.email}: {e}")


def send_cycle_change_confirmation_email(school, new_cycle, scheduled_date):
    """Email confirmation when billing cycle change scheduled"""
    if not school.email:
        return

    subject = f"Billing Cycle Change Scheduled - {school.name}"
    text = f"""
Hello {school.name},

Your billing cycle change has been scheduled.

New Billing Cycle: {new_cycle.title()}
Effective Date: {scheduled_date}

This change will take effect at your next renewal. Your current subscription will continue until then.

If you have any questions, please contact our support team.

Manage Subscription: https://app.preppee.online/settings/subscription

Best regards,
The Preppee Team
"""

    try:
        mailer.send_email(
            recipients=[school.email],
            subject=subject,
            text=text,
        )
    except Exception as e:
        print(f"Failed to send cycle change confirmation email to {school.email}: {e}")
