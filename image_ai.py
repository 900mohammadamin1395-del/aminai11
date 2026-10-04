# -*- coding: utf-8 -*-

"""
ساخت عکس جدید از روی «عکس آپلودشده + پرامپت» با سرویس هوش مصنوعی
(image-to-image). پیش‌فرض: Pollinations، endpoint سازگار با OpenAI:

    POST https://gen.pollinations.ai/v1/images/edits   (multipart/form-data)

عکس مستقیم از خود سرور فرستاده می‌شه؛ نیازی به آدرس عمومی یا ngrok نیست.

تنظیم‌ها از متغیرهای محیطی (توی ویندوز با set یا setx):

    POLLINATIONS_KEY     کلید API (الزامی) — از enter.pollinations.ai
    AMIN_IMG2IMG_URL     آدرس endpoint؛ پیش‌فرض https://gen.pollinations.ai/v1/images/edits
    AMIN_IMG2IMG_MODEL   اسم مدل؛ پیش‌فرض black-forest-labs/flux.1-kontext-pro
"""

import base64
import io
import mimetypes
import os
import re
import time
import uuid

import requests
from PIL import Image

from image_gen import translate_to_english
from network import get_safe_proxies


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULT_DIR = os.path.join(BASE_DIR, "static", "generated")

DEFAULT_SERVICE_URL = "https://gen.pollinations.ai/v1/images/edits"
DEFAULT_MODEL = "black-forest-labs/flux.1-kontext-pro"

MAX_RESULT_BYTES = 15 * 1024 * 1024

COOLDOWN_SECONDS = 8

_last_call = {}


AI_WORDS = ["هوش مصنوعی", "با ای آی", "با ai", "با a.i", " ai ", "(ai)"]


def api_key():

    return (os.environ.get("POLLINATIONS_KEY") or "").strip()


def is_configured():

    return bool(api_key())


def wants_ai(prompt):
    """کاربر صراحتاً خواسته با هوش مصنوعی ساخته بشه؟"""

    text = " " + prompt.lower().replace("\u200c", " ") + " "

    return any(word in text for word in AI_WORDS)


def clean_prompt(prompt):
    """کلمه‌های مربوط به انتخاب موتور رو از پرامپت حذف می‌کنه"""

    text = prompt

    for word in ["با هوش مصنوعی", "با ای آی", "با AI", "با ai"]:
        text = text.replace(word, " ")

    return re.sub(r"\s+", " ", text).strip(" \u200c،,.؟?!")


def _save_result(content):
    """بایت‌های جواب سرویس رو با Pillow اعتبارسنجی و به‌صورت PNG ذخیره می‌کنه"""

    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except Exception:
        return None

    os.makedirs(RESULT_DIR, exist_ok=True)

    filename = uuid.uuid4().hex + ".png"

    image.convert("RGB").save(os.path.join(RESULT_DIR, filename), "PNG")

    return "/static/generated/" + filename


def _extract_image_bytes(payload):
    """
    جواب سازگار با OpenAI: {"data": [{"b64_json": "..."}]} یا {"data": [{"url": "..."}]}
    """

    items = payload.get("data") or []

    if not items:
        return None

    first = items[0]

    if first.get("b64_json"):

        try:
            return base64.b64decode(first["b64_json"])
        except Exception:
            return None

    url = first.get("url")

    if url and url.startswith("https://"):

        try:
            image_response = requests.get(
                url,
                proxies=get_safe_proxies(),
                timeout=(10, 60)
            )
            image_response.raise_for_status()
            return image_response.content
        except Exception:
            return None

    return None


def generate(image_path, prompt, user_id=None):
    """
    image_path: مسیر عکس آپلودشده روی دیسک
    برمی‌گردونه: (آدرس نتیجه یا None، پیام خطا یا None)
    """

    if not is_configured():
        return None, "not_configured"

    now = time.time()

    if user_id is not None:

        last = _last_call.get(user_id, 0)

        if now - last < COOLDOWN_SECONDS:
            return None, "یه کم صبر کن و چند ثانیه‌ی دیگه دوباره امتحان کن ⏳"

        _last_call[user_id] = now

    service = (os.environ.get("AMIN_IMG2IMG_URL") or DEFAULT_SERVICE_URL).strip()

    model = (os.environ.get("AMIN_IMG2IMG_MODEL") or DEFAULT_MODEL).strip()

    english_prompt = translate_to_english(prompt).strip()

    content_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"

    try:

        with open(image_path, "rb") as handle:

            response = requests.post(
                service,
                headers={"Authorization": "Bearer " + api_key()},
                data={
                    "prompt": english_prompt,
                    "model": model,
                    "response_format": "b64_json"
                },
                files={
                    "image": (os.path.basename(image_path), handle, content_type)
                },
                proxies=get_safe_proxies(),
                timeout=(10, 180)
            )

    except requests.exceptions.Timeout:
        return None, "سرویس ساخت عکس دیر جواب داد. دوباره امتحان کن."

    except Exception:
        return None, "به سرویس ساخت عکس وصل نشدم. اینترنت یا پروکسی رو چک کن."

    if response.status_code == 401:
        return None, "کلید API معتبر نیست یا ست نشده (POLLINATIONS_KEY)."

    if response.status_code == 402:
        return None, "اعتبار حساب سرویس ساخت عکس تموم شده."

    if response.status_code == 429:
        return None, "سرویس ساخت عکس الان شلوغه (محدودیت تعداد درخواست). کمی بعد دوباره امتحان کن."

    if response.status_code != 200:
        return None, "سرویس ساخت عکس خطا داد (کد " + str(response.status_code) + ")."

    try:
        content = _extract_image_bytes(response.json())
    except Exception:
        content = None

    if not content:
        return None, "سرویس ساخت عکس جواب تصویری نداد."

    if len(content) > MAX_RESULT_BYTES:
        return None, "عکس تولیدشده خیلی بزرگ بود."

    result_url = _save_result(content)

    if not result_url:
        return None, "عکسی که سرویس برگردوند خراب بود."

    return result_url, None
