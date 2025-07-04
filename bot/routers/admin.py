import logging
from typing import List, Tuple

from aiogram import Router, types, F
from aiogram.filters import BaseFilter, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
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

logger = logging.getLogger(__name__)

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == ADMIN_ID

class SearchStates(StatesGroup):
    waiting_for_query = State()


def generate_code(length: int = 6) -> str:
    return ''.join(random.choices('0123456789', k=length))


def format_vin_info(vins: List[Tuple[str, str]]) -> str:
    if not vins:
        return "У этого пользователя нет подтвержденных VIN-кодов."
    vin_lines = "\n".join(f"✅ VIN: <code>{vin}</code> | 📅 Дата: {date}" for vin, date in vins)
    return f"Этот пользователь имеет {len(vins)} VIN-кодов со статусом ✅ 'approved':\n\n{vin_lines}"


def format_user_info(user: Tuple[int, str, str, str], vins: List[Tuple[str, str]]) -> str:
    user_id, first_name, last_name, phone = user
    vin_info = format_vin_info(vins)
    return (
        f"👤 <b>{first_name} {last_name}</b>\n"
        f"📞 Телефон: <code>{phone}</code>\n"
        f"🆔 ID: <code>{user_id}</code>\n\n"
        f"{vin_info}"
    )


@router.callback_query(F.data.startswith("approve"))
async def handle_approve(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        if len(parts) != 4:
            raise ValueError("Некорректное количество частей в callback data")

        _, user_id_str, vin, number = parts
        user_id = int(user_id_str)

        code = generate_code()
        timestamp = datetime.datetime.now().isoformat()

        await update_request_status(user_id, vin, number, "approved")
        await insert_code(user_id, vin, number, code, timestamp)

        await bot.send_message(
            user_id,
            f"✅ Ваш код: <code>{code}</code>\nПожалуйста, введите его в приложении.",
            parse_mode="HTML"
        )
        await callback.answer("Код отправлен пользователю ✅")

    except Exception as e:
        logger.error(f"Ошибка в handle_approve: {e}")
        await callback.answer("❌ Ошибка при обработке заявки.", show_alert=True)


@router.callback_query(F.data.startswith("reject"))
async def handle_reject(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        if len(parts) != 2:
            raise ValueError("Некорректное количество частей в callback data")

        _, user_id_str = parts
        user_id = int(user_id_str)

        await delete_request(user_id)
        await bot.send_message(user_id, "❌ Ваша заявка была отклонена админом.")
        await callback.answer("Заявка отклонена 🚫")

    except Exception as e:
        logger.error(f"Ошибка в handle_reject: {e}")
        await callback.answer("❌ Ошибка при обработке заявки.", show_alert=True)


@router.message(Command("search"), IsAdmin())
async def cmd_search(msg: Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_query)
    await msg.answer("🔍 Введите имя, фамилию, номер телефона или ID пользователя для поиска:")
    


@router.message(SearchStates.waiting_for_query)
async def handle_search_query(msg: Message, state: FSMContext):
    query = msg.text.strip()
    try:
        users = await search_user(query)
        if not users:
            await msg.answer("❌ Пользователь не найден.")
            await state.clear()
            return

        for user in users:
            user_id = user[0]
            vins = await get_approved_vins(user_id)
            formatted_message = format_user_info(user, vins)
            await msg.answer(formatted_message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка в handle_search_query: {e}")
        await msg.answer("❌ Произошла ошибка при поиске пользователя.")

    await state.clear()