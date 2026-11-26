import asyncio
import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = os.getenv("BOT_TOKEN", "9155152712:AAFbM3LACN4LHrsEdUeOEGar7Amc44wQ6Qg")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://nakakano2006-lang.github.io/quit-vape-bot/")
DATA_FILE = "progress.json"
MILESTONES = [1, 3, 5, 7, 10, 14, 21, 30]

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Открыть приложение", web_app=WebAppInfo(url=WEBAPP_URL))]
        ],
        resize_keyboard=True,
    )


async def check_milestones():
    data = load_data()
    now = datetime.now()
    changed = False

    for user_id, info in data.items():
        start_time = datetime.fromisoformat(info["start_time"])
        passed_days = (now - start_time).days
        sent_days = info.get("sent_days", [])

        for day in MILESTONES:
            if passed_days >= day and day not in sent_days:
                try:
                    await bot.send_message(
                        chat_id=int(user_id),
                        text=f"Ты держишься уже {day} дн. Отличный рубеж — продолжай в том же духе.",
                    )
                    sent_days.append(day)
                    changed = True
                except Exception as e:
                    print(f"Ошибка отправки {user_id}: {e}")

    if changed:
        save_data(data)


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    data = load_data()
    user_id = str(message.from_user.id)

    if user_id not in data:
        data[user_id] = {
            "start_time": datetime.now().isoformat(),
            "sent_days": [],
        }
        save_data(data)

    await message.answer(
        "Открой приложение по кнопке ниже: там счётчик времени, кнопка 15 минут со случайной мотивацией и сброс прогресса.",
        reply_markup=get_keyboard(),
    )


@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        payload = json.loads(message.web_app_data.data)
    except Exception:
        return

    if payload.get("action") == "reset":
        data = load_data()
        user_id = str(message.from_user.id)
        start_iso = payload.get("start_time") or datetime.now().isoformat()
        data[user_id] = {
            "start_time": start_iso,
            "sent_days": [],
        }
        save_data(data)
        await message.answer("Прогресс сброшен, отсчёт начат заново.", reply_markup=get_keyboard())


async def main():
    scheduler.add_job(check_milestones, "interval", minutes=10)
    scheduler.start()
    print("Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())