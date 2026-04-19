import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent

# Support both repository-level `.env` and `backend/.env` regardless of cwd.
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "45"))
