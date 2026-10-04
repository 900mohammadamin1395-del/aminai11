# -*- coding: utf-8 -*-

import html
import os
import re

import requests

from network import get_safe_proxies


LANGUAGE_MAP = {
    "انگلیسی": "en",
    "english": "en",
    "فارسی": "fa",
    "فارسی‌": "fa",
    "عربی": "ar",
    "فرانسوی": "fr",
    "فرانسه": "fr",
    "آلمانی": "de",
    "اسپانیایی": "es",
    "ایتالیایی": "it",
    "ترکی": "tr",
    "استانبولی": "tr",
    "روسی": "ru",
    "چینی": "zh-CN",
    "ژاپنی": "ja",
    "کره‌ای": "ko",
    "هندی": "hi",
    "پرتغالی": "pt",
    "اردو": "ur"
}

LANGUAGE_DISPLAY = {
    "en": "انگلیسی",
    "fa": "فارسی",
    "ar": "عربی",
    "fr": "فرانسوی",
    "de": "آلمانی",
    "es": "اسپانیایی",
    "it": "ایتالیایی",
    "tr": "ترکی",
    "ru": "روسی",
    "zh-CN": "چینی",
    "ja": "ژاپنی",
    "ko": "کره‌ای",
    "hi": "هندی",
    "pt": "پرتغالی",
    "ur": "اردو"
}

PLACEHOLDER_PHRASES = ["این جمله", "این متن", "این عبارت", "این کلمه"]


def _find_target_lang(text):

    for name, code in sorted(LANGUAGE_MAP.items(), key=lambda item: len(item[0]), reverse=True):

        if ("به " + name) in text or ("به‌" + name) in text:
            return code

    return None


def detect_request(message):

    text = message.strip()

    if "ترجمه" not in text:
        return None

    target_code = _find_target_lang(text)

    # حالت اول: بعد از دونقطه، متن اصلی میاد
    # مثال: «این جمله رو به انگلیسی ترجمه کن: سلام دنیا»
    colon_match = re.search(r"[:：]\s*(.+)$", text, re.DOTALL)

    if colon_match:

        content = colon_match.group(1).strip()

        if content:
            return {"text": content, "target": target_code or "en"}

    # حالت دوم: TEXT رو/را به LANG ترجمه کن
    # مثال: «سلام دنیا رو به انگلیسی ترجمه کن»
    pattern = re.compile(
        r"^(?P<content>.+?)\s*(?:رو|را)?\s*به\s+(?P<lang>[\w\u0600-\u06FF]+)\s*ترجمه\s*(?:کن)?[\.\!\؟\?]*$"
    )

    match = pattern.match(text)

    if match:

        content = match.group("content").strip()
        lang_word = match.group("lang").strip()

        code = LANGUAGE_MAP.get(lang_word)

        if content and content not in PLACEHOLDER_PHRASES:
            return {"text": content, "target": code or "en"}

    # حالت سوم: فقط «ترجمه کن» + متن، بدون دونقطه و بدون زبان مشخص
    # مثال: «ترجمه کن سلام دنیا»
    simple_match = re.match(
        r"^ترجمه\s*(?:ی\s*این\s*(?:جمله|متن|عبارت))?\s*کن\s+(?P<content>.+)$",
        text
    )

    if simple_match:

        content = simple_match.group("content").strip()

        if content:
            return {"text": content, "target": target_code or "en"}

    return None


LAST_ERROR_LOG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "translate_error.log"
)


def _log_error(text):

    try:
        with open(LAST_ERROR_LOG, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass


PERSIAN_CHAR_PATTERN = re.compile(r"[\u0600-\u06FF]")


def _guess_source(text, target):

    if PERSIAN_CHAR_PATTERN.search(text):
        source = "fa"
    else:
        source = "en"

    # جلوگیری از حالت بی‌معنی «ترجمه از فارسی به فارسی»
    if source == target:
        source = "en" if target == "fa" else "fa"

    return source


def translate(text, target="en"):

    source = _guess_source(text, target)

    try:

        # MyMemory یه سرویس ترجمه‌ی رایگان و رسمیه (برخلاف endpoint
        # غیررسمی گوگل که سریع محدودیت نرخ می‌ذاره)
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={
                "q": text,
                "langpair": source + "|" + target
            },
            proxies=get_safe_proxies(),
            timeout=(5, 10)
        )

        response.raise_for_status()

        data = response.json()

        translated = data.get("responseData", {}).get("translatedText", "")

        translated = html.unescape(translated).strip()

        status = data.get("responseStatus")

        if (
            not translated
            or "MYMEMORY WARNING" in translated.upper()
            or status not in (200, "200")
        ):
            _log_error(
                "mymemory issue — status: " + str(status) + "\n" +
                "translated: " + translated[:500]
            )
            return None

        return translated

    except Exception as error:

        _log_error("exception: " + repr(error))

        return None


def build_answer(message):

    request_info = detect_request(message)

    if not request_info:
        return None

    translated = translate(request_info["text"], request_info["target"])

    if not translated:
        return (
            "متأسفانه توی ترجمه مشکلی پیش اومد 😕\n"
            "جزئیات خطا داخل فایل translate_error.log (کنار server.py) ذخیره شده."
        )

    target_name = LANGUAGE_DISPLAY.get(request_info["target"], request_info["target"])

    return "🌐 ترجمه به " + target_name + ":\n\n" + translated
