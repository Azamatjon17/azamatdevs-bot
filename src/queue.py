"""Notion navbatidan tayyor post olish va holatini yangilash."""
from datetime import datetime, timezone

import requests

from . import config

API = "https://api.notion.com/v1"
VERSION = "2025-09-03"


def _headers():
    return {
        "Authorization": f"Bearer {config.NOTION_TOKEN}",
        "Notion-Version": VERSION,
        "Content-Type": "application/json",
    }


def _plain_text(rich_text):
    return "".join(t.get("plain_text", "") for t in rich_text).strip()


def next_queued():
    """Navbatdagi eng eski 'Navbatda' postni qaytaradi, bo'lmasa yoki xato bo'lsa None."""
    if not config.NOTION_TOKEN or not config.NOTION_DS_ID:
        return None

    body = {
        "filter": {"property": "Holat", "select": {"equals": "Navbatda"}},
        "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
        "page_size": 1,
    }
    try:
        r = requests.post(
            f"{API}/data_sources/{config.NOTION_DS_ID}/query",
            headers=_headers(), json=body, timeout=30,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
    except requests.RequestException as e:
        print(f"[navbat] Notion so'rovi muvaffaqiyatsiz: {e}")
        return None

    if not results:
        return None

    props = results[0]["properties"]
    hashtags_raw = _plain_text(props["Hashteglar"]["rich_text"])

    return {
        "page_id": results[0]["id"],
        "title": _plain_text(props["Sarlavha"]["title"]),
        "body": _plain_text(props["Matn"]["rich_text"]),
        "hashtags": [h for h in hashtags_raw.split() if h],
        "image_prompt": _plain_text(props["Rasm prompti"]["rich_text"]),
        "topic": _plain_text(props["Mavzu"]["rich_text"]),
        "category": (props["Kategoriya"].get("select") or {}).get("name", ""),
    }


def mark_published(page_id):
    """Postni 'Chiqdi' deb belgilaydi. Xato bo'lsa False qaytaradi, yiqilmaydi."""
    body = {
        "properties": {
            "Holat": {"select": {"name": "Chiqdi"}},
            "Chiqarilgan sana": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        }
    }
    try:
        r = requests.patch(f"{API}/pages/{page_id}", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[navbat] Holatni yangilab bo'lmadi: {e}")
        return False
