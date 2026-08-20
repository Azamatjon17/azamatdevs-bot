"""Chiqarilgan postlar tarixi — mavzu takrorlanmasligi uchun."""
import json
from datetime import datetime, timedelta

from . import config


def load():
    try:
        return json.loads(config.HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save(entries):
    config.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.HISTORY_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def recent_titles(days=None):
    days = days or config.HISTORY_DAYS
    cutoff = datetime.now(config.TZ) - timedelta(days=days)
    out = []
    for e in load():
        try:
            when = datetime.fromisoformat(e["date"])
        except Exception:
            continue
        if when >= cutoff:
            out.append(f'{e.get("title", "")} — {e.get("topic", "")}')
    return out[-40:]


def published_today():
    today = datetime.now(config.TZ).date().isoformat()
    return any(e.get("date", "").startswith(today) and e.get("status") == "published"
               for e in load())


def add(topic, title, category, status, rewrites=0, qc_score=None):
    entries = load()
    entries.append({
        "date": datetime.now(config.TZ).isoformat(timespec="seconds"),
        "topic": topic,
        "title": title,
        "category": category,
        "status": status,
        "rewrites": rewrites,
        "qc_score": qc_score,
    })
    save(entries[-400:])
