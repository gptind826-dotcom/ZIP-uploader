"""
Application configuration.
Loads environment variables and provides defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ─────────────────────────────────────────
API_ID: int = int(os.getenv("API_ID", "0"))
API_HASH: str = os.getenv("API_HASH", "")
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
SESSION_STRING: str = os.getenv("SESSION_STRING", "")

# ── Dashboard / Flask ───────────────────────────────
SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-me")
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
DASHBOARD_HOST: str = os.getenv("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", "5000"))

# ── Paths ────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
DB_PATH = os.path.join(BASE_DIR, "database", "bot.db")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ── Bot metadata ─────────────────────────────────────
DEVELOPER = "@EXUCODR"
