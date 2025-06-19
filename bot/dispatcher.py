import os
from aiogram import Bot, Dispatcher
from bot.routers import user, admin
from dotenv import load_dotenv  

load_dotenv()

# Получение токена бота из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле!")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключение маршрутизаторов
dp.include_router(user.router)
dp.include_router(admin.router
