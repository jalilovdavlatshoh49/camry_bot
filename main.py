import asyncio
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




if __name__ == "__main__":
    asyncio.run(start_bot())