import asyncio
from bot.dispatcher import dp, bot
from bot.routers import user, admin
from db import connect_db, disconnect_db, init_db

# Запуск Telegram-бота
async def start_bot():
    dp.include_router(user.router)
    dp.include_router(admin.router)
    await connect_db()
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    print("bot is running")
    await dp.start_polling(bot)
    await disconnect_db()




if __name__ == "__main__":
    asyncio.run(start_bot())