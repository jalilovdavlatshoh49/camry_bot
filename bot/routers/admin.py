import logging
import datetime
import random
import hashlib
from typing import List, Tuple

from aiogram import Router, types, F
from aiogram.filters import BaseFilter, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

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


# === Филтри оддӣ барои админ ===
class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == ADMIN_ID


# === Состояния для поиска ===
class SearchStates(StatesGroup):
    waiting_for_query = State()


# === Генерация кода на основе PUK ===
def generate_code_from_puk(puk: str, length: int = 6) -> str:
    hash_object = hashlib.sha256(puk.encode())
    hex_dig = hash_object.hexdigest()
    big_int = int(hex_dig, 16)
    digits = str(big_int % (10 ** length)).zfill(length)
    return digits


# === Форматирование VIN-кодов ===
def format_vin_info(vins: List[Tuple[str, str]]) -> str:
    if not vins:
        return "❌ У этого пользователя нет подтвержденных VIN-кодов."

    vin_lines = "\n".join(f"✅ VIN: <code>{vin}</code> | 📅 Дата: {date}" for vin, date in vins)
    return f"✅ Подтверждённые VIN-коды ({len(vins)}):\n\n{vin_lines}"


# === Форматирование информации о пользователе ===
def format_user_info(user: Tuple[int, str, str, str], vins: List[Tuple[str, str]]) -> str:
    user_id, first_name, last_name, phone = user
    vin_info = format_vin_info(vins)
    return (
        f"👤 <b>{first_name} {last_name}</b>\n"
        f"📞 Телефон: <code>{phone}</code>\n"
        f"🆔 ID: <code>{user_id}</code>\n\n"
        f"{vin_info}"
    )


# === Обработка "Одобрить" заявки ===
@router.callback_query(F.data.startswith("approve"))
async def handle_approve(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        if len(parts) != 4:
            raise ValueError("❌ Неверная структура данных.")

        _, user_id_str, vin, number = parts
        user_id = int(user_id_str)

        puk = f"{vin}_{number}".upper()
        code = generate_code_from_puk(puk)
        timestamp = datetime.datetime.now().isoformat()

        await update_request_status(user_id, vin, number, "approved")
        await insert_code(user_id, vin, number, code, timestamp)

        await bot.send_message(
            user_id,
            f"✅ Ваш код: <code>{code}</code>\nВведите его в приложении.",
            parse_mode="HTML"
        )
        await callback.answer("✅ Код отправлен пользователю")

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_approve: {e}")
        await callback.answer("❌ Ошибка при обработке.", show_alert=True)


# === Обработка "Отклонить" заявки ===
@router.callback_query(F.data.startswith("reject"))
async def handle_reject(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        if len(parts) != 2:
            raise ValueError("❌ Неверная структура данных.")

        _, user_id_str = parts
        user_id = int(user_id_str)

        await delete_request(user_id)
        await bot.send_message(user_id, "❌ Ваша заявка была отклонена админом.")
        await callback.answer("🚫 Заявка отклонена")

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_reject: {e}")
        await callback.answer("❌ Ошибка при отклонении.", show_alert=True)


# === Команда /search (только для админа) ===
@router.message(Command("search"), IsAdmin())
async def cmd_search(msg: Message, state: FSMContext):
    await msg.answer("🔍 Введите имя, фамилию, телефон или ID пользователя:")
    await state.set_state(SearchStates.waiting_for_query)


# === Обработка запроса поиска ===
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
            formatted = format_user_info(user, vins)
            await msg.answer(formatted, parse_mode="HTML")

    except Exception as e:
        logger.error(f"❌ Ошибка в поиске: {e}")
        await msg.answer("❌ Ошибка при поиске пользователя.")

    await state.clear()