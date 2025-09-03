import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "8378392886:AAEbH9ZBMoQXx14Jm8E3W_xUj3bIxIaRjO0"

bot = Bot(token=TOKEN)
dp = Dispatcher()
conn = sqlite3.connect("birthdays.db")
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, birthday TEXT)")
conn.commit()

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("Отправь дату рождения в формате ГГГГ-ММ-ДД")

@dp.message()
async def set_birthday(msg: types.Message):
    try:
        date = datetime.strptime(msg.text, "%Y-%m-%d").date()
        cur.execute("REPLACE INTO users (user_id, birthday) VALUES (?, ?)", (msg.from_user.id, msg.text))
        conn.commit()
        await msg.answer("Дата рождения сохранена")
    except:
        await msg.answer("Неверный формат, попробуй ГГГГ-ММ-ДД")

async def send_countdowns():
    cur.execute("SELECT user_id, birthday FROM users")
    for user_id, bday_str in cur.fetchall():
        bday = datetime.strptime(bday_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        next_bday = bday.replace(year=today.year)
        if next_bday < today:
            next_bday = next_bday.replace(year=today.year + 1)
        delta = datetime.combine(next_bday, datetime.min.time()) - datetime.now()
        months = (next_bday.year - today.year) * 12 + next_bday.month - today.month - (1 if next_bday.day < today.day else 0)
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        text = f"{months} мес {days} дн {hours} ч {minutes} м {seconds} с до дня рождения"
        await bot.send_message(user_id, text)

async def scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_countdowns, "cron", hour=9)
    scheduler.start()

async def main():
    await scheduler()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
