"""Kunlik post pipeline: Notion navbatidan post olish -> tekshiruv -> tasdiq -> publish."""
import html
import os
import re
import sys
import time
import traceback
from datetime import datetime, timedelta

from . import config, history, queue
from . import telegram_api as tg

KB = [
    [{"text": "✅ Chiqarish", "callback_data": "publish"}],
    [{"text": "📝 Tahrirlash", "callback_data": "edit"}],
    [{"text": "❌ Bugun chiqmasin", "callback_data": "cancel"}],
]

CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")


def log(msg):
    print(f"[{datetime.now(config.TZ):%H:%M:%S}] {msg}", flush=True)


def publish_deadline():
    now = datetime.now(config.TZ)
    hh, mm = (int(x) for x in config.PUBLISH_AT.split(":"))
    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if target < now:
        target = now + timedelta(minutes=2)
    return target


def build_caption(post):
    title = html.escape(post.get("title", "").strip())
    body = html.escape(post.get("body", "").strip())
    tags = " ".join(post.get("hashtags", []))
    return f"<b>{title}</b>\n\n{body}\n\n{tags}".strip()


def check_issues(post, caption):
    """Alohida AI QC yo'q — dasturiy tekshiruv. Bloklamaydi, faqat ogohlantiradi."""
    issues = []
    if not post.get("title", "").strip():
        issues.append("sarlavha yo'q")
    if not post.get("hashtags"):
        issues.append("hashteg yo'q")
    if len(caption) > config.MAX_CAPTION:
        issues.append(f"{len(caption)} belgi — {config.MAX_CAPTION} dan oshgan")
    if CYRILLIC_RE.search(post.get("title", "") + post.get("body", "")):
        issues.append("kirill harfi topildi")
    return issues


def send_draft(caption, deadline, source, issues):
    header = (
        f"📝 <b>Qoralama</b>\n"
        f"✍️ Manba: {source}\n"
        f"⏰ {deadline:%H:%M} da avtomatik chiqadi\n"
        f"📏 {len(caption)} / {config.MAX_CAPTION} belgi"
    )
    if issues:
        header += "\n⚠️ " + "; ".join(issues)
    tg.send_message(config.OWNER_CHAT_ID, header)
    return tg.send_message(config.OWNER_CHAT_ID, caption, KB)


def publish(caption):
    return tg.send_message(config.CHANNEL, caption)


def run():
    missing = config.missing_secrets()
    if missing:
        sys.exit(f"Secrets yetishmayapti: {', '.join(missing)}")

    if history.published_today() and not os.environ.get("FORCE"):
        log("Bugun post allaqachon chiqqan. Chiqildi.")
        return

    deadline = publish_deadline()
    offset = tg.drain()

    queued = queue.next_queued()
    if not queued:
        tg.send_message(config.OWNER_CHAT_ID, "📭 Navbat bo'sh — bugun post chiqmaydi.")
        log("Navbat bo'sh.")
        return

    topic, category = queued["topic"], queued["category"]
    post = {
        "title": queued["title"],
        "body": queued["body"],
        "hashtags": queued["hashtags"],
    }
    log(f"Navbatdan olindi: {topic}")

    caption = build_caption(post)
    issues = check_issues(post, caption)
    if issues:
        log(f"Tekshiruv: {'; '.join(issues)}")

    msg = send_draft(caption, deadline, "Cowork", issues)

    while True:
        action, cb, offset = wait_for_click(deadline, offset)

        if action in ("timeout", "publish"):
            if cb:
                tg.answer_callback(cb["id"], "Chiqarilmoqda…")
                tg.clear_keyboard(config.OWNER_CHAT_ID, msg["message_id"])
            else:
                log("Javob bo'lmadi — avtomatik chiqarilmoqda")
            break

        if action == "cancel":
            tg.answer_callback(cb["id"], "Bekor qilindi")
            tg.clear_keyboard(config.OWNER_CHAT_ID, msg["message_id"])
            tg.send_message(config.OWNER_CHAT_ID, "❌ Bugun post chiqmadi.")
            history.add(topic, post.get("title", ""), category, "cancelled")
            return

        if action == "edit":
            tg.answer_callback(cb["id"], "Tahrirlashga yuborildi")
            tg.clear_keyboard(config.OWNER_CHAT_ID, msg["message_id"])
            queue.mark_draft(queued["page_id"])
            tg.send_message(
                config.OWNER_CHAT_ID,
                "📝 Notion'da \"Qoralama\" holatiga o'tkazildi.\n"
                "Tuzatib, Holatni yana \"Navbatda\"ga qaytaring — ertaga chiqadi.",
            )
            history.add(topic, post.get("title", ""), category, "editing")
            return

    while datetime.now(config.TZ) < deadline:
        time.sleep(min(30, (deadline - datetime.now(config.TZ)).total_seconds()))

    sent = publish(caption)
    log("Post kanalga chiqdi")

    if not queue.mark_published(queued["page_id"]):
        tg.send_message(config.OWNER_CHAT_ID,
                         "⚠️ Post chiqdi, lekin Notion navbatidagi holatini yangilab bo'lmadi — "
                         "qo'lda \"Chiqdi\" deb belgilang, aks holda ertaga qayta chiqishi mumkin.")

    link = f"https://t.me/{config.CHANNEL.lstrip('@')}/{sent.get('message_id', '')}"
    tg.send_message(config.OWNER_CHAT_ID, f"✅ Post chiqdi\n{link}", preview=True)
    history.add(topic, post.get("title", ""), category, "published")


def wait_for_click(deadline, offset):
    """Tugma bosilishini kutadi. (action, callback, offset) qaytaradi."""
    while datetime.now(config.TZ) < deadline:
        for u in tg.get_updates(offset, timeout=20):
            offset = u["update_id"] + 1
            cb = u.get("callback_query")
            if cb and cb.get("from", {}).get("id") == config.OWNER_CHAT_ID:
                return cb.get("data"), cb, offset
        time.sleep(1)
    return "timeout", None, offset


def main():
    try:
        run()
    except Exception:
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        if config.TELEGRAM_TOKEN and config.OWNER_CHAT_ID:
            try:
                tg.send_message(config.OWNER_CHAT_ID,
                                f"🚨 <b>Xatolik</b>\n<pre>{html.escape(tb[-1500:])}</pre>")
            except Exception:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
