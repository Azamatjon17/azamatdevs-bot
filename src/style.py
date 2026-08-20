"""Agentlar uchun prompt'lar. Uslub yo'riqnomasi shu yerda."""
from . import config


def _read(path, fallback=""):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return fallback


def samples():
    return _read(config.SAMPLES_FILE)


def rules():
    return _read(config.RULES_FILE)


VOICE = """
You write Telegram posts in UZBEK (Latin script) for the channel @azamatdevs.
The author is a young Uzbek developer who writes about programming, business,
personal growth and things he learns day to day.

AUTHOR'S VOICE — imitate this precisely:
- First person, warm, sincere, talking to friends. Never corporate, never academic.
- Structure: personal observation or small story -> the thought it triggered ->
  a practical or moral takeaway -> a closing line aimed at the reader.
- Short sentences. One idea per sentence.
- Sometimes opens with "Assalomu alaykum azizlar!" — use it in maybe 1 of 4 posts, not always.
- If a foreign-language quote is used, always give the Uzbek translation in parentheses
  right after it. This is a signature move of the author.
- Emphasis words the author likes: "juda muhim", "zarur", "achinarli", "haqiqatan ham".
- 2-4 emojis maximum in the whole post, placed naturally, not on every line.

SPELLING: the author sometimes misspells words. YOU MUST WRITE CORRECT UZBEK
ORTHOGRAPHY (muhim, ta'sir, mas'uliyat, o', g') while keeping his casual TONE.
Do not make the text formal or bookish — only fix the spelling.

FORBIDDEN: obscene / indecent / suggestive content of any kind. Deep discussion of
religion or politics (surface mention only). Advertising or link-baiting.
""".strip()


def topic_prompt(recent_titles):
    recent = "\n".join(f"- {t}" for t in recent_titles) or "- (hali post yo'q)"
    return f"""Use Google Search to find ONE fresh, genuinely interesting topic for today's
post on an Uzbek-language Telegram channel about programming, business, personal
growth and learning.

Good topics: a new dev tool or practice worth knowing, a business/productivity idea
with real substance, a research finding about learning or habits, a concrete
engineering lesson. Prefer something published or discussed in the last 30 days.

Avoid anything close to these already-published topics:
{recent}

Return ONLY valid JSON, no markdown fences:
{{"topic": "<topic in Uzbek, one short sentence>",
  "angle": "<the specific angle or hook, in Uzbek, one sentence>",
  "category": "<dasturlash|biznes|shaxsiy rivojlanish|bilim>"}}"""


def research_prompt(topic, angle=""):
    return f"""Use Google Search. Research this topic thoroughly for a short Telegram post:

TOPIC: {topic}
ANGLE: {angle}

Return a compact briefing in Uzbek:
1. 3-5 concrete facts, each with the source name.
2. Any specific numbers, dates or names — only if you actually found them in a source.
   If you are not certain of a number, say "aniq raqam topilmadi" instead of guessing.
3. One counter-argument or nuance most people miss.
4. Why this matters to a young Uzbek developer or entrepreneur.

Be factual. Do not invent statistics. Maximum 300 words."""


def write_prompt(topic, angle, research, feedback=None, previous=None):
    short_lo, short_hi = config.LENGTH_MODES["short"]
    norm_lo, norm_hi = config.LENGTH_MODES["normal"]

    fb = ""
    if feedback:
        fb = f"""
IMPORTANT — the author rejected the previous draft. His feedback:
"{feedback}"

Previous draft was:
{previous}

Rewrite completely addressing his feedback. Do not repeat the same mistake.
"""

    return f"""{VOICE}

--- AUTHOR'S OWN POSTS (imitate rhythm, sentence length, structure) ---
{samples()}
--- END SAMPLES ---

--- QUALITY RULES ---
{rules()}
--- END RULES ---

TODAY'S TOPIC: {topic}
ANGLE: {angle}

RESEARCH BRIEFING:
{research}
{fb}
LENGTH — pick one and respect it strictly:
- "short": {short_lo}-{short_hi} words. Use for a single sharp observation or thought.
- "normal": {norm_lo}-{norm_hi} words. Use for a topic that needs a story plus a lesson.
Default to "normal" about 70% of the time.

HARD LIMIT: title + body + hashtags together must stay under 950 characters.
Count characters, not words. Uzbek words are long — be disciplined.

Write the post. Return ONLY valid JSON, no markdown fences:
{{"title": "<3-7 words, no emoji inside, no hashtag>",
  "body": "<the post text; use \\n\\n between paragraphs; 2-4 emojis total>",
  "hashtags": ["#tag1", "#tag2"],
  "length_mode": "short|normal",
  "image_prompt": "<English prompt for an illustration, see below>"}}

IMAGE PROMPT RULES: describe a clean, modern, minimal illustration that matches the
post's idea metaphorically. Warm muted palette. Flat vector or soft 3D style.
Absolutely NO text, NO letters, NO numbers anywhere in the image. No real people's
faces. No logos. Landscape orientation."""


def qc_prompt(caption, topic):
    return f"""You are a strict quality controller for an Uzbek Telegram channel.

--- RULES THE POST MUST SATISFY ---
{rules()}
--- END RULES ---

TOPIC: {topic}

--- POST AS IT WILL APPEAR (HTML, {len(caption)} characters) ---
{caption}
--- END POST ---

Check every rule. Pay special attention to: Uzbek spelling errors, unverified numbers,
forbidden content, klishe phrases, emoji count, character limit.

Return ONLY valid JSON, no markdown fences:
{{"verdict": "pass|fix|reject",
  "score": <0-100>,
  "issues": ["<issue in Uzbek>", ...],
  "fixed_caption": "<if verdict is 'fix': the corrected full caption in the same HTML
   format, under 1000 characters. If verdict is 'pass' or 'reject': empty string>"}}

Use "reject" only for forbidden content or fabricated facts. Use "fix" for anything
repairable. Use "pass" if it is genuinely good."""
