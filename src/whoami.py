"""Chat ID'ni aniqlash. Botga /start yozing, keyin: python -m src.whoami"""
from . import config, telegram_api as tg

if not config.TELEGRAM_TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN yo'q")

ups = tg.get_updates(timeout=0)
if not ups:
    print("Update yo'q. Botga /start yozing va qayta ishga tushiring.")
for u in ups:
    m = u.get("message") or {}
    frm = m.get("from") or {}
    if frm:
        print(f"OWNER_CHAT_ID = {frm.get('id')}   ({frm.get('first_name')} @{frm.get('username')})")
