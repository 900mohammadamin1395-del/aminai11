# -*- coding: utf-8 -*-

import html
import re

from urllib.parse import quote

import requests

from network import get_safe_proxies


TRIGGER_VERBS = [
    "بساز",
    "بکش",
    "درست کن",
    "تولید کن",
    "طراحی کن",
    "نقاشی کن",
    "رسم کن",
    "ایجاد کن",
    "بزن"
]

SUBJECT_WORDS = ["عکس", "تصویر", "نقاشی", "طرح", "لوگو", "پوستر"]

LEADING_FILLERS = [
    "میشه",
    "می‌شه",
    "میتونی",
    "می‌تونی",
    "میخوام",
    "می‌خوام",
    "لطفا",
    "لطفاً",
    "خواهش می‌کنم",
    "برام",
    "واسم"
]

TRAILING_FILLERS = [
    "برام",
    "واسم",
    "لطفا",
    "لطفاً",
    "میشه",
    "می‌شه",
    "؟",
    "?",
    "!"
]


GRAYSCALE_PHRASES = [
    "سیاه و سفید",
    "سیاه‌و‌سفید",
    "سیاه سفید",
    "مشکی و سفید",
    "مشکی سفید",
    "مونوکروم",
    "black and white",
    "black & white",
    "monochrome"
]


def strip_grayscale_request(prompt):
    """
    Looks for a black-and-white request inside an already-extracted image
    prompt (e.g. "یک گربه سیاه و سفید"), removes that phrase from the
    description, and reports whether grayscale mode should be used.
    Returns (cleaned_prompt, is_grayscale).
    """

    cleaned = prompt

    is_grayscale = False

    for phrase in GRAYSCALE_PHRASES:

        if phrase in cleaned:

            is_grayscale = True

            cleaned = cleaned.replace(phrase, " ")

    if is_grayscale:

        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        cleaned = re.sub(r"^از\s+", "", cleaned)

        cleaned = cleaned.strip(" \u200c،,.؟?!")

        if not cleaned:
            cleaned = prompt

    return cleaned, is_grayscale


def detect_prompt(message):

    text = message.strip()

    has_subject = any(word in text for word in SUBJECT_WORDS)
    has_verb = any(verb in text for verb in TRIGGER_VERBS)

    if not (has_subject and has_verb):
        return None

    # strip trailing punctuation early so it doesn't block later cleanup
    cleaned = text.strip(" \u200c؟?!.,،")

    for verb in TRIGGER_VERBS:
        cleaned = cleaned.replace(verb, " ")

    # a verb like "بساز" removed from a conjugated form like "بسازی"
    # can leave a stray single "ی" behind — drop those isolated leftovers
    cleaned = re.sub(r"(?<!\S)ی(?!\S)", " ", cleaned)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    changed = True

    while changed:

        changed = False

        for filler in LEADING_FILLERS:

            if cleaned.startswith(filler):
                cleaned = cleaned[len(filler):].strip()
                changed = True

        for filler in TRAILING_FILLERS:

            if cleaned.endswith(filler):
                cleaned = cleaned[:len(cleaned) - len(filler)].strip()
                changed = True

    before_subject_strip = cleaned

    cleaned = re.sub(
        r"^(یک\s+|یه\s+)?(عکس|تصویر|نقاشی|طرح|لوگو|پوستر)(ی)?\s*(از\s+)?",
        "",
        cleaned.strip()
    )

    # if stripping the subject word (e.g. "لوگو") leaves nothing behind,
    # the subject word itself was the whole description — keep it
    if not cleaned.strip():
        cleaned = before_subject_strip.strip()

    cleaned = re.sub(r"\s+(رو|را)$", "", cleaned.strip())

    cleaned = cleaned.strip(" \u200c،,.؟?!")

    if not cleaned:
        return None

    return cleaned


def translate_to_english(text):

    try:

        # MyMemory یه سرویس ترجمه‌ی رایگان و رسمیه (برخلاف endpoint
        # غیررسمی گوگل که خیلی زود محدودیت نرخ (429) می‌ذاره)
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={
                "q": text,
                "langpair": "fa|en"
            },
            proxies=get_safe_proxies(),
            timeout=(5, 8)
        )

        response.raise_for_status()

        data = response.json()

        translated = data.get("responseData", {}).get("translatedText", "")

        translated = html.unescape(translated).strip()

        if not translated or "MYMEMORY WARNING" in translated.upper():
            return text

        return translated

    except Exception:

        return text


def build_image_url(prompt, width=768, height=768, grayscale=False):

    english_prompt = translate_to_english(prompt)

    if grayscale:
        english_prompt = english_prompt.strip() + ", black and white, monochrome, grayscale photography"

    encoded = quote(english_prompt.strip())

    return (
        "https://image.pollinations.ai/prompt/" + encoded +
        "?width=" + str(width) +
        "&height=" + str(height) +
        "&nologo=true"
    )

