# -*- coding: utf-8 -*-

import re

from datetime import date


TRIGGER_WORDS = [
    "چند روز",
    "چند روزه",
    "روزشمار",
    "چقدر مونده",
    "چقدر مانده",
    "چند روز مونده",
    "چند روز مانده"
]

# تاریخ‌ها میلادی و تقریبی‌ان (مثلاً نوروز گاهی ۲۰ و گاهی ۲۱ اسفندماه
# میلادیه، چون به لحظه‌ی اعتدال بهاری بستگی داره) — برای یه قابلیت
# سرگرم‌کننده کافیه، نه برای مصارف رسمی/تقویمی دقیق
OCCASIONS = [
    {
        "names": ["نوروز", "عید نوروز", "سال نو"],
        "display": "نوروز",
        "month": 3,
        "day": 20,
        "emoji": "🌸"
    },
    {
        "names": ["یلدا", "شب یلدا", "شب چله"],
        "display": "شب یلدا",
        "month": 12,
        "day": 21,
        "emoji": "🍉"
    },
    {
        "names": ["سیزده بدر", "سیزده به در"],
        "display": "سیزده‌بدر",
        "month": 4,
        "day": 2,
        "emoji": "🌿"
    },
    {
        "names": ["مهرگان"],
        "display": "مهرگان",
        "month": 10,
        "day": 2,
        "emoji": "🍂"
    },
    {
        "names": ["تیرگان"],
        "display": "تیرگان",
        "month": 7,
        "day": 1,
        "emoji": "💧"
    }
]


def detect_request(message):

    text = message.strip()

    has_trigger = any(word in text for word in TRIGGER_WORDS)

    if not has_trigger:
        return False

    return _find_occasion(text) is not None


def _find_occasion(text):

    for occasion in OCCASIONS:

        for name in occasion["names"]:

            pattern = r"\b" + re.escape(name) + r"\b"

            if re.search(pattern, text):
                return occasion

    return None


def _days_until(month, day):

    today = date.today()

    year = today.year

    target = date(year, month, day)

    if target < today:
        target = date(year + 1, month, day)

    return (target - today).days, target


def build_answer(message):

    occasion = _find_occasion(message)

    if not occasion:
        return None

    days_left, target_date = _days_until(occasion["month"], occasion["day"])

    if days_left == 0:
        return occasion["emoji"] + " امروز " + occasion["display"] + "ه! پیشاپیش مبارک باشه 🎉"

    return (
        occasion["emoji"] + " تا " + occasion["display"] + " حدود " +
        str(days_left) + " روز مونده (تقریباً " +
        str(target_date.day) + "/" + str(target_date.month) + "/" + str(target_date.year) + " میلادی)."
    )
