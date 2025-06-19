import asyncio
import threading
import uvicorn

from server.main import app as fastapi_app
from bot.dispatcher import dp, bot
from db.db import init_db


# Запуск Telegram-бота
async def start_bot():
    await init_db()
    await dp.start_polling(bot)


# Запуск FastAPI-сервера в отдельном потоке
def start_api():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    threading.Thread(target=start_api).start()
    asyncio.run(start_bot())