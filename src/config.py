"""Barcha sozlamalar shu yerda. Maxfiy kalitlar faqat environment orqali."""
import os
import pathlib
from zoneinfo import ZoneInfo

# --- Maxfiy kalitlar (GitHub Secrets) ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "0") or 0)
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DS_ID = os.environ.get("NOTION_DS_ID", "")

# --- Kanal ---
CHANNEL = os.environ.get("CHANNEL", "@azamatdevs")

# --- Vaqt ---
TZ = ZoneInfo("Asia/Tashkent")
PUBLISH_AT = os.environ.get("PUBLISH_AT", "07:00")  # Toshkent vaqti, HH:MM

# --- Post qoidalari ---
CAPTION_LIMIT = 4096          # Telegram oddiy xabar chegarasi (rasm yo'q, sendMessage)
SAFETY_MARGIN = 24            # zaxira belgilar
MAX_CAPTION = CAPTION_LIMIT - SAFETY_MARGIN

HISTORY_DAYS = int(os.environ.get("HISTORY_DAYS", "60"))
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"

# --- Fayllar ---
ROOT = pathlib.Path(__file__).resolve().parent.parent
HISTORY_FILE = ROOT / "data" / "history.json"


def missing_secrets():
    out = []
    if not TELEGRAM_TOKEN:
        out.append("TELEGRAM_BOT_TOKEN")
    if not OWNER_CHAT_ID:
        out.append("OWNER_CHAT_ID")
    return out
