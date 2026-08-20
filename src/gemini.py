"""Gemini API: mavzu topish, research, yozish, QC, rasm."""
import base64
import json
import re
import time

import requests

from . import config, style

BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiError(RuntimeError):
    pass


def _call(model, payload, timeout=180, retries=3):
    url = f"{BASE}/{model}:generateContent"
    headers = {"x-goog-api-key": config.GEMINI_KEY, "Content-Type": "application/json"}
    last = None
    for attempt in range(retries):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 503):
                last = f"{r.status_code}: {r.text[:300]}"
                time.sleep(5 * (attempt + 1))
                continue
            raise GeminiError(f"{model} -> {r.status_code}: {r.text[:500]}")
        except requests.RequestException as e:
            last = str(e)
            time.sleep(5 * (attempt + 1))
    raise GeminiError(f"{model} muvaffaqiyatsiz: {last}")


def _text_of(resp):
    out = []
    for cand in resp.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            if "text" in part:
                out.append(part["text"])
    return "\n".join(out).strip()


def _json_of(resp):
    raw = _text_of(resp)
    raw = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw.strip())
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            return json.loads(m.group(0))
        raise GeminiError(f"JSON o'qib bo'lmadi: {raw[:300]}")


def _gen(prompt, search=False, json_out=False, temperature=0.9):
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 4096},
    }
    if search:
        payload["tools"] = [{"google_search": {}}]
    resp = _call(config.TEXT_MODEL, payload)
    return _json_of(resp) if json_out else _text_of(resp)


# ---------- 1. Mavzu ----------
def pick_topic(recent_titles):
    data = _gen(style.topic_prompt(recent_titles), search=True, json_out=True, temperature=1.0)
    return data.get("topic", ""), data.get("angle", ""), data.get("category", "")


# ---------- 2. Research ----------
def research(topic, angle=""):
    return _gen(style.research_prompt(topic, angle), search=True, temperature=0.4)


# ---------- 3. Yozish ----------
def write_post(topic, angle, briefing, feedback=None, previous=None):
    data = _gen(
        style.write_prompt(topic, angle, briefing, feedback, previous),
        json_out=True,
        temperature=0.95,
    )
    tags = data.get("hashtags") or []
    if isinstance(tags, str):
        tags = tags.split()
    data["hashtags"] = ["#" + t.lstrip("#") for t in tags][:3]
    return data


def shorten(caption, limit):
    prompt = (
        f"{style.VOICE}\n\nThis Telegram caption is {len(caption)} characters but must be "
        f"under {limit}. Shorten it in Uzbek, keeping the title, the main idea, the voice "
        f"and the hashtags. Cut examples and repetition, not the point.\n\n"
        f"--- CAPTION ---\n{caption}\n--- END ---\n\n"
        f"Return ONLY the shortened caption text, same HTML formatting, nothing else."
    )
    out = _gen(prompt, temperature=0.5)
    return re.sub(r"^\s*```(?:html)?\s*|\s*```\s*$", "", out.strip())


# ---------- 4. Sifat nazorati ----------
def qc(caption, topic):
    return _gen(style.qc_prompt(caption, topic), json_out=True, temperature=0.2)


# ---------- 5. Rasm ----------
def generate_image(image_prompt):
    """Rasm baytlarini qaytaradi, bo'lmasa None."""
    full = (
        f"{image_prompt}\n\n"
        "Wide landscape composition, 16:9. Clean minimal illustration, warm muted palette, "
        "soft lighting, plenty of negative space. Critically important: the image must "
        "contain absolutely no text, no letters, no numbers, no watermarks, no logos."
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": full}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    for model in config.IMAGE_MODELS:
        try:
            resp = _call(model, payload, timeout=240, retries=2)
        except GeminiError as e:
            print(f"[rasm] {model} ishlamadi: {e}")
            continue
        for cand in resp.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and inline.get("data"):
                    print(f"[rasm] {model} orqali yaratildi")
                    return base64.b64decode(inline["data"])
        print(f"[rasm] {model} rasm qaytarmadi")
    return None
