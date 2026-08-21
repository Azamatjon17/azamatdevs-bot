# @azamatdevs — avtomatik post tizimi

Har kuni ertalab: Notion'dagi post navbatidan eng eski "Navbatda" yozuv
olinadi → dasturiy tekshiruvdan o'tadi → sizga tasdiqlashga yuboriladi →
07:00 da kanalga chiqadi. Postlarni Cowork (yoki siz qo'lda) Notion'ga
oldindan tayyorlab qo'yadi — bu skriptning o'zi hech qanday AI chaqirmaydi.

## Kunlik oqim

| Vaqt (Toshkent) | Nima bo'ladi |
|---|---|
| 06:10 | Ishga tushadi: Notion navbatidan post oladi, tekshiradi |
| ~06:11 | Sizga botga qoralama keladi, 3 ta tugma bilan |
| 06:11–07:00 | Siz ko'rib chiqasiz. Javob bermasangiz ham post chiqadi |
| 07:00 | Kanalga chiqadi, sizga havola keladi |

Navbat bo'sh bo'lsa — botga «📭 Navbat bo'sh» xabari keladi, bugun post
chiqmaydi.

**Tugmalar:** ✅ Chiqarish · 📝 Tahrirlash (Notion'da "Qoralama"ga
o'tkazadi, tuzatib "Navbatda"ga qaytarasiz) · ❌ Bugun chiqmasin

---

## O'rnatish

### 1. Bot tokenini yangilang
@BotFather → `/mybots` → `@azamatjon_ai_bot` → *API Token* → **Revoke current token**.
Yangi tokenni hech kimga ko'rsatmang.

### 2. Botni kanalga admin qiling
@azamatdevs → *Administrators* → *Add Admin* → `@azamatjon_ai_bot` →
**Post Messages** huquqini yoqing.

### 3. Notion integratsiyasini yarating
notion.so/my-integrations → *New integration* → nom bering → Save →
*Internal Integration Secret* ni nusxalang. Post navbati bazasini oching →
⋯ → *Connections* → shu integratsiyani qo'shing (bu qadam eng ko'p unutiladi).

### 4. Secrets va Variables qo'shing
Repo → *Settings* → *Secrets and variables* → *Actions*:

| Joy | Nomi | Qiymati |
|---|---|---|
| Secrets | `TELEGRAM_BOT_TOKEN` | 1-qadamdagi yangi token |
| Secrets | `OWNER_CHAT_ID` | pastdagi 5-qadamda olasiz |
| Secrets | `NOTION_TOKEN` | 3-qadamdagi integratsiya kaliti |
| Variables | `NOTION_DS_ID` | Post navbati bazasining data source ID'si |

### 5. Chat ID'ni aniqlang
Eng oson yo'l: Telegram'da **@userinfobot** ga `/start` yozing — u sizga ID beradi.

### 6. Sinab ko'ring
Notion'da navbatga "Navbatda" holatida bitta post qo'ying, so'ng
Repo → *Actions* → *Kunlik post* → **Run workflow**.

> Sinovda post darhol emas, keyingi `PUBLISH_AT` vaqtida chiqadi. Darhol
> ko'rish uchun repo *Variables* bo'limiga `PUBLISH_AT` = hozirgi vaqtdan
> 5-10 daqiqa keyingi soatni qo'ying, sinab bo'lgach `07:00` ga qaytaring.

### 7. Avtomatik rejim
Hech narsa qilish shart emas — cron o'zi ertalab ishga tushadi. Faqat
navbatni bo'sh qoldirmang, aks holda o'sha kuni post chiqmaydi.

---

## Vaqtni o'zgartirish
Repo → *Settings* → *Variables* → `PUBLISH_AT` = `08:00`.
Cron vaqtini ham `.github/workflows/daily_post.yml` da mos ravishda suring
(UTC = Toshkent − 5 soat).

---

## Nosozliklar

**Qoralama kelmadi** → Actions'dagi log'ni oching. Xatolik bo'lsa bot sizga
xabar yuborishi ham kerak.

**"chat not found"** → `OWNER_CHAT_ID` noto'g'ri, yoki siz botga hali `/start`
yozmagansiz.

**"not enough rights"** → bot kanalda admin emas yoki *Post Messages* o'chiq.

**`[navbat] Notion so'rovi muvaffaqiyatsiz`** → `NOTION_TOKEN` yoki
`NOTION_DS_ID` noto'g'ri, yoki integratsiya bazaga ulanmagan (3-qadam).

**📭 Navbat bo'sh** → Notion'da "Navbatda" holatida hech narsa yo'q.

---

## Fayllar

```
src/config.py        sozlamalar
src/queue.py          Notion navbati bilan ishlash
src/telegram_api.py  Telegram
src/history.py       tarix va "bugun chiqdimi" tekshiruvi
src/main.py          umumiy oqim
```
