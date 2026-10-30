import os

from dashboard.ai_security import ai_security_page

ai_security_page(os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
