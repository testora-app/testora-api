import requests
from globals import SMTP2GO_API_KEY

class Mailer(object):
    def __init__(self):
        self.api_key = SMTP2GO_API_KEY
        self.api_url = 'https://api.smtp2go.com/v3/email/send'

    def send_email(self, recipients, subject, text, sender='Preppee Support <support@wedidtech.com>', html=False):
        """
        Sends an email using the SMTP2GO API.

        :param sender: Email address of the sender
        :param recipient: Email address of the recipient
        :param subject: Subject of the email
        :param body: Body of the email (plain text or HTML)
        :param html: Boolean indicating if the body is HTML
        :return: Response from the SMTP2GO API
        """

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            'api_key': self.api_key,
            'to': recipients,
            'sender': sender,
            'subject': subject,
            'text_body': text if not html else None,
            'html_body': text if html else None
        }

        response = requests.post(self.api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    

mailer = Mailer()