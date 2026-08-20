"""Telegram Bot API bilan ishlash."""
import time

import requests

from . import config


class TelegramError(RuntimeError):
    pass


def _api(method, **kwargs):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/{method}"
    files = kwargs.pop("files", None)
    for attempt in range(3):
        try:
            if files:
                r = requests.post(url, data=kwargs, files=files, timeout=120)
            else:
                r = requests.post(url, json=kwargs, timeout=60)
            data = r.json()
            if data.get("ok"):
                return data["result"]
            desc = data.get("description", "")
            if "retry after" in desc.lower():
                time.sleep(int(data.get("parameters", {}).get("retry_after", 5)) + 1)
                continue
            raise TelegramError(f"{method}: {desc}")
        except requests.RequestException as e:
            if attempt == 2:
                raise TelegramError(f"{method}: {e}")
            time.sleep(3)
    raise TelegramError(f"{method}: takrorlash tugadi")


def send_photo(chat_id, photo_bytes, caption, keyboard=None):
    kw = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
    if keyboard:
        import json as _j
        kw["reply_markup"] = _j.dumps({"inline_keyboard": keyboard})
    return _api("sendPhoto", files={"photo": ("post.png", photo_bytes, "image/png")}, **kw)


def send_message(chat_id, text, keyboard=None, preview=False):
    kw = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": not preview},
    }
    if keyboard:
        kw["reply_markup"] = {"inline_keyboard": keyboard}
    return _api("sendMessage", **kw)


def edit_caption(chat_id, message_id, caption):
    return _api("editMessageCaption", chat_id=chat_id, message_id=message_id,
                caption=caption, parse_mode="HTML")


def clear_keyboard(chat_id, message_id):
    try:
        _api("editMessageReplyMarkup", chat_id=chat_id, message_id=message_id,
             reply_markup={"inline_keyboard": []})
    except TelegramError:
        pass


def answer_callback(cb_id, text=""):
    try:
        _api("answerCallbackQuery", callback_query_id=cb_id, text=text)
    except TelegramError:
        pass


def get_updates(offset=None, timeout=25):
    kw = {"timeout": timeout, "allowed_updates": ["message", "callback_query"]}
    if offset is not None:
        kw["offset"] = offset
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getUpdates"
    try:
        r = requests.post(url, json=kw, timeout=timeout + 15)
        data = r.json()
        return data.get("result", []) if data.get("ok") else []
    except requests.RequestException:
        return []


def drain(offset=None):
    """Eski update'larni tashlab, keyingi offset'ni qaytaradi."""
    ups = get_updates(offset, timeout=0)
    return (ups[-1]["update_id"] + 1) if ups else offset
