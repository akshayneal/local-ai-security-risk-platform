import os

from dashboard.knowledge_workspace import knowledge_page

knowledge_page(os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
