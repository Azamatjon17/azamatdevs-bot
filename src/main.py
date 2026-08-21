"""Kunlik post pipeline: mavzu -> research -> yozish -> rasm -> QC -> tasdiq -> publish."""
import html
import os
import sys
import time
import traceback
from datetime import datetime, timedelta

from . import config, gemini, history, queue
from . import telegram_api as tg

KB = [
    [{"text": "✅ Chiqarish", "callback_data": "publish"}],
    [{"text": "✏️ Qayta yozish", "callback_data": "rewrite"}],
    [{"text": "🖼 Rasmni almashtir", "callback_data": "reimage"}],
    [{"text": "❌ Bugun chiqmasin", "callback_data": "cancel"}],
]


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


def fit(caption, allow_gemini=True):
    """1024 belgiga sig'dirish."""
    if allow_gemini:
        for _ in range(2):
            if len(caption) <= config.MAX_CAPTION:
                return caption
            log(f"caption {len(caption)} belgi — qisqartirilmoqda")
            caption = gemini.shorten(caption, config.MAX_CAPTION - 40)
    if len(caption) > config.MAX_CAPTION:
        caption = caption[: config.MAX_CAPTION - 1].rsplit(" ", 1)[0] + "…"
    return caption


def make_post(topic, angle, briefing, feedback=None, previous=None, post=None):
    """post berilsa (Notion navbatidan), Gemini umuman chaqirilmaydi — QC ham o'tkazib yuboriladi."""
    use_gemini = post is None
    if post is None:
        post = gemini.write_post(topic, angle, briefing, feedback, previous)
    caption = fit(build_caption(post), allow_gemini=use_gemini)

    if not use_gemini:
        return post, caption, {"verdict": "skip", "score": None, "issues": []}

    verdict = gemini.qc(caption, topic)
    log(f"QC: {verdict.get('verdict')} ({verdict.get('score')}) {verdict.get('issues')}")

    if verdict.get("verdict") == "fix" and verdict.get("fixed_caption"):
        caption = fit(verdict["fixed_caption"])
    elif verdict.get("verdict") == "reject":
        log("QC rad etdi — qayta yoziladi")
        issues = "; ".join(verdict.get("issues", []))
        post = gemini.write_post(topic, angle, briefing,
                                 feedback=f"QC rad etdi: {issues}", previous=caption)
        caption = fit(build_caption(post))
        verdict = gemini.qc(caption, topic)

    return post, caption, verdict


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


def wait_for_text(deadline, offset):
    """Izoh matnini kutadi."""
    while datetime.now(config.TZ) < deadline:
        for u in tg.get_updates(offset, timeout=20):
            offset = u["update_id"] + 1
            m = u.get("message") or {}
            if m.get("from", {}).get("id") == config.OWNER_CHAT_ID and m.get("text"):
                return m["text"], offset
        time.sleep(1)
    return None, offset


def send_draft(caption, image, rewrites, deadline, source):
    header = (
        f"📝 <b>Qoralama</b>"
        f"{f' (qayta yozish #{rewrites})' if rewrites else ''}\n"
        f"✍️ Manba: {source}\n"
        f"⏰ {deadline:%H:%M} da avtomatik chiqadi\n"
        f"📏 {len(caption)} / {config.CAPTION_LIMIT} belgi"
    )
    tg.send_message(config.OWNER_CHAT_ID, header)
    if image:
        return tg.send_photo(config.OWNER_CHAT_ID, image, caption, KB)
    return tg.send_message(config.OWNER_CHAT_ID, caption + "\n\n⚠️ <i>Rasm yaratilmadi</i>", KB)


def publish(caption, image):
    if image:
        return tg.send_photo(config.CHANNEL, image, caption)
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

    # 1. Navbat (Notion) yoki mavzu
    source = "Gemini"
    queued = queue.next_queued()
    topic = os.environ.get("TOPIC", "").strip()
    angle, category = "", "qo'lda"
    manual_post = None

    if queued:
        source = "Cowork"
        topic, category = queued["topic"], queued["category"]
        manual_post = {
            "title": queued["title"],
            "body": queued["body"],
            "hashtags": queued["hashtags"],
            "image_prompt": queued["image_prompt"],
        }
        log(f"Navbatdan olindi: {topic}")
    elif topic:
        log(f"Berilgan mavzu: {topic}")
    else:
        topic, angle, category = gemini.pick_topic(history.recent_titles())
        log(f"Tanlangan mavzu: {topic} | {angle}")

    # 2. Research (navbatdagi post uchun kerak emas)
    briefing = ""
    if not manual_post:
        briefing = gemini.research(topic, angle)
        log(f"Research tayyor ({len(briefing)} belgi)")

    # 3-4. Yozish + QC
    post, caption, verdict = make_post(topic, angle, briefing, post=manual_post)

    # 5. Rasm
    image = gemini.generate_image(post.get("image_prompt", topic))

    # 6. Tasdiqlash sikli
    rewrites = 0
    msg = send_draft(caption, image, rewrites, deadline, source)

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
            history.add(topic, post.get("title", ""), category, "cancelled", rewrites)
            return

        if action == "reimage":
            tg.answer_callback(cb["id"], "Yangi rasm…")
            tg.clear_keyboard(config.OWNER_CHAT_ID, msg["message_id"])
            new = gemini.generate_image(post.get("image_prompt", topic) + " Alternative composition.")
            image = new or image
            msg = send_draft(caption, image, rewrites, deadline, source)
            continue

        if action == "rewrite":
            if rewrites >= config.MAX_REWRITES:
                tg.answer_callback(cb["id"], "Qayta yozish limiti tugadi")
                continue
            tg.answer_callback(cb["id"], "Izohingizni yozing")
            tg.clear_keyboard(config.OWNER_CHAT_ID, msg["message_id"])
            tg.send_message(
                config.OWNER_CHAT_ID,
                "✏️ <b>Nimasi yoqmadi?</b>\nQisqacha yozing — masalan "
                "<i>«boshlanishi zerikarli»</i> yoki <i>«mavzuni o'zgartir»</i>.\n"
                "5 daqiqa javob bermasangiz, o'zim boshqacha yozaman.",
            )
            fb_deadline = min(deadline, datetime.now(config.TZ) + timedelta(minutes=5))
            feedback, offset = wait_for_text(fb_deadline, offset)
            log(f"Izoh: {feedback!r}")

            rewrites += 1
            if feedback and any(w in feedback.lower() for w in ("mavzu", "boshqa mavzu")):
                topic, angle, category = gemini.pick_topic(history.recent_titles() + [topic])
                briefing = gemini.research(topic, angle)
                log(f"Yangi mavzu: {topic}")

            source = "Gemini"
            post, caption, verdict = make_post(topic, angle, briefing,
                                               feedback=feedback, previous=caption)
            image = gemini.generate_image(post.get("image_prompt", topic)) or image
            msg = send_draft(caption, image, rewrites, deadline, source)
            continue

    # 7. Kutish va chiqarish
    while datetime.now(config.TZ) < deadline:
        time.sleep(min(30, (deadline - datetime.now(config.TZ)).total_seconds()))

    sent = publish(caption, image)
    log("Post kanalga chiqdi")

    if queued and not queue.mark_published(queued["page_id"]):
        tg.send_message(config.OWNER_CHAT_ID,
                         "⚠️ Post chiqdi, lekin Notion navbatidagi holatini yangilab bo'lmadi — "
                         "qo'lda \"Chiqdi\" deb belgilang, aks holda ertaga qayta chiqishi mumkin.")

    link = f"https://t.me/{config.CHANNEL.lstrip('@')}/{sent.get('message_id', '')}"
    tg.send_message(config.OWNER_CHAT_ID, f"✅ Post chiqdi\n{link}", preview=True)
    history.add(topic, post.get("title", ""), category, "published",
                rewrites, verdict.get("score"))


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
