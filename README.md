# @azamatdevs — avtomatik post tizimi

Har kuni ertalab bitta post: mavzu topiladi → internetdan tekshiriladi → sizning
uslubingizda yoziladi → rasm yaratiladi → sifat nazoratidan o'tadi → sizga
tasdiqlashga yuboriladi → 07:00 da kanalga chiqadi.

## Kunlik oqim

| Vaqt (Toshkent) | Nima bo'ladi |
|---|---|
| 06:10 | Ishga tushadi: mavzu → research → matn → rasm → QC |
| ~06:20 | Sizga botga qoralama keladi, 4 ta tugma bilan |
| 06:20–07:00 | Siz ko'rib chiqasiz. Javob bermasangiz ham post chiqadi |
| 07:00 | Kanalga chiqadi, sizga havola keladi |

**Tugmalar:** ✅ Chiqarish · ✏️ Qayta yozish (izohingiz bilan, 3 martagacha) ·
🖼 Rasmni almashtir · ❌ Bugun chiqmasin

---

## O'rnatish — 8 qadam

### 1. Bot tokenini yangilang
@BotFather → `/mybots` → `@azamatjon_ai_bot` → *API Token* → **Revoke current token**.
Yangi tokenni hech kimga ko'rsatmang.

### 2. Botni kanalga admin qiling
@azamatdevs → *Administrators* → *Add Admin* → `@azamatjon_ai_bot` →
**Post Messages** huquqini yoqing.

### 3. Gemini kalitini oling
https://aistudio.google.com/apikey → *Create API key*.

### 4. GitHub'da repo yarating
github.com → *New repository* → nomi `azamatdevs-bot` → **Public**
(public bo'lsa Actions daqiqalari cheksiz va bepul; private'da oyiga 2000 daqiqa
chegara bor, bizga ~1000 kerak — ikkalasi ham yetadi).

Shu papkadagi barcha fayllarni repo'ga yuklang.

### 5. Secrets qo'shing
Repo → *Settings* → *Secrets and variables* → *Actions* → *New repository secret*:

| Nomi | Qiymati |
|---|---|
| `TELEGRAM_BOT_TOKEN` | 1-qadamdagi yangi token |
| `GEMINI_API_KEY` | 3-qadamdagi kalit |
| `OWNER_CHAT_ID` | 6-qadamda olasiz |

### 6. Chat ID'ni aniqlang
Eng oson yo'l: Telegram'da **@userinfobot** ga `/start` yozing — u sizga ID beradi.

Yoki kompyuterda:
```bash
pip install requests
export TELEGRAM_BOT_TOKEN="yangi_token"
# @azamatjon_ai_bot ga /start yozing, keyin:
python -m src.whoami
```

### 7. Sinab ko'ring
Repo → *Actions* → *Kunlik post* → **Run workflow** → *Mavzu* maydoniga
masalan `Deadline'ga amal qilish nega muhim` yozing → *Run*.

Bir-ikki daqiqada botga qoralama kelishi kerak.

> Sinovda post darhol emas, keyingi 07:00 da chiqadi. Darhol ko'rish uchun
> repo *Variables* bo'limiga `PUBLISH_AT` = hozirgi vaqtdan 5 daqiqa keyingi
> soatni qo'ying, sinab bo'lgach `07:00` ga qaytaring.

### 8. Avtomatik rejimni yoqing
Hech narsa qilish shart emas — cron o'zi ertalab ishga tushadi.
Faqat repo 60 kun harakatsiz qolsa GitHub cron'ni to'xtatadi, shuning uchun
oyda bir marta biror faylni tahrirlab qo'ying (yoki har kuni post chiqib
tarix commit bo'lgani uchun bu muammo bo'lmaydi).

---

## Kundalik ishlatish

### Mavzuni o'zingiz berish
Actions → *Kunlik post* → *Run workflow* → mavzuni yozing.
Masalan: `Bugun Docker volumes'ni o'rgandim` yoki `Aytilgan gapga javob berish`.

### Uslubni yaxshilash
`samples.md` fayliga o'zingizga yoqqan postlarni qo'shib boring.
Har bir yangi namuna agentni aniqroq qiladi.

### Yangi qoida qo'shish
`rules.md` faylining oxiriga yozing. Masalan:
```
17. "Do'stlar" so'zini ishlatmasin, "azizlar" desin.
18. Har postda kamida bitta amaliy maslahat bo'lsin.
```
QC agent ertasi kunidan boshlab shu qoidani tekshiradi.

### Vaqtni o'zgartirish
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

**Rasm chiqmayapti** → Gemini'ning rasm modeli bepul tarifda cheklangan bo'lishi
mumkin. Bu holda post rasmsiz chiqadi va sizga ogohlantirish keladi.
`IMAGE_MODELS` variable orqali boshqa model nomini sinab ko'rish mumkin.

**Post 1024 belgidan oshdi** → tizim o'zi qisqartiradi, aralashish shart emas.

---

## Fayllar

```
src/config.py        sozlamalar
src/style.py         uslub yo'riqnomasi va prompt'lar  ← eng muhim fayl
src/gemini.py        Gemini chaqiruvlari
src/telegram_api.py  Telegram
src/history.py       mavzu takrorlanmasligi uchun tarix
src/main.py          umumiy oqim
samples.md           sizning post namunalaringiz    ← to'ldirib boring
rules.md             sifat nazorati qoidalari       ← to'ldirib boring
```
