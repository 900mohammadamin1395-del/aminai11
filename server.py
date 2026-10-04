# -*- coding: utf-8 -*-

import os
import secrets

from flask import Flask, request, jsonify, render_template, session, redirect, url_for

from brain import think, remember, recall
from web_search import web_search
import weather
import conversations
import users
import user_memory
import google_auth
import image_gen
import gif_gen
import music_gen
import code_gen
import calculator
import translator
import hafez_gen
import news_briefing
import riddle_gen
import dream_gen
import name_gen
import occasions_countdown
import rps_gen
import date_converter
import image_edit


app = Flask(__name__)

app.secret_key = os.environ.get("AMIN_SECRET_KEY", "amin-ai-secret-key-change-me")

# سقف حجم کل درخواست (عکس تا ۸ مگابایت + کمی فضای اضافه)
app.config["MAX_CONTENT_LENGTH"] = 9 * 1024 * 1024


@app.errorhandler(413)
def too_large(error):
    return jsonify({"answer": "حجم عکس زیاده. یه عکس کوچیک‌تر (زیر ۸ مگابایت) انتخاب کن."}), 413


WEATHER_WORDS = ["هوا", "دمای", "بارون", "باران", "چتر ببر", "برف میاد"]


def is_weather_question(message):

    text = message.replace("\u200c", " ")

    return any(word in text for word in WEATHER_WORDS)


def weather_answer(message, user_id):

    saved_city = user_memory.get_fact(user_id, "city")

    return weather.build_answer(message, saved_city)


def needs_search(message):

    text = message.lower()

    words = [
        "آخرین",
        "جدیدترین",
        "امروز",
        "امسال",
        "قیمت",
        "خبر",
        "اخبار",
        "کی میاد",
        "چه زمانی",
        "چند است",
        "چنده",
        "نسخه جدید"
    ]

    for word in words:

        if word in text:
            return True

    return False


def memory_answer(message, messages):

    text = message.lower()

    if (
        "چی گفتم" in text
        or "یادت هست" in text
    ):

        if messages:
            return "آره، پیام‌های این گفتگو رو یادم هست 🧠💾"

        return "فعلاً چیزی در این گفتگو نگفتی."

    return None


def current_user():
    return session.get("username")


def require_login():
    return bool(current_user())


@app.route("/")
def home():

    if not current_user():
        return render_template("login.html", google_enabled=google_auth.is_configured())

    return render_template(
        "chat.html",
        is_google_account=users.is_google_user(current_user())
    )


@app.route("/register")
def register_page():

    if current_user():
        return render_template("chat.html")

    return render_template("register.html", google_enabled=google_auth.is_configured())


@app.route("/api/register", methods=["POST"])
def api_register():

    data = request.get_json() or {}

    username = data.get("username", "")
    password = data.get("password", "")

    error = users.validate_credentials(username, password)

    if error:
        return jsonify({"success": False, "error": error})

    if users.user_exists(username):
        return jsonify({"success": False, "error": "این نام کاربری قبلاً ثبت شده است."})

    users.create_user(username, password)

    session["username"] = username.strip().lower()

    return jsonify({"success": True})


@app.route("/login", methods=["POST"])
def login():

    data = request.get_json() or {}

    username = data.get("username", "")
    password = data.get("password", "")

    if users.verify_user(username, password):

        session["username"] = username.strip().lower()

        return jsonify({"success": True})

    return jsonify({"success": False})


@app.route("/logout", methods=["POST"])
def logout():

    session.pop("username", None)

    return jsonify({"success": True})


@app.route("/login/google")
def login_google():

    if not google_auth.is_configured():
        return render_template(
            "login.html",
            google_enabled=False,
            google_error="ورود با گوگل هنوز روی این سرور تنظیم نشده است."
        )

    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state

    redirect_uri = url_for("login_google_callback", _external=True)

    return redirect(google_auth.build_auth_url(redirect_uri, state))


@app.route("/login/google/callback")
def login_google_callback():

    if not google_auth.is_configured():
        return redirect(url_for("home"))

    if request.args.get("error"):
        return redirect(url_for("home"))

    state = request.args.get("state")

    if not state or state != session.pop("oauth_state", None):
        return redirect(url_for("home"))

    code = request.args.get("code")

    if not code:
        return redirect(url_for("home"))

    redirect_uri = url_for("login_google_callback", _external=True)

    try:

        token_data = google_auth.exchange_code(code, redirect_uri)

        access_token = token_data.get("access_token")

        email, verified = google_auth.get_user_email(access_token)

    except Exception:
        return redirect(url_for("home"))

    if not email or not verified:
        return redirect(url_for("home"))

    if not users.user_exists(email):
        users.create_google_user(email)

    session["username"] = email.strip().lower()

    return redirect(url_for("home"))


@app.route("/api/conversations", methods=["GET"])
def api_list_conversations():

    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    return jsonify(conversations.list_conversations(current_user()))


@app.route("/api/conversations", methods=["POST"])
def api_create_conversation():

    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    conv = conversations.create_conversation(current_user())

    return jsonify({
        "id": conv["id"],
        "title": conv["title"]
    })


@app.route("/api/conversations/<conv_id>", methods=["GET"])
def api_get_conversation(conv_id):

    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    conv = conversations.get_conversation(current_user(), conv_id)

    if conv is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(conv)


@app.route("/api/conversations/<conv_id>", methods=["DELETE"])
def api_delete_conversation(conv_id):

    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    ok = conversations.delete_conversation(current_user(), conv_id)

    if not ok:
        return jsonify({"error": "not found"}), 404

    return jsonify({"success": True})


@app.route("/api/conversations/<conv_id>/rename", methods=["POST"])
def api_rename_conversation(conv_id):

    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json() or {}

    title = data.get("title", "")

    ok = conversations.rename_conversation(current_user(), conv_id, title)

    if not ok:
        return jsonify({"error": "invalid"}), 400

    return jsonify({"success": True})


@app.route("/api/conversations", methods=["DELETE"])
def api_delete_all_conversations():

    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    conversations.delete_all_conversations(current_user())

    return jsonify({"success": True})


@app.route("/api/memory", methods=["GET"])
def api_get_memory():

    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    return jsonify(user_memory.get_all_facts(current_user()))


@app.route("/api/memory/<key>", methods=["DELETE"])
def api_delete_memory(key):

    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    ok = user_memory.delete_fact(current_user(), key)

    if not ok:
        return jsonify({"error": "not found"}), 404

    return jsonify({"success": True})


@app.route("/api/change-password", methods=["POST"])
def api_change_password():

    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json() or {}

    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")

    error = users.change_password(current_user(), old_password, new_password)

    if error:
        return jsonify({"success": False, "error": error})

    return jsonify({"success": True})


@app.route("/api/account", methods=["DELETE"])
def api_delete_account():

    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    user_id = current_user()

    users.delete_user(user_id)
    conversations.delete_all_conversations(user_id)
    user_memory.delete_all_facts(user_id)

    session.pop("username", None)

    return jsonify({"success": True})


def handle_image_message(user_id, conv_id, message, uploaded_image):

    try:
        image_path, upload_url = image_edit.save_upload(uploaded_image)

    except image_edit.UploadError as error:

        return jsonify({
            "answer": str(error),
            "conversation_id": conv_id
        })

    conversations.add_message(
        user_id,
        conv_id,
        "user",
        message or "🖼️ (عکس ارسال شد)",
        image_url=upload_url
    )

    try:
        answer, result_url = image_edit.build_answer(
            image_path,
            message,
            upload_url=upload_url,
            user_id=user_id
        )

    except Exception:
        answer, result_url = "متأسفانه در پردازش عکس مشکلی پیش اومد 😕", None

    updated_conv = conversations.add_message(
        user_id,
        conv_id,
        "assistant",
        answer,
        image_url=result_url
    )

    return jsonify({

        "answer": answer,

        "image_url": result_url,

        "gif_url": None,

        "melody": None,

        "code": None,

        "conversation_id": conv_id,

        "title": updated_conv["title"] if updated_conv else "گفتگوی جدید"

    })


@app.route("/chat", methods=["POST"])
def chat():

    user_id = current_user()

    if not user_id:

        return jsonify({
            "answer": "لطفاً ابتدا وارد شوید."
        }), 401


    uploaded_image = None

    if request.mimetype == "multipart/form-data":

        message = (request.form.get("message") or "").strip()

        conv_id = request.form.get("conversation_id") or None

        if conv_id in ("null", "undefined"):
            conv_id = None

        uploaded_image = request.files.get("image")

    else:

        data = request.get_json() or {}

        message = data.get(
            "message",
            ""
        ).strip()

        conv_id = data.get("conversation_id")


    if not message and not uploaded_image:

        return jsonify({
            "answer": "پیامی دریافت نشد."
        })


    conv = None

    if conv_id:
        conv = conversations.get_conversation(user_id, conv_id)

    if conv is None:
        conv = conversations.create_conversation(user_id)
        conv_id = conv["id"]


    if uploaded_image is not None and uploaded_image.filename:

        return handle_image_message(user_id, conv_id, message, uploaded_image)


    conversations.add_message(
        user_id,
        conv_id,
        "user",
        message
    )


    existing_messages = conv.get("messages", [])

    image_url = None
    gif_url = None
    melody = None
    code_snippet = None

    answer = remember(user_id, message)

    if answer is None:
        answer = recall(user_id, message)

    if answer is None:
        answer = memory_answer(message, existing_messages)


    if answer is None:

        if riddle_gen.detect_answer_request(message):

            pending_riddle = conversations.get_current_riddle(user_id, conv_id)

            answer = riddle_gen.build_answer_message(pending_riddle)

            conversations.clear_current_riddle(user_id, conv_id)

        elif riddle_gen.detect_riddle_request(message):

            riddle = riddle_gen.pick_riddle()

            conversations.set_current_riddle(user_id, conv_id, riddle)

            answer = riddle_gen.build_riddle_message(riddle)


    if answer is None:
        answer = calculator.detect_and_calculate(message)


    if answer is None:
        answer = translator.build_answer(message)


    if answer is None:

        if hafez_gen.detect_request(message):
            answer = hafez_gen.build_answer()


    if answer is None:

        if news_briefing.detect_request(message):
            answer = news_briefing.build_briefing()


    if answer is None:

        if dream_gen.detect_request(message):
            answer = dream_gen.build_answer(message)


    if answer is None:

        if name_gen.detect_request(message):
            answer = name_gen.build_answer(message)


    if answer is None:

        if occasions_countdown.detect_request(message):
            answer = occasions_countdown.build_answer(message)


    if answer is None:

        if date_converter.detect_request(message):
            answer = date_converter.build_answer(message)


    if answer is None:

        if rps_gen.detect_start(message):

            conversations.reset_rps_score(user_id, conv_id)

            answer = rps_gen.build_intro()

        else:

            user_move = rps_gen.detect_move(message)

            if user_move:

                round_text, winner = rps_gen.play_round(user_move)

                score = conversations.update_rps_score(user_id, conv_id, winner)

                answer = (
                    round_text +
                    "\n\n📊 امتیاز: تو " + str(score["user"]) +
                    " - " + str(score["bot"]) + " من"
                )


    if answer is None:

        gif_prompt = gif_gen.detect_prompt(message)

        if gif_prompt:

            gif_url = gif_gen.generate_gif(gif_prompt)

            if gif_url:
                answer = "🌀 بفرما، این هم گیفی که خواستی:"
            else:
                answer = "متأسفانه در ساخت گیف مشکلی پیش اومد، یه بار دیگه امتحان کن 😕"


    if answer is None:

        image_prompt = image_gen.detect_prompt(message)

        if image_prompt:
            image_prompt, is_grayscale = image_gen.strip_grayscale_request(image_prompt)
            image_url = image_gen.build_image_url(image_prompt, grayscale=is_grayscale)
            answer = "🎨 بفرما، این هم عکسی که خواستی:"


    if answer is None:

        if music_gen.detect_request(message):
            melody = music_gen.generate_melody(message)
            answer = "🎵 بفرما، یه آهنگ " + melody["mood"] + " برات ساختم:"


    if answer is None:

        code_result = code_gen.detect_request(message)

        if code_result:
            code_snippet = code_result
            answer = "🐍 بفرما، کد " + code_result["title"] + ":"


    if answer is None:

        if is_weather_question(message):

            answer = weather_answer(message, user_id)


        elif needs_search(message):

            answer = web_search(message)


        else:

            answer = think(message)

            if answer is None:

                answer = web_search(message)


    updated_conv = conversations.add_message(
        user_id,
        conv_id,
        "assistant",
        answer,
        image_url=image_url,
        gif_url=gif_url,
        melody=melody,
        code=code_snippet
    )


    return jsonify({

        "answer": answer,

        "image_url": image_url,

        "gif_url": gif_url,

        "melody": melody,

        "code": code_snippet,

        "conversation_id": conv_id,

        "title": updated_conv["title"] if updated_conv else "گفتگوی جدید"

    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
