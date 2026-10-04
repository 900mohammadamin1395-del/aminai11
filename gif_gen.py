# -*- coding: utf-8 -*-

import io
import os
import re
import uuid

from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import requests
from PIL import Image

from image_gen import translate_to_english
from network import get_safe_proxies


GIF_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static",
    "gifs"
)

TRIGGER_VERBS = [
    "بساز",
    "درست کن",
    "تولید کن",
    "طراحی کن",
    "ایجاد کن",
    "بزن"
]

SUBJECT_WORDS = ["گیف", "گیفی", "gif", "عکس متحرک", "تصویر متحرک", "انیمیشن"]

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


def detect_prompt(message):

    text = message.strip()

    has_subject = any(word in text for word in SUBJECT_WORDS)
    has_verb = any(verb in text for verb in TRIGGER_VERBS)

    if not (has_subject and has_verb):
        return None

    cleaned = text.strip(" \u200c؟?!.,،")

    for verb in TRIGGER_VERBS:
        cleaned = cleaned.replace(verb, " ")

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
        r"^(یک\s+|یه\s+)?(گیف|گیفی|gif|عکس متحرک|تصویر متحرک|انیمیشن)(ی)?\s*(از\s+)?",
        "",
        cleaned.strip(),
        flags=re.IGNORECASE
    )

    if not cleaned.strip():
        cleaned = before_subject_strip.strip()

    cleaned = re.sub(r"\s+(رو|را)$", "", cleaned.strip())

    cleaned = cleaned.strip(" \u200c،,.؟?!")

    if not cleaned:
        return None

    return cleaned


def _fetch_frame(args):

    prompt, width, height, seed = args

    url = (
        "https://image.pollinations.ai/prompt/" + quote(prompt) +
        "?width=" + str(width) +
        "&height=" + str(height) +
        "&nologo=true" +
        "&seed=" + str(seed)
    )

    response = requests.get(
        url,
        proxies=get_safe_proxies(),
        timeout=(5, 55)
    )
    response.raise_for_status()

    image = Image.open(io.BytesIO(response.content)).convert("RGB")

    return image


def generate_gif(prompt, frame_count=3, width=384, height=384, frame_duration_ms=450):
    """
    Builds a short looping GIF out of several free Pollinations image
    generations of the same prompt (each with a different seed so they
    vary slightly), stitched together. This keeps it free — unlike real
    video generation, which costs paid credits — but the result is more
    of a looping slideshow of related frames than smooth motion.

    Returns a local URL path like "/static/gifs/<name>.gif", or None on
    failure.
    """

    english_prompt = translate_to_english(prompt)

    base_seed = uuid.uuid4().int % 100000

    jobs = [
        (english_prompt, width, height, base_seed + i)
        for i in range(frame_count)
    ]

    try:

        with ThreadPoolExecutor(max_workers=frame_count) as pool:
            frames = list(pool.map(_fetch_frame, jobs))

        if not frames:
            return None

        os.makedirs(GIF_DIR, exist_ok=True)

        filename = uuid.uuid4().hex + ".gif"
        filepath = os.path.join(GIF_DIR, filename)

        frames[0].save(
            filepath,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration_ms,
            loop=0
        )

        return "/static/gifs/" + filename

    except Exception:

        return None
