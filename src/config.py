"""Barcha sozlamalar shu yerda. Maxfiy kalitlar faqat environment orqali."""
import os
from zoneinfo import ZoneInfo

# --- Maxfiy kalitlar (GitHub Secrets) ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "0") or 0)
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DS_ID = os.environ.get("NOTION_DS_ID", "")

# --- Kanal ---
CHANNEL = os.environ.get("CHANNEL", "@azamatdevs")

# --- Vaqt ---
TZ = ZoneInfo("Asia/Tashkent")
PUBLISH_AT = os.environ.get("PUBLISH_AT", "07:00")  # Toshkent vaqti, HH:MM

# --- Modellar ---
TEXT_MODEL = os.environ.get("TEXT_MODEL", "gemini-3.6-flash")
IMAGE_MODELS = [
    m.strip() for m in
    os.environ.get("IMAGE_MODELS", "gemini-2.5-flash-image,gemini-2.0-flash-preview-image-generation").split(",")
    if m.strip()
]

# --- Post qoidalari ---
CAPTION_LIMIT = 1024          # Telegram caption qat'iy chegarasi
SAFETY_MARGIN = 24            # zaxira belgilar
MAX_CAPTION = CAPTION_LIMIT - SAFETY_MARGIN

LENGTH_MODES = {
    "short":  (55, 80),       # qisqa fikr / kuzatuv
    "normal": (100, 120),     # asosiy rejim
}

MAX_REWRITES = int(os.environ.get("MAX_REWRITES", "3"))
HISTORY_DAYS = int(os.environ.get("HISTORY_DAYS", "60"))
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"

# --- Fayllar ---
import pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
HISTORY_FILE = ROOT / "data" / "history.json"
RULES_FILE = ROOT / "rules.md"
SAMPLES_FILE = ROOT / "samples.md"


def missing_secrets():
    out = []
    if not TELEGRAM_TOKEN:
        out.append("TELEGRAM_BOT_TOKEN")
    if not GEMINI_KEY:
        out.append("GEMINI_API_KEY")
    if not OWNER_CHAT_ID:
        out.append("OWNER_CHAT_ID")
    return out
