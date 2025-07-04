import asyncio
import threading
import uvicorn

from server.main import app as fastapi_app
from bot.dispatcher import dp, bot
from db.db import init_db
from bot.routers import user, admin

# Запуск Telegram-бота
async def start_bot():
    dp.include_router(user.router)
    dp.include_router(admin.router)
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    print("bot is running")
    await dp.start_polling(bot)


# Запуск FastAPI-сервера в отдельном потоке
def start_api():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    threading.Thread(target=start_api).start()
    asyncio.run(start_bot())