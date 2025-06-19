from aiogram import Router, types, F
from aiogram.filters import BaseFilter, Command
from aiogram.types import Message
import datetime
import random

from bot.dispatcher import bot
from config import ADMIN_ID
from bot.services.logic import (
    update_request_status,
    insert_code,
    delete_request,
    search_user,
    get_approved_vins
)

router = Router()


# Фильтр для проверки, является ли пользователь админом
class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == ADMIN_ID


# Обработка кнопки "Одобрить"
@router.callback_query(F.data.startswith("approve"))
async def approve_code(callback: types.CallbackQuery):
    _, user_id, vin, number = callback.data.split(":")
    user_id = int(user_id)
    code = ''.join(random.choices('0123456789', k=6))
    now = datetime.datetime.now().isoformat()

    await update_request_status(user_id, vin, number, "approved")
    await insert_code(user_id, vin, number, code, now)

    await bot.send_message(
        user_id,
        f"✅ Ваш код: <code>{code}</code>\nПожалуйста, введите его в приложении.",
        parse_mode="HTML"
    )
    await callback.answer("Код отправлен пользователю")


# Обработка кнопки "Отклонить"
@router.callback_query(F.data.startswith("reject"))
async def reject_code(callback: types.CallbackQuery):
    _, user_id = callback.data.split(":")
    user_id = int(user_id)

    await delete_request(user_id)
    await bot.send_message(user_id, "❌ Ваша заявка была отклонена админом.")
    await callback.answer("Заявка отклонена")


# Команда /поиск только для админа
@router.message(Command("поиск"), IsAdmin())
async def cmd_search(msg: types.Message):
    await msg.answer("🔍 Введите имя, фамилию, номер телефона или ID пользователя для поиска:")


# Обработка текста после команды /поиск
@router.message()
async def handle_search_query(msg: types.Message):
    query = msg.text.strip()
    users = await search_user(query)

    if not users:
        await msg.answer("❌ Пользователь не найден.")
        return

    for user in users:
        user_id, first_name, last_name, phone = user
        vins = await get_approved_vins(user_id)

        if not vins:
            vin_info = "У этого пользователя нет подтвержденных VIN-кодов."
        else:
            vin_lines = "\n".join([
                f"✅ VIN: <code>{vin}</code> | 📅 Дата: {date}" for vin, date in vins
            ])
            vin_info = (
                f"Этот пользователь имеет {len(vins)} VIN-кодов со статусом ✅ 'approved':\n\n{vin_lines}"
            )

        await msg.answer(
            f"👤 <b>{first_name} {last_name}</b>\n"
            f"📞 Телефон: <code>{phone}</code>\n"
            f"🆔 ID: <code>{user_id}</code>\n\n"
            f"{vin_info}",
            parse_mode="HTML"
        )
