import os
from dotenv import load_dotenv

load_dotenv()

SMTP2GO_API_KEY = os.getenv("SMTP2GO_API_KEY")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3050")
ONE_SIGNAL_APP_ID = os.getenv("ONE_SIGNAL_APP_ID")
ONE_SIGNAL_REST_API_KEY = os.getenv("ONE_SIGNAL_REST_API_KEY")
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")
PAYSTACK_API_KEY = os.getenv("PAYSTACK_API_KEY")
PAYSTACK_CALLBACK_URL = os.getenv("PAYSTACK_CALLBACK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")