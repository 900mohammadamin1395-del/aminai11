# -*- coding: utf-8 -*-

import ast
import operator
import re


# فقط همین عملگرها مجازن؛ هیچ چیز دیگه‌ای (فراخوانی تابع، اسم متغیر و ...)
# اجازه‌ی اجرا نداره، برای همینه که این روش امن‌تر از eval() ساده‌ست.
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

TRIGGER_WORDS = [
    "ماشین حساب",
    "حساب کن",
    "حساب کنی",
    "چند میشه",
    "چند می شود",
    "چقدر میشه",
    "چقدر می شود",
    "برابره با چند",
    "مساویه با چند",
    "جوابش چنده"
]

WORD_OPERATORS = {
    "به علاوه": "+",
    "بعلاوه": "+",
    "جمع": "+",
    "منهای": "-",
    "تفریق": "-",
    "ضربدر": "*",
    "ضرب در": "*",
    "ضرب": "*",
    "تقسیم بر": "/",
    "تقسیم": "/",
    "به توان": "**",
    "توان": "**",
    "باقیمانده": "%"
}

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ENGLISH_DIGITS = "0123456789"

DIGIT_MAP = str.maketrans(
    PERSIAN_DIGITS + ARABIC_DIGITS,
    ENGLISH_DIGITS + ENGLISH_DIGITS
)

FULL_EXPRESSION_PATTERN = re.compile(r"^[\d\.\+\-\*/%\(\)\s]+$")


def _normalize(text):

    text = text.translate(DIGIT_MAP)

    text = text.replace("×", "*")
    text = text.replace("÷", "/")
    text = text.replace("^", "**")

    # جایگزین کردن کلمات ریاضی فارسی با علامت‌های واقعی، طولانی‌ترین‌ها اول
    for word in sorted(WORD_OPERATORS, key=len, reverse=True):
        text = text.replace(word, " " + WORD_OPERATORS[word] + " ")

    return text


def _extract_expression(text):

    pieces = re.findall(r"[0-9\.\+\-\*/%\(\)\s]+", text)

    candidate = "".join(pieces)

    candidate = re.sub(r"\s+", " ", candidate).strip()

    if not re.search(r"\d", candidate):
        return None

    if not re.search(r"[\+\-\*/%]", candidate):
        return None

    return candidate


def _safe_eval(node):

    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)

    if isinstance(node, ast.Constant):

        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value

        raise ValueError("invalid constant")

    if isinstance(node, ast.BinOp):

        op_func = OPERATORS.get(type(node.op))

        if op_func is None:
            raise ValueError("invalid operator")

        return op_func(_safe_eval(node.left), _safe_eval(node.right))

    if isinstance(node, ast.UnaryOp):

        op_func = OPERATORS.get(type(node.op))

        if op_func is None:
            raise ValueError("invalid operator")

        return op_func(_safe_eval(node.operand))

    raise ValueError("invalid expression")


def _format_result(result):

    if isinstance(result, float) and result.is_integer():
        result = int(result)

    elif isinstance(result, float):
        result = round(result, 6)

    return str(result)


def detect_and_calculate(message):
    """
    Returns a Persian answer string like "🧮 نتیجه: 42" if the message is
    (or clearly contains) a math expression, otherwise returns None so
    the caller can fall through to other handlers.

    Two ways this triggers:
      1. The whole message, once normalized, is nothing but numbers and
         operators — e.g. "25 * 4" or "١٢٫٥ + ٧" — so plain calculator-
         style typing just works.
      2. The message contains an explicit trigger phrase like
         "حساب کن" or "چند میشه", in which case the math part is pulled
         out of the surrounding sentence.
    """

    text = message.strip()

    if not text:
        return None

    normalized = _normalize(text)

    if (
        FULL_EXPRESSION_PATTERN.match(normalized)
        and re.search(r"\d", normalized)
        and re.search(r"[\+\-\*/%]", normalized)
    ):
        expression = normalized.strip()

    else:

        has_trigger = any(word in text for word in TRIGGER_WORDS)

        if not has_trigger:
            return None

        expression = _extract_expression(normalized)

        if not expression:
            return None

    try:
        parsed = ast.parse(expression, mode="eval")
        result = _safe_eval(parsed)

    except ZeroDivisionError:
        return "نمیشه یه عدد رو بر صفر تقسیم کرد 🚫"

    except Exception:
        return None

    return "🧮 نتیجه: " + _format_result(result)
