import os

from dashboard.workflows import workflow_page

workflow_page(os.getenv("API_BASE_URL", "http://127.0.0.1:8000"), soc=False)
