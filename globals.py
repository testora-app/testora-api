import os
from dotenv import load_dotenv

load_dotenv()

SMTP2GO_API_KEY = os.getenv('SMTP2GO_API_KEY')
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')