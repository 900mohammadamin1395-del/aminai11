# -*- coding: utf-8 -*-

from web_search import fetch_results
from summarizer import summarize


TRIGGER_PHRASES = [
    "اخبار امروز",
    "اخبار صبح",
    "خلاصه اخبار",
    "خلاصه‌ی اخبار",
    "چه خبر",
    "امروز چه خبره",
    "امروز چه خبر است",
    "صبح چی شده",
    "صبح چه خبر",
    "اخبار رو بگو",
    "اخبار را بگو",
    "خبر جدید چیه",
    "خبرای امروز",
    "اخبار جدید"
]

# هر بخش چند عبارت جستجوی جایگزین داره؛ اگه اولی فقط نتیجه‌ی کم‌محتوا
# (مثلاً فقط اسم سایت‌ها) بده، بعدی امتحان می‌شه
CATEGORIES = [
    ("🇮🇷 ایران", ["آخرین اخبار ایران", "تازه‌ترین اخبار ایران امروز"]),
    ("🌍 جهان", ["آخرین اخبار بین‌الملل", "تازه‌ترین اخبار جهان امروز"])
]

# نتیجه‌هایی که طولشون از این کمتره معمولاً فقط اسم سایت یا یه تیتر
# خیلی کوتاهن، نه محتوای واقعی — برای خلاصه‌سازی به‌درد نمی‌خورن
MIN_USEFUL_LENGTH = 40


def detect_request(message):

    text = message.strip()

    return any(phrase in text for phrase in TRIGGER_PHRASES)


def _fetch_quality_texts(query, limit=6):

    raw_texts = fetch_results(query, limit=limit * 2)

    quality_texts = [text for text in raw_texts if len(text) >= MIN_USEFUL_LENGTH]

    return quality_texts[:limit]


def build_briefing():

    sections = []

    for label, queries in CATEGORIES:

        texts = []

        for query in queries:

            try:
                texts = _fetch_quality_texts(query)
            except Exception:
                texts = []

            if texts:
                break

        if not texts:
            continue

        full_text = " ".join(texts)

        summary = summarize(full_text, max_sentences=2)

        if summary.strip():
            sections.append(label + ":\n" + summary)

    if not sections:
        return "متأسفانه الان نتونستم خبر واقعی پیدا کنم (فقط نتیجه‌های کم‌محتوا اومد)، یه بار دیگه امتحان کن 📰"

    return "📰 خلاصه‌ی اخبار امروز:\n\n" + "\n\n".join(sections)
