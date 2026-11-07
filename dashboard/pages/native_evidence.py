import os

from dashboard.native_evidence import native_evidence_page

native_evidence_page(os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
