# -*- coding: utf-8 -*-


TEMPLATES = [

    {
        "keywords": ["فاکتوریل"],
        "title": "محاسبه‌ی فاکتوریل",
        "code": """def factorial(n):
    # فاکتوریل یک عدد رو با حلقه حساب می‌کنیم
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


number = int(input("یک عدد وارد کن: "))
print("فاکتوریل", number, "برابر است با", factorial(number))"""
    },

    {
        "keywords": ["فیبوناچی"],
        "title": "دنباله‌ی فیبوناچی",
        "code": """def fibonacci(count):
    sequence = [0, 1]
    for i in range(2, count):
        sequence.append(sequence[-1] + sequence[-2])
    return sequence[:count]


n = int(input("چند جمله می‌خوای؟ "))
print(fibonacci(n))"""
    },

    {
        "keywords": ["عدد اول", "اعداد اول"],
        "title": "بررسی عدد اول",
        "code": """def is_prime(n):
    if n < 2:
        return False

    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False

    return True


number = int(input("یک عدد وارد کن: "))

if is_prime(number):
    print(number, "عدد اول است.")
else:
    print(number, "عدد اول نیست.")"""
    },

    {
        "keywords": ["زوج یا فرد", "زوج فرد", "زوج و فرد"],
        "title": "تشخیص زوج یا فرد",
        "code": """number = int(input("یک عدد وارد کن: "))

if number % 2 == 0:
    print(number, "زوج است.")
else:
    print(number, "فرد است.")"""
    },

    {
        "keywords": ["مرتب سازی لیست", "مرتب کردن لیست", "لیست مرتب"],
        "title": "مرتب‌سازی یک لیست",
        "code": """numbers = [5, 2, 9, 1, 7]

numbers_ascending = sorted(numbers)
numbers_descending = sorted(numbers, reverse=True)

print("صعودی:", numbers_ascending)
print("نزولی:", numbers_descending)"""
    },

    {
        "keywords": ["جمع لیست", "جمع اعداد لیست"],
        "title": "جمع اعداد یک لیست",
        "code": """numbers = [4, 8, 15, 16, 23, 42]

total = sum(numbers)
average = total / len(numbers)

print("جمع:", total)
print("میانگین:", average)"""
    },

    {
        "keywords": ["برعکس کردن رشته", "معکوس رشته", "برعکس رشته"],
        "title": "برعکس کردن یک رشته",
        "code": """text = input("یک متن وارد کن: ")

reversed_text = text[::-1]

print("متن برعکس‌شده:", reversed_text)"""
    },

    {
        "keywords": ["ماشین حساب", "حاسبه"],
        "title": "ماشین‌حساب ساده",
        "code": """def calculate(a, operator, b):
    if operator == "+":
        return a + b
    elif operator == "-":
        return a - b
    elif operator == "*":
        return a * b
    elif operator == "/":
        if b == 0:
            return "خطا: تقسیم بر صفر ممکن نیست"
        return a / b
    else:
        return "عملگر نامعتبر است"


x = float(input("عدد اول: "))
op = input("عملگر (+ - * /): ")
y = float(input("عدد دوم: "))

print("نتیجه:", calculate(x, op, y))"""
    },

    {
        "keywords": ["حدس عدد", "بازی حدس"],
        "title": "بازی حدس عدد",
        "code": """import random

secret_number = random.randint(1, 100)
attempts = 0

print("یک عدد بین ۱ تا ۱۰۰ حدس بزن!")

while True:
    guess = int(input("حدس تو: "))
    attempts += 1

    if guess < secret_number:
        print("بزرگ‌تر بگو!")
    elif guess > secret_number:
        print("کوچیک‌تر بگو!")
    else:
        print("آفرین! درست حدس زدی، تعداد تلاش:", attempts)
        break"""
    },

    {
        "keywords": ["رمز عبور تصادفی", "پسورد تصادفی", "رمز تصادفی"],
        "title": "ساخت رمز عبور تصادفی",
        "code": """import random
import string

def generate_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(random.choice(characters) for _ in range(length))
    return password


print("رمز پیشنهادی:", generate_password())"""
    },

    {
        "keywords": ["خواندن فایل", "فایل رو بخون", "خوندن فایل"],
        "title": "خواندن یک فایل متنی",
        "code": """with open("myfile.txt", "r", encoding="utf-8") as f:
    content = f.read()

print(content)"""
    },

    {
        "keywords": ["نوشتن فایل", "فایل بنویس", "نوشتن در فایل"],
        "title": "نوشتن در یک فایل متنی",
        "code": """text = "این متنی است که ذخیره می‌شود."

with open("myfile.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("ذخیره شد.")"""
    },

    {
        "keywords": ["فایل csv", "csv بخون", "csv"],
        "title": "کار با فایل CSV",
        "code": """import csv

# خواندن
with open("data.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        print(row)

# نوشتن
with open("output.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["نام", "سن"])
    writer.writerow(["امین", 20])"""
    },

    {
        "keywords": ["فایل json", "json بخون"],
        "title": "کار با فایل JSON",
        "code": """import json

data = {"name": "امین", "age": 20}

# نوشتن
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# خواندن
with open("data.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)

print(loaded)"""
    },

    {
        "keywords": ["درخواست اینترنتی", "درخواست http", "http request"],
        "title": "ارسال درخواست HTTP",
        "code": """import requests

response = requests.get("https://api.github.com")

print("کد وضعیت:", response.status_code)
print("محتوا:", response.json())"""
    },

    {
        "keywords": ["وب اسکرپینگ", "اسکرپ کردن سایت", "اسکرپ"],
        "title": "استخراج اطلاعات از یک صفحه‌ی وب",
        "code": """import requests
from bs4 import BeautifulSoup

url = "https://example.com"

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

title = soup.find("title").text
print("عنوان صفحه:", title)"""
    },

    {
        "keywords": ["کلاس بنویس", "مثال کلاس", "class"],
        "title": "تعریف یک کلاس ساده",
        "code": """class Person:

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def introduce(self):
        print("سلام، اسم من " + self.name + " است و " + str(self.age) + " سالمه.")


p1 = Person("امین", 20)
p1.introduce()"""
    },

    {
        "keywords": ["تبدیل دما"],
        "title": "تبدیل دما (سلسیوس به فارنهایت)",
        "code": """celsius = float(input("دما به سلسیوس: "))

fahrenheit = (celsius * 9 / 5) + 32

print(celsius, "درجه سلسیوس برابر است با", fahrenheit, "درجه فارنهایت")"""
    },

    {
        "keywords": ["رابط گرافیکی", "پنجره بساز", "gui"],
        "title": "یک پنجره‌ی گرافیکی ساده (Tkinter)",
        "code": """import tkinter as tk

def say_hello():
    label.config(text="سلام! خوش اومدی 👋")


window = tk.Tk()
window.title("برنامه‌ی من")
window.geometry("300x150")

button = tk.Button(window, text="بزن اینجا", command=say_hello)
button.pack(pady=20)

label = tk.Label(window, text="")
label.pack()

window.mainloop()"""
    },

    {
        "keywords": ["دوز", "بازی دوز", "tic tac toe"],
        "title": "بازی دوز (Tic-Tac-Toe) ساده",
        "code": """board = [" "] * 9


def print_board():
    for row in range(0, 9, 3):
        print(board[row], "|", board[row + 1], "|", board[row + 2])


def check_winner(player):
    win_combos = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for combo in win_combos:
        if all(board[i] == player for i in combo):
            return True
    return False


current_player = "X"

for turn in range(9):
    print_board()
    move = int(input("نوبت " + current_player + " - خانه (۰ تا ۸): "))

    if board[move] == " ":
        board[move] = current_player

        if check_winner(current_player):
            print_board()
            print(current_player, "برنده شد! 🎉")
            break

        current_player = "O" if current_player == "X" else "X"
    else:
        print("این خانه پره، دوباره امتحان کن.")"""
    }

]


def detect_request(message):

    text = message.strip().lower()

    has_code_word = (
        "کد" in text
        or "برنامه" in text
        or "پایتون" in text
        or "اسکریپت" in text
    )

    has_verb = (
        "بساز" in text
        or "بنویس" in text
        or "بده" in text
        or "درست کن" in text
    )

    if not (has_code_word and has_verb):
        return None

    for template in TEMPLATES:

        for keyword in template["keywords"]:

            if keyword in text:

                return {
                    "title": template["title"],
                    "code": template["code"]
                }

    return None
