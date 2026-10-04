# -*- coding: utf-8 -*-

import json
import os
import time
import uuid
import threading


DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "conversations.json"
)

_lock = threading.Lock()


def _load():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_conversations(user_id):

    with _lock:
        data = _load()

    user_convs = data.get(user_id, {})

    items = []

    for conv_id, conv in user_convs.items():

        items.append({
            "id": conv_id,
            "title": conv.get("title", "گفتگوی بدون عنوان"),
            "updated": conv.get("updated", 0)
        })

    items.sort(key=lambda c: c["updated"], reverse=True)

    return items


def create_conversation(user_id):

    conv_id = uuid.uuid4().hex[:12]

    now = time.time()

    conv = {
        "id": conv_id,
        "title": "گفتگوی جدید",
        "created": now,
        "updated": now,
        "messages": []
    }

    with _lock:
        data = _load()

        if user_id not in data:
            data[user_id] = {}

        data[user_id][conv_id] = conv

        _save(data)

    return conv


def get_conversation(user_id, conv_id):

    with _lock:
        data = _load()

    return data.get(user_id, {}).get(conv_id)


def delete_conversation(user_id, conv_id):

    with _lock:
        data = _load()

        user_convs = data.get(user_id, {})

        if conv_id in user_convs:
            del user_convs[conv_id]
            _save(data)
            return True

        return False


def delete_all_conversations(user_id):

    with _lock:
        data = _load()

        if user_id in data:
            data[user_id] = {}
            _save(data)

        return True


def rename_conversation(user_id, conv_id, title):

    title = title.strip()

    if not title:
        return False

    with _lock:
        data = _load()

        user_convs = data.get(user_id, {})

        if conv_id not in user_convs:
            return False

        user_convs[conv_id]["title"] = title[:60]
        user_convs[conv_id]["updated"] = time.time()

        _save(data)

        return True


def set_current_riddle(user_id, conv_id, riddle):

    with _lock:
        data = _load()

        user_convs = data.get(user_id, {})

        if conv_id not in user_convs:
            return False

        user_convs[conv_id]["current_riddle"] = riddle

        _save(data)

        return True


def get_current_riddle(user_id, conv_id):

    with _lock:
        data = _load()

    conv = data.get(user_id, {}).get(conv_id)

    if not conv:
        return None

    return conv.get("current_riddle")


def clear_current_riddle(user_id, conv_id):

    with _lock:
        data = _load()

        user_convs = data.get(user_id, {})

        if conv_id in user_convs and "current_riddle" in user_convs[conv_id]:
            del user_convs[conv_id]["current_riddle"]
            _save(data)


def get_rps_score(user_id, conv_id):

    with _lock:
        data = _load()

    conv = data.get(user_id, {}).get(conv_id)

    if not conv:
        return {"user": 0, "bot": 0}

    return conv.get("rps_score", {"user": 0, "bot": 0})


def update_rps_score(user_id, conv_id, winner):

    with _lock:
        data = _load()

        user_convs = data.get(user_id, {})

        if conv_id not in user_convs:
            return {"user": 0, "bot": 0}

        conv = user_convs[conv_id]

        score = conv.get("rps_score", {"user": 0, "bot": 0})

        if winner == "user":
            score["user"] = score.get("user", 0) + 1
        elif winner == "bot":
            score["bot"] = score.get("bot", 0) + 1

        conv["rps_score"] = score

        _save(data)

        return score


def reset_rps_score(user_id, conv_id):

    with _lock:
        data = _load()

        user_convs = data.get(user_id, {})

        if conv_id in user_convs and "rps_score" in user_convs[conv_id]:
            del user_convs[conv_id]["rps_score"]
            _save(data)


def add_message(user_id, conv_id, role, text, image_url=None, gif_url=None, melody=None, code=None):

    with _lock:
        data = _load()

        user_convs = data.get(user_id, {})

        if conv_id not in user_convs:
            return None

        conv = user_convs[conv_id]

        message = {
            "role": role,
            "text": text,
            "time": time.time()
        }

        if image_url:
            message["image_url"] = image_url

        if gif_url:
            message["gif_url"] = gif_url

        if melody:
            message["melody"] = melody

        if code:
            message["code"] = code

        conv["messages"].append(message)

        conv["updated"] = time.time()

        auto_title_needed = (
            conv.get("title") == "گفتگوی جدید"
            and role == "user"
        )

        if auto_title_needed:

            short_title = text.strip()

            if len(short_title) > 40:
                short_title = short_title[:40] + "…"

            conv["title"] = short_title if short_title else "گفتگوی جدید"

        _save(data)

        return conv
