# -*- coding: utf-8 -*-

import random
import re


START_PHRASES = [
    "سنگ کاغذ قیچی",
    "بازی با ربات",
    "بازی سنگ کاغذ",
    "بریم بازی کنیم",
    "یه بازی کنیم",
    "بازی کنیم"
]

MOVES = ["سنگ", "کاغذ", "قیچی"]

# کلید می‌بره روی مقدارش: سنگ می‌بره قیچی رو، قیچی می‌بره کاغذ رو،
# کاغذ می‌بره سنگ رو
BEATS = {
    "سنگ": "قیچی",
    "قیچی": "کاغذ",
    "کاغذ": "سنگ"
}

MOVE_EMOJI = {
    "سنگ": "🪨",
    "کاغذ": "📄",
    "قیچی": "✂️"
}


def detect_start(message):

    text = message.strip()

    return any(phrase in text for phrase in START_PHRASES)


def detect_move(message):

    text = message.strip()

    # پیام‌های طولانی احتمالاً یه جمله‌ی معمولین که این کلمات توشون
    # به‌طور اتفاقی اومده، نه یه حرکت واقعی توی بازی
    if len(text) > 12:
        return None

    for move in MOVES:

        pattern = r"\b" + re.escape(move) + r"\b"

        if re.search(pattern, text):
            return move

    return None


def build_intro():

    return (
        "✊📄✂️ بازی سنگ‌کاغذقیچی شروع شد!\n"
        "فقط بنویس «سنگ»، «کاغذ» یا «قیچی» تا اولین دستت رو ببینم."
    )


def play_round(user_move):

    bot_move = random.choice(MOVES)

    if user_move == bot_move:
        result = "تساوی 😐"
        winner = "tie"

    elif BEATS[user_move] == bot_move:
        result = "بردی! 🎉"
        winner = "user"

    else:
        result = "باختی 😅"
        winner = "bot"

    text = (
        "تو: " + MOVE_EMOJI[user_move] + " " + user_move + "\n" +
        "من: " + MOVE_EMOJI[bot_move] + " " + bot_move + "\n\n" +
        result
    )

    return text, winner
