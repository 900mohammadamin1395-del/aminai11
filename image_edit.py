# -*- coding: utf-8 -*-

"""
ویرایش عکس آپلودشده بر اساس پرامپت فارسی، به‌صورت کاملاً لوکال با Pillow
(بدون نیاز به اینترنت یا سرویس بیرونی).

مسیر کار:
    save_upload(file_storage)  ->  عکس رو اعتبارسنجی و ذخیره می‌کنه
    build_answer(path, prompt) ->  افکت‌های خواسته‌شده رو اعمال می‌کنه
"""

import os
import re
import uuid

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

import image_ai


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
RESULT_DIR = os.path.join(BASE_DIR, "static", "generated")

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_SIDE = 2048

ALLOWED_FORMATS = ("JPEG", "PNG", "WEBP", "GIF")


class UploadError(Exception):
    """پیام این خطا مستقیم به کاربر نشون داده می‌شه"""


# ---------------------------------------------------------------- آپلود

def _new_name(extension):
    return uuid.uuid4().hex + "." + extension


def save_upload(file_storage):
    """
    فایل آپلودشده رو با Pillow باز می‌کنه (نه فقط با پسوند اسمش)،
    چرخش EXIF رو اعمال می‌کنه، اگه خیلی بزرگ بود کوچیکش می‌کنه و با
    یک اسم تصادفی ذخیره می‌کنه. اسم اصلی فایل کاربر هیچ‌جا استفاده نمی‌شه.

    برمی‌گردونه: (مسیر فایل روی دیسک، آدرس /static/...)
    """

    data = file_storage.read(MAX_UPLOAD_BYTES + 1)

    if not data:
        raise UploadError("فایل خالیه.")

    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadError("حجم عکس بیشتر از ۸ مگابایته. یه عکس کوچیک‌تر انتخاب کن.")

    import io

    try:
        probe = Image.open(io.BytesIO(data))
        probe.verify()
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception:
        raise UploadError("این فایل یه عکس معتبر نیست.")

    if image.format not in ALLOWED_FORMATS:
        raise UploadError("فقط عکس‌های JPG، PNG، WEBP و GIF پشتیبانی می‌شن.")

    image = ImageOps.exif_transpose(image)

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA" if "transparency" in image.info else "RGB")

    image.thumbnail((MAX_SIDE, MAX_SIDE))

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    if image.mode == "RGBA":
        name = _new_name("png")
        image.save(os.path.join(UPLOAD_DIR, name), "PNG")
    else:
        name = _new_name("jpg")
        image.save(os.path.join(UPLOAD_DIR, name), "JPEG", quality=92)

    return os.path.join(UPLOAD_DIR, name), "/static/uploads/" + name


# ------------------------------------------------------ متن پرامپت

def normalize(text):

    text = text.replace("\u200c", " ")
    text = text.replace("ي", "ی").replace("ك", "ک")

    digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

    text = text.translate(digits)

    return re.sub(r"\s+", " ", text).strip().lower()


# هر افکت: (اسم داخلی، توضیح برای کاربر، کلیدواژه‌ها)
EFFECTS = [
    ("grayscale", "سیاه‌وسفید", ["سیاه و سفید", "سیاه وسفید", "سیاه سفید", "مشکی و سفید", "مشکی وسفید", "مشکی سفید", "مونوکروم", "خاکستری", "black and white", "grayscale"]),
    ("sepia", "قدیمی (سپیا)", ["سپیا", "قدیمی", "وینتیج", "کلاسیک", "sepia", "vintage"]),
    ("sketch", "طرح مدادی", ["اسکچ", "طراحی", "مدادی", "طرح", "sketch"]),
    ("cartoon", "کارتونی", ["کارتون", "انیمه", "cartoon"]),
    ("pixelate", "پیکسلی", ["پیکسل", "pixel"]),
    ("invert", "رنگ‌های معکوس", ["نگاتیو", "معکوس", "برعکس رنگ", "invert"]),
    ("blur", "محو", ["بلور", "محو", "تار کن", "تارش", "blur"]),
    ("sharpen", "واضح‌تر", ["شارپ", "واضح", "تیز", "sharp"]),
    ("brighter", "روشن‌تر", ["روشن", "روشن‌تر", "نورانی", "bright"]),
    ("darker", "تیره‌تر", ["تیره", "تاریک", "کم نور", "dark"]),
    ("contrast", "کنتراست بیشتر", ["کنتراست", "contrast"]),
    ("vivid", "رنگ‌های زنده‌تر", ["رنگی تر", "زنده", "پررنگ", "سیر", "vivid"]),
    ("faded", "رنگ‌های ملایم‌تر", ["کم رنگ", "ملایم", "مات", "faded"]),
    ("warm", "تُن گرم", ["گرم تر", "تن گرم", "رنگ گرم", "warm"]),
    ("cool", "تُن سرد", ["سرد تر", "تن سرد", "رنگ سرد", "cool"]),
    ("mirror", "قرینه (آینه‌ای)", ["قرینه", "آینه", "mirror"]),
    ("flip", "وارونه (سر و ته)", ["وارونه", "سر و ته", "سرو ته", "flip"]),
    ("rotate", "چرخش", ["بچرخون", "بچرخان", "بچرخ", "چرخش", "rotate", "درجه"]),
    ("half", "نصف‌اندازه", ["نصف", "کوچیک", "کوچک", "کم حجم", "small"]),
    ("double", "دوبرابر", ["دو برابر", "دوبرابر", "بزرگ", "double"]),
    ("border", "قاب", ["قاب", "حاشیه", "فریم", "border", "frame"]),
]

DESCRIBE_WORDS = ["توصیف", "چیه", "چی هست", "چیست", "اطلاعات", "مشخصات", "ابعاد", "describe", "info"]


def find_effects(prompt):
    """افکت‌ها رو به ترتیبی که توی پرامپت اومدن برمی‌گردونه (هر کدوم یک‌بار)"""

    text = normalize(prompt)

    found = []

    for name, label, keywords in EFFECTS:

        positions = [text.find(normalize(k)) for k in keywords if normalize(k) in text]

        if positions:
            found.append((min(positions), name, label))

    found.sort()

    # روشن/تیره‌ی هم‌زمان معنی نداره؛ اولی که اومده رو نگه می‌داریم
    names = [n for _, n, _ in found]

    if "brighter" in names and "darker" in names:
        drop = "darker" if names.index("brighter") < names.index("darker") else "brighter"
        found = [f for f in found if f[1] != drop]

    return [(n, l) for _, n, l in found], text


# ------------------------------------------------------------- افکت‌ها

def _rgb(image):
    return image.convert("RGB")


def _sepia(image):
    gray = ImageOps.grayscale(_rgb(image))
    return ImageOps.colorize(gray, black="#2b1a0a", white="#f4e3c1", mid="#a07850")


def _sketch(image):
    gray = ImageOps.grayscale(_rgb(image))
    gray = gray.filter(ImageFilter.GaussianBlur(1.2))
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.invert(edges)
    return ImageOps.autocontrast(edges, cutoff=2).convert("RGB")


def _cartoon(image):
    rgb = _rgb(image)
    smooth = rgb.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.SMOOTH_MORE)
    flat = ImageOps.posterize(smooth, 3)
    flat = ImageEnhance.Color(flat).enhance(1.4)
    edges = ImageOps.grayscale(rgb).filter(ImageFilter.GaussianBlur(1)).filter(ImageFilter.FIND_EDGES)
    mask = edges.point(lambda v: 255 if v > 28 else 0).filter(ImageFilter.MaxFilter(3))
    outline = Image.new("RGB", flat.size, (20, 20, 20))
    return Image.composite(outline, flat, mask)


def _pixelate(image):
    rgb = _rgb(image)
    width, height = rgb.size
    block = max(6, min(width, height) // 48)
    small = rgb.resize((max(1, width // block), max(1, height // block)), Image.BILINEAR)
    return small.resize((width, height), Image.NEAREST)


def _tint(image, red, green, blue):
    rgb = _rgb(image)
    r, g, b = rgb.split()
    r = r.point(lambda v: min(255, int(v * red)))
    g = g.point(lambda v: min(255, int(v * green)))
    b = b.point(lambda v: min(255, int(v * blue)))
    return Image.merge("RGB", (r, g, b))


def _border(image):
    rgb = _rgb(image)
    size = max(12, min(rgb.size) // 25)
    framed = ImageOps.expand(rgb, border=size, fill=(255, 255, 255))
    return ImageOps.expand(framed, border=max(2, size // 6), fill=(30, 30, 30))


def _rotate_angle(text):

    match = re.search(r"(\d{1,3})\s*درجه", text)

    if match:
        return int(match.group(1)) % 360

    return 90


def apply_effect(image, name, text):

    if name == "grayscale":
        return ImageOps.grayscale(_rgb(image)).convert("RGB")
    if name == "sepia":
        return _sepia(image)
    if name == "sketch":
        return _sketch(image)
    if name == "cartoon":
        return _cartoon(image)
    if name == "pixelate":
        return _pixelate(image)
    if name == "invert":
        return ImageOps.invert(_rgb(image))
    if name == "blur":
        return _rgb(image).filter(ImageFilter.GaussianBlur(max(2, min(image.size) // 120)))
    if name == "sharpen":
        return _rgb(image).filter(ImageFilter.UnsharpMask(radius=2, percent=180, threshold=2))
    if name == "brighter":
        return ImageEnhance.Brightness(_rgb(image)).enhance(1.35)
    if name == "darker":
        return ImageEnhance.Brightness(_rgb(image)).enhance(0.7)
    if name == "contrast":
        return ImageEnhance.Contrast(_rgb(image)).enhance(1.4)
    if name == "vivid":
        return ImageEnhance.Color(_rgb(image)).enhance(1.6)
    if name == "faded":
        return ImageEnhance.Color(_rgb(image)).enhance(0.55)
    if name == "warm":
        return _tint(image, 1.12, 1.0, 0.86)
    if name == "cool":
        return _tint(image, 0.88, 1.0, 1.12)
    if name == "mirror":
        return ImageOps.mirror(_rgb(image))
    if name == "flip":
        return ImageOps.flip(_rgb(image))
    if name == "rotate":
        return _rgb(image).rotate(-_rotate_angle(text), expand=True, fillcolor=(255, 255, 255))
    if name == "half":
        return _rgb(image).resize((max(1, image.width // 2), max(1, image.height // 2)), Image.LANCZOS)
    if name == "double":
        width, height = image.width * 2, image.height * 2
        if max(width, height) > MAX_SIDE * 2:
            return _rgb(image)
        return _rgb(image).resize((width, height), Image.LANCZOS)
    if name == "border":
        return _border(image)

    return _rgb(image)


# ------------------------------------------------------------ توصیف

PALETTE = [
    ("قرمز", (200, 40, 40)), ("نارنجی", (235, 130, 40)), ("زرد", (230, 210, 60)),
    ("سبز", (60, 160, 70)), ("فیروزه‌ای", (50, 180, 180)), ("آبی", (50, 90, 200)),
    ("بنفش", (130, 70, 180)), ("صورتی", (235, 130, 170)), ("قهوه‌ای", (120, 80, 45)),
    ("سفید", (240, 240, 240)), ("خاکستری", (128, 128, 128)), ("مشکی", (20, 20, 20))
]


def _closest_color_name(rgb):

    best = min(
        PALETTE,
        key=lambda item: sum((a - b) ** 2 for a, b in zip(item[1], rgb))
    )

    return best[0]


def describe_image(image):

    small = _rgb(image).resize((1, 1), Image.BOX)

    average = small.getpixel((0, 0))

    brightness = sum(average) / 3

    if brightness > 170:
        light = "روشن"
    elif brightness < 85:
        light = "تیره"
    else:
        light = "متوسط"

    orientation = (
        "افقی" if image.width > image.height * 1.1
        else "عمودی" if image.height > image.width * 1.1
        else "تقریباً مربع"
    )

    return (
        "🖼️ عکس " + orientation + " با ابعاد " + str(image.width) + "×" + str(image.height) +
        "، رنگ غالب " + _closest_color_name(average) + " و نور " + light + "."
    )


# ---------------------------------------------------------- خروجی

HELP_TEXT = (
    "عکس رو گرفتم 👍 ولی نفهمیدم باهاش چی کار کنم.\n"
    "این‌ها رو می‌تونی بنویسی:\n"
    "• سیاه‌وسفیدش کن / قدیمی کن / کارتونی کن / طرح مدادی کن / پیکسلی کن\n"
    "• روشن‌تر کن / تیره‌تر کن / کنتراست بده / رنگ‌هاش رو زنده‌تر کن / گرم‌تر کن\n"
    "• شارپ کن / محو کن / قرینه کن / وارونه کن / ۹۰ درجه بچرخون\n"
    "• قاب بزن / نصف کن / دو برابر کن\n"
    "• چند تا رو با هم هم می‌شه: «سیاه و سفید کن و قاب بزن»\n"
    "• «توصیفش کن» هم بزنی مشخصات عکس رو می‌گم.\n"
    "• برای تغییرهای خلاقانه بنویس «با هوش مصنوعی ...» (مثلاً: با هوش مصنوعی تبدیلش کن به نقاشی آبرنگ)."
)


AI_NOT_READY_TEXT = (
    "ساخت عکس با هوش مصنوعی هنوز روی این سرور تنظیم نشده. "
    "(مدیر برنامه باید کلید API رو توی POLLINATIONS_KEY ست کنه.)"
)


def _local_edit(image, effects, text, wants_description):

    result = image

    for name, _label in effects:
        result = apply_effect(result, name, text)

    os.makedirs(RESULT_DIR, exist_ok=True)

    filename = _new_name("png")

    result.save(os.path.join(RESULT_DIR, filename), "PNG")

    labels = "، ".join(label for _name, label in effects)

    answer = "🎨 انجام شد: " + labels

    if wants_description:
        answer += "\n" + describe_image(image)

    return answer, "/static/generated/" + filename


def build_answer(image_path, prompt, upload_url=None, user_id=None):
    """
    برمی‌گردونه: (متن جواب، آدرس عکس نتیجه یا None)

    مسیر انتخاب:
      ۱) کاربر صراحتاً «با هوش مصنوعی» خواسته -> AI
      ۲) افکت ساده‌ی شناخته‌شده (سیاه‌وسفید، قاب، چرخش...) -> Pillow (سریع و رایگان)
      ۳) درخواست آزاد و نامشخص (مثلاً «تبدیلش کن به نقاشی آبرنگ») -> AI
    """

    image = Image.open(image_path)
    image.load()

    forced_ai = image_ai.wants_ai(prompt)

    ai_prompt = image_ai.clean_prompt(prompt) if forced_ai else prompt

    effects, text = find_effects(ai_prompt)

    wants_description = any(normalize(word) in text for word in DESCRIBE_WORDS)

    use_ai = False

    if forced_ai:
        use_ai = True
    elif not effects and not wants_description and text:
        use_ai = image_ai.is_configured()

    if use_ai:

        result_url, error = image_ai.generate(image_path, ai_prompt, user_id)

        if result_url:
            return "✨ با هوش مصنوعی ساختمش:", result_url

        if error == "not_configured":
            error = AI_NOT_READY_TEXT

        # اگه افکت ساده هم توی درخواست بود، به‌جای شکست کامل، همون رو انجام می‌دیم
        if effects:
            answer, url = _local_edit(image, effects, text, wants_description)
            return error + "\nبه‌جاش افکت ساده رو انجام دادم:\n" + answer, url

        return error, None

    if not effects:

        if wants_description or not text:
            answer = describe_image(image)

            if not text:
                answer += "\n\nبنویس باهاش چی کار کنم؛ مثلاً «سیاه‌وسفیدش کن» یا «کارتونی کن»."

            return answer, None

        return HELP_TEXT, None

    return _local_edit(image, effects, text, wants_description)
