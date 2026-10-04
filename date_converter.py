# -*- coding: utf-8 -*-

import re

from datetime import date


# پیاده‌سازی الگوریتم نجومی معروف jalaali-js (بر پایه‌ی کار Kazimierz M.
# Borkowski) — همون الگوریتمی که تقویم رسمی ایران هم بر پایه‌ش کار می‌کنه.

def _div(a, b):
    # تقسیم صحیح رو به سمت صفر گرد می‌کنه (مثل ~~(a/b) در جاوااسکریپت)،
    # نه به سمت منفی‌بی‌نهایت (که رفتار پیش‌فرض // در پایتونه)
    q = a // b
    if (a % b != 0) and ((a < 0) != (b < 0)):
        q += 1
    return q


BREAKS = [
    -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181,
    1210, 1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178
]


def _jal_cal(jy):

    bl = len(BREAKS)
    gy = jy + 621
    leap_j = -14
    jp = BREAKS[0]

    if jy < jp or jy >= BREAKS[bl - 1]:
        raise ValueError("سال شمسی نامعتبر: " + str(jy))

    jump = 0
    i = 1
    while i < bl:
        jm = BREAKS[i]
        jump = jm - jp
        if jy < jm:
            break
        leap_j = leap_j + _div(jump, 33) * 8 + _div(jump % 33, 4)
        jp = jm
        i += 1

    n = jy - jp
    leap_j = leap_j + _div(n, 33) * 8 + _div((n % 33) + 3, 4)

    if (jump % 33) == 4 and (jump - n) == 4:
        leap_j += 1

    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g

    if (jump - n) < 6:
        n = n - jump + _div(jump + 4, 33) * 33

    leap = (((n + 1) % 33) - 1) % 4
    if leap == -1:
        leap = 4

    return {"leap": leap, "gy": gy, "march": march}


def _g2d(gy, gm, gd):
    d = (
        _div((gy + _div(gm - 8, 6) + 100100) * 1461, 4)
        + _div(153 * ((gm + 9) % 12) + 2, 5)
        + gd - 34840408
    )
    d = d - _div(_div(gy + 100100 + _div(gm - 8, 6), 100) * 3, 4) + 752
    return d


def _d2g(jdn):
    j = 4 * jdn + 139361631
    j = j + _div(_div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908
    i = _div(j % 1461, 4) * 5 + 308
    gd = _div(i % 153, 5) + 1
    gm = (_div(i, 153) % 12) + 1
    gy = _div(j, 1461) - 100100 + _div(8 - gm, 6)
    return {"gy": gy, "gm": gm, "gd": gd}


def _j2d(jy, jm, jd):
    r = _jal_cal(jy)
    return _g2d(r["gy"], 3, r["march"]) + (jm - 1) * 31 - _div(jm, 7) * (jm - 7) + jd - 1


def _d2j(jdn):
    gy = _d2g(jdn)["gy"]
    jy = gy - 621
    r = _jal_cal(jy)
    jdn1f = _g2d(r["gy"], 3, r["march"])

    k = jdn - jdn1f

    if k >= 0:
        if k <= 185:
            jm = 1 + _div(k, 31)
            jd = (k % 31) + 1
            return {"jy": jy, "jm": jm, "jd": jd}
        else:
            k -= 186
    else:
        jy -= 1
        k += 179
        if r["leap"] == 1:
            k += 1

    jm = 7 + _div(k, 30)
    jd = (k % 30) + 1
    return {"jy": jy, "jm": jm, "jd": jd}


def jalali_to_gregorian(jy, jm, jd):
    d = _d2g(_j2d(jy, jm, jd))
    return d["gy"], d["gm"], d["gd"]


def gregorian_to_jalali(gy, gm, gd):
    d = _d2j(_g2d(gy, gm, gd))
    return d["jy"], d["jm"], d["jd"]


# ---------------------------------------------------------------------
# تشخیص درخواست و پارس کردن تاریخ از متن فارسی
# ---------------------------------------------------------------------

PERSIAN_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]

GREGORIAN_MONTHS_FA = [
    "ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن",
    "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"
]

# چند اسم جایگزین/رایج‌تر برای بعضی ماه‌های میلادی که مردم بیشتر باهاشون
# آشنان (مثلاً «می» به‌جای «مه»، «جولای» به‌جای «ژوئیه»)
GREGORIAN_MONTH_ALIASES = {
    "می": 5,
    "جولای": 7,
    "آگوست": 8
}

PERSIAN_WEEKDAYS = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ENGLISH_DIGITS = "0123456789"

DIGIT_MAP = str.maketrans(
    PERSIAN_DIGITS + ARABIC_DIGITS,
    ENGLISH_DIGITS + ENGLISH_DIGITS
)


def _normalize_digits(text):
    return text.translate(DIGIT_MAP)


def detect_request(message):

    text = _normalize_digits(message.strip())

    has_trigger = ("میلادی" in text) or ("شمسی" in text)

    has_digit = bool(re.search(r"\d", text))

    return has_trigger and has_digit


def _parse_named_month(text, month_names):

    for idx, name in enumerate(month_names, start=1):

        pattern = r"(\d{1,2})\s*" + re.escape(name) + r"\s*(\d{2,4})"

        match = re.search(pattern, text)

        if match:
            return int(match.group(2)), idx, int(match.group(1))

    return None


def _parse_gregorian_aliases(text):

    for alias, idx in GREGORIAN_MONTH_ALIASES.items():

        pattern = r"(\d{1,2})\s*" + re.escape(alias) + r"\s*(\d{4})"

        match = re.search(pattern, text)

        if match:
            return int(match.group(2)), idx, int(match.group(1))

    return None


def _parse_numeric_date(text):

    # yyyy-mm-dd یا yyyy/mm/dd
    match = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", text)

    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    # dd-mm-yyyy یا dd/mm/yyyy
    match = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", text)

    if match:
        return int(match.group(3)), int(match.group(2)), int(match.group(1))

    return None


def _weekday_name(gy, gm, gd):

    try:
        return PERSIAN_WEEKDAYS[date(gy, gm, gd).weekday()]
    except Exception:
        return None


def build_answer(message):

    text = _normalize_digits(message.strip())

    # کلمه‌ای که کاربر خواسته («میلادی» یا «شمسی») در واقع نشون میده
    # می‌خواد تاریخش به چه تقویمی تبدیل بشه — یعنی تاریخ ورودی خودش
    # باید در تقویم مقابل باشه
    wants_gregorian_output = "میلادی" in text
    wants_jalali_output = "شمسی" in text

    if wants_gregorian_output:

        # ورودی احتمالاً شمسیه: اول اسم ماه فارسی، بعد فرمت عددی
        parsed = _parse_named_month(text, PERSIAN_MONTHS) or _parse_numeric_date(text)

        if not parsed:
            return (
                "📅 تاریخ شمسی رو متوجه نشدم. یه نمونه بنویس مثلاً "
                "«۱۵ مهر ۱۴۰۳ چه تاریخی میلادیه؟»"
            )

        jy, jm, jd = parsed

        try:

            gy, gm, gd = jalali_to_gregorian(jy, jm, jd)

            weekday = _weekday_name(gy, gm, gd)
            weekday_part = ("(" + weekday + ") ") if weekday else ""

            return (
                "📅 " + str(jd) + " " + PERSIAN_MONTHS[jm - 1] + " " + str(jy) +
                " برابره با " + weekday_part +
                str(gd) + " " + GREGORIAN_MONTHS_FA[gm - 1] + " " + str(gy) + " میلادی."
            )

        except Exception:
            return "این تاریخ شمسی معتبر نیست، دوباره چک کن 😕"

    if wants_jalali_output:

        # ورودی احتمالاً میلادیه: اسم ماه (فارسی‌شده یا رایج)، بعد فرمت عددی
        parsed = (
            _parse_named_month(text, GREGORIAN_MONTHS_FA)
            or _parse_gregorian_aliases(text)
            or _parse_numeric_date(text)
        )

        if not parsed:
            return (
                "📅 تاریخ میلادی رو متوجه نشدم. یه نمونه بنویس مثلاً "
                "«۲۵ دسامبر ۲۰۲۶ چه تاریخی شمسیه؟»"
            )

        gy, gm, gd = parsed

        try:

            jy, jm, jd = gregorian_to_jalali(gy, gm, gd)

            weekday = _weekday_name(gy, gm, gd)
            weekday_part = ("(" + weekday + ") ") if weekday else ""

            return (
                "📅 " + str(gd) + " " + GREGORIAN_MONTHS_FA[gm - 1] + " " + str(gy) +
                " میلادی برابره با " + weekday_part +
                str(jd) + " " + PERSIAN_MONTHS[jm - 1] + " " + str(jy) + " شمسی."
            )

        except Exception:
            return "این تاریخ میلادی معتبر نیست، دوباره چک کن 😕"

    return None
