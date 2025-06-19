# bot/bot.py
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
