import requests
from globals import PAYSTACK_API_KEY, PAYSTACK_CALLBACK_URL


class Paystack(object):
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.paystack.co"

    def create_payment(self, email, amount, callback_url=PAYSTACK_CALLBACK_URL):
        data = {
            "email": email,
            "amount": amount * 100,  # so we get amount in peswes
            "callback_url": callback_url,
        }
        url = f"{self.base_url}/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def verify_payment(self, ref):
        url = f"{self.base_url}/transaction/verify/{ref}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)
        return response.json()

    def get_payment(self, ref):
        url = f"{self.base_url}/transaction/{ref}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)
        return response.json()


paystack = Paystack(api_key=PAYSTACK_API_KEY)
