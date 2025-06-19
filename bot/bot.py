from bot.dispatcher import dp
from bot.routers import user, admin

dp.include_router(user.router)
dp.include_router(admin.router)
