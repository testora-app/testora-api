import requests


class Paystack:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.paystack.co"

    def create_payment(self, data):
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