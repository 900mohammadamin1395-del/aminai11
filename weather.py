# -*- coding: utf-8 -*-

import re
from datetime import date

import requests

from network import get_safe_proxies


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

DEFAULT_CITY = {
    "name": "تهران",
    "latitude": 35.6892,
    "longitude": 51.3890
}

WEEKDAYS_FA = [
    "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"
]

# کدهای WMO که Open-Meteo برمی‌گردونه -> (توضیح، ایموجی)
WEATHER_CODES = {
    0: ("آسمان صاف", "☀️"),
    1: ("نیمه‌صاف", "🌤"),
    2: ("نیمه‌ابری", "⛅"),
    3: ("ابری", "☁️"),
    45: ("مه‌آلود", "🌫"),
    48: ("مه‌آلود", "🌫"),
    51: ("نم‌نم باران", "🌦"),
    53: ("نم‌نم باران", "🌦"),
    55: ("نم‌نم باران", "🌦"),
    56: ("نم‌نم باران یخ‌زده", "🌦"),
    57: ("نم‌نم باران یخ‌زده", "🌦"),
    61: ("بارانی", "🌧"),
    63: ("بارانی", "🌧"),
    65: ("باران شدید", "🌧"),
    66: ("باران یخ‌زده", "🌧"),
    67: ("باران یخ‌زده", "🌧"),
    71: ("برفی", "🌨"),
    73: ("برفی", "🌨"),
    75: ("برف سنگین", "❄️"),
    77: ("دانه‌های برف", "🌨"),
    80: ("رگبار", "🌦"),
    81: ("رگبار", "🌦"),
    82: ("رگبار شدید", "⛈"),
    85: ("رگبار برف", "🌨"),
    86: ("رگبار برف", "🌨"),
    95: ("رعد و برق", "⛈"),
    96: ("رعد و برق با تگرگ", "⛈"),
    99: ("رعد و برق با تگرگ", "⛈")
}

# کلمه‌هایی که توی پیام هواشناسی هستن ولی اسم شهر نیستن
STOP_WORDS = set("""
هوا هوای آب‌وهوا آب‌وهوای آبوهوا آبوهوای آب و
فردا امروز پس‌فردا پسفردا پس الان الآن فعلا فعلاً
چطوره چطور چطوری چجوره چجور چیه چی چه چند چنده
است هست هستش بگو بگید بده بدید بزن بزنی حدس پیش‌بینی پیشبینی
دما درجه دمای وضعیت وضع
در تو توی برای واسه واسم برام به از
لطفا لطفاً میشه می‌شه میتونی می‌تونی
بارون باران بارونی بارانی میاد میباره می‌باره می‌یاد میشه می‌شه
گرمه سرده خنکه گرم سرد خنک برفی برف آفتابی ابری
هفته هفته‌ی آینده روز روزه روزهای بعد بعدی
شهر شهره این آن اون چتر ببرم ببر بپوشم بپوشیم لازمه لازم باید
""".replace("\u200c", " ").split())


def _clean(text):
    text = text.replace("\u200c", " ")
    text = text.replace("ي", "ی").replace("ك", "ک")
    return text.strip()


def detect_day(message):
    """
    0 = امروز/الان، 1 = فردا، 2 = پس‌فردا، "week" = چند روز آینده،
    None = روز مشخص نشده (یعنی وضعیت فعلی + یه نگاه به فردا).
    """

    text = _clean(message)

    if "پس فردا" in text or "پسفردا" in text:
        return 2

    if "فردا" in text:
        return 1

    if (
        "هفته" in text
        or "روز آینده" in text
        or "روزهای آینده" in text
        or "چند روز" in text
        or "۳ روز" in text
        or "3 روز" in text
    ):
        return "week"

    if "امروز" in text or "الان" in text or "الآن" in text:
        return 0

    return None


def extract_city_name(message):
    """
    کلمه‌های مربوط به هوا و زمان رو از پیام حذف می‌کنه و اگه چیزی
    شبیه اسم شهر باقی موند برمی‌گردونه؛ وگرنه None.
    """

    text = _clean(message)
    text = re.sub(r"[؟?!.,،:;]", " ", text)

    words = []

    for word in text.split():

        if word in STOP_WORDS:
            continue

        if re.fullmatch(r"[0-9۰-۹]+", word):
            continue

        words.append(word)

    if not words or len(words) > 3:
        return None

    return " ".join(words)


def _get(url, params):

    response = requests.get(
        url,
        params=params,
        proxies=get_safe_proxies(),
        timeout=(5, 10)
    )

    response.raise_for_status()

    return response.json()


def geocode(name):
    """اسم شهر (فارسی یا انگلیسی) -> {name, latitude, longitude} یا None"""

    try:

        data = _get(GEOCODE_URL, {
            "name": name,
            "count": 1,
            "language": "fa",
            "format": "json"
        })

        results = data.get("results") or []

        if not results:
            return None

        first = results[0]

        return {
            "name": first.get("name") or name,
            "latitude": first["latitude"],
            "longitude": first["longitude"]
        }

    except Exception:
        return None


def fetch_forecast(latitude, longitude):

    return _get(FORECAST_URL, {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "wind_speed_10m_max"
        ]),
        "forecast_days": 4,
        "timezone": "auto"
    })


def describe(code):
    return WEATHER_CODES.get(code, ("وضعیت نامشخص", "🌡"))


def _day_label(index, iso_date):

    if index == 0:
        return "امروز"

    if index == 1:
        return "فردا"

    if index == 2:
        return "پس‌فردا"

    try:
        year, month, day = [int(part) for part in iso_date.split("-")]
        return WEEKDAYS_FA[date(year, month, day).weekday()]
    except Exception:
        return "روز " + str(index + 1)


def _day_values(daily, index):

    def pick(key):
        values = daily.get(key) or []
        return values[index] if index < len(values) else None

    return {
        "code": pick("weather_code"),
        "max": pick("temperature_2m_max"),
        "min": pick("temperature_2m_min"),
        "rain": pick("precipitation_probability_max"),
        "wind": pick("wind_speed_10m_max")
    }


def _num(value):

    if value is None:
        return "؟"

    return str(int(round(value)))


def build_tips(day, today=None):
    """
    توصیه‌ی کوتاه بر اساس خود پیش‌بینی. اینجا پیش‌بینی جدیدی
    ساخته نمی‌شه؛ فقط عددهای سرویس هواشناسی به نکته تبدیل می‌شن.
    """

    tips = []

    rain = day["rain"]
    high = day["max"]
    low = day["min"]
    wind = day["wind"]
    code = day["code"]

    snowy = code in (71, 73, 75, 77, 85, 86)

    if snowy:
        tips.append("برف میاد؛ لباس گرم و کفش مناسب یادت نره ❄️")
    elif rain is not None and rain >= 60:
        tips.append("احتمال بارش بالاست؛ چتر یا بارونی با خودت ببر ☔")
    elif rain is not None and rain >= 30:
        tips.append("یه کم احتمال بارش هست؛ چتر تو کیفت بد نیست 🌂")

    if high is not None and high >= 35:
        tips.append("هوا خیلی گرمه؛ آب زیاد بخور و ظهر از آفتاب دوری کن 🥵")
    elif high is not None and high >= 28:
        tips.append("هوا گرمه؛ لباس سبک بپوش 👕")
    elif high is not None and high <= 5:
        tips.append("هوا سرده؛ لباس گرم بپوش 🧥")

    if low is not None and low <= 0:
        tips.append("شب و صبح زود احتمال یخبندان هست 🧊")

    if high is not None and low is not None and (high - low) >= 15:
        tips.append("اختلاف دمای صبح و عصر زیاده؛ لایه‌لایه بپوش 🧣")

    if wind is not None and wind >= 40:
        tips.append("باد نسبتاً شدیده؛ مراقب وسایل سبک باش 💨")

    if today and today["max"] is not None and high is not None:

        diff = high - today["max"]

        if diff >= 4:
            tips.append("نسبت به امروز حدود " + _num(diff) + " درجه گرم‌تر می‌شه 📈")
        elif diff <= -4:
            tips.append("نسبت به امروز حدود " + _num(-diff) + " درجه خنک‌تر می‌شه 📉")

    return tips


def _day_block(label, day):

    text, emoji = describe(day["code"])

    line = (
        emoji + " " + label + ": " + text +
        "، بین " + _num(day["min"]) + " تا " + _num(day["max"]) + " درجه"
    )

    extras = []

    if day["rain"] is not None:
        extras.append("احتمال بارش " + _num(day["rain"]) + "٪")

    if day["wind"] is not None:
        extras.append("باد تا " + _num(day["wind"]) + " km/h")

    if extras:
        line += "\n   " + " | ".join(extras)

    return line


def resolve_city(message, saved_city=None):
    """
    اولویت: شهری که توی خود پیام نوشته شده > شهر ذخیره‌شده‌ی کاربر > تهران
    """

    name = extract_city_name(message)

    if name:
        found = geocode(name)
        if found:
            return found

    if saved_city:
        found = geocode(saved_city)
        if found:
            return found

    return DEFAULT_CITY


def build_answer(message, saved_city=None):

    city = resolve_city(message, saved_city)

    try:
        data = fetch_forecast(city["latitude"], city["longitude"])
    except Exception:
        return "الان نتونستم به سرویس آب‌وهوا وصل بشم. چند لحظه‌ی دیگه دوباره امتحان کن 🙏"

    daily = data.get("daily") or {}
    dates = daily.get("time") or []

    if not dates:
        return "اطلاعات آب‌وهوا دریافت نشد. دوباره امتحان کن."

    days = [_day_values(daily, i) for i in range(len(dates))]

    which = detect_day(message)

    header = "📍 " + city["name"] + "\n"

    if which == "week":

        blocks = [
            _day_block(_day_label(i, dates[i]), days[i])
            for i in range(len(days))
        ]

        return header + "\n".join(blocks)

    if which in (1, 2) and which < len(days):

        label = _day_label(which, dates[which])

        answer = header + _day_block(label, days[which])

        tips = build_tips(days[which], today=days[0])

        if tips:
            answer += "\n\n" + "\n".join(tips)

        return answer

    current = data.get("current") or {}

    current_text, current_emoji = describe(current.get("weather_code"))

    answer = (
        header +
        current_emoji + " الان: " + current_text +
        "، حدود " + _num(current.get("temperature_2m")) + " درجه"
    )

    if which == 0:

        answer += "\n" + _day_block("امروز", days[0])

        tips = build_tips(days[0])

        if tips:
            answer += "\n\n" + "\n".join(tips)

        return answer

    # روز مشخص نشده: وضعیت فعلی + یه نگاه سریع به فردا
    if len(days) > 1:
        answer += "\n" + _day_block("فردا", days[1])

        tips = build_tips(days[1], today=days[0])

        if tips:
            answer += "\n\n" + "\n".join(tips)

    return answer


def get_weather():
    """سازگاری با نسخه‌ی قبلی: دما و کد وضعیت فعلی تهران"""

    data = fetch_forecast(DEFAULT_CITY["latitude"], DEFAULT_CITY["longitude"])

    return data["current"]["temperature_2m"], data["current"]["weather_code"]
