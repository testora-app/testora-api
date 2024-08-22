import os
from dotenv import load_dotenv

load_dotenv()

SMTP2GO_API_KEY = os.getenv('SMTP2GO_API_KEY')
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')
ONE_SIGNAL_APP_ID = os.getenv('ONE_SIGNAL_APP_ID')
ONE_SIGNAL_REST_API_KEY = os.getenv('ONE_SIGNAL_REST_API_KEY')