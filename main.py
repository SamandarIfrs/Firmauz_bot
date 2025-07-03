from aiogram import executor
from loader import dp
import handlers
import admin
from database import init_db
import logging

logging.basicConfig(level=logging.INFO, filename="bot.log", encoding="utf-8")

if __name__ == '__main__':
    init_db()  # Ma'lumotlar bazasini ishga tushirish
    executor.start_polling(dp, skip_updates=True)