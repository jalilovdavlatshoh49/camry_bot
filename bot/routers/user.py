import re
import datetime
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_main_kb, get_register_kb
from bot.services.logic import (
    add_user,
    is_registered,
    insert_request
)

from config import ADMIN_ID
from bot.dispatcher import bot

router = Router()

# === Состояния FSM ===
class PUKStates(StatesGroup):
    waiting_for_vin = State()


# === Команда /start ===
@router.message(CommandStart())
async def start_cmd(msg: types.Message):
    user_id = msg.from_user.id

    if await is_registered(user_id):
        await msg.answer("✅ Вы уже зарегистрированы!", reply_markup=get_main_kb())
    else:
        await msg.answer(
            "👋 Добро пожаловать!\n\n"
            "Чтобы использовать бота, необходимо пройти простую регистрацию."
        )
        await msg.answer(
            "📲 Пожалуйста, нажмите на кнопку ниже, чтобы отправить свой номер телефона.",
            reply_markup=get_register_kb()
        )


# === Обработка контакта и регистрация пользователя ===
@router.message(F.contact)
async def register_user_handler(msg: types.Message):
    contact = msg.contact

    if contact.user_id != msg.from_user.id:
        await msg.answer(
            "❗️Пожалуйста, отправьте *свой собственный* контакт с помощью кнопки.",
            parse_mode="Markdown"
        )
        return

    user_id = contact.user_id
    first_name = msg.from_user.first_name or ""
    last_name = msg.from_user.last_name or ""
    phone = contact.phone_number

    await add_user(user_id, first_name, last_name, phone)

    await msg.answer(
        f"🎉 Регистрация прошла успешно!\n\n"
        f"👤 Имя: {first_name} {last_name}\n"
        f"📞 Телефон: {phone}",
        reply_markup=get_main_kb()
    )


# === Команда "ПУК новый" ===
@router.message(F.text.casefold() == "пук новый")
async def new_puk(msg: types.Message, state: FSMContext):
    if not await is_registered(msg.from_user.id):
        await msg.answer("❗️Сначала зарегистрируйтесь.")
        return

    await state.set_state(PUKStates.waiting_for_vin)
    await msg.answer("✍️ Введите ПУК (в формате: VIN_номер)")


# === Обработка ПУК запроса (VIN_номер) ===
@router.message(PUKStates.waiting_for_vin)
async def handle_puk_request(msg: types.Message, state: FSMContext):
    text = msg.text.strip()

    if not re.fullmatch(r"[A-Z0-9]+_[0-9]+", text, flags=re.IGNORECASE):
        await msg.answer("❗️Неверный формат. Пожалуйста, введите ПУК в формате VIN_номер, например ABC1234_5678")
        return

    vin, number = text.split("_")
    vin = vin.upper()
    now = datetime.datetime.now().isoformat()

    await insert_request(msg.from_user.id, vin, number, now)
    await state.clear()

    await msg.answer("⏳ Пожалуйста, подождите, пока админ подтвердит вашу заявку.")

    # Уведомление админу
    text_admin = (
        f"🔔 Новый запрос на код!\n"
        f"👤 Пользователь: {msg.from_user.full_name}\n"
        f"🆔 ID: {msg.from_user.id}\n"
        f"🚘 VIN: {vin}\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve:{msg.from_user.id}:{vin}:{number}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{msg.from_user.id}")
        ]
    ])

    await bot.send_message(ADMIN_ID, text_admin, reply_markup=kb)


# === Обработка остальных сообщений ===
@router.message(lambda msg: msg.text and not msg.text.startswith("/"))
async def process_input(msg: types.Message, state: FSMContext):
    if not await is_registered(msg.from_user.id):
        await msg.answer("❗️Сначала зарегистрируйтесь.")
        return

    current_state = await state.get_state()
    if current_state == PUKStates.waiting_for_vin.state:
        await msg.answer("❗️Пожалуйста, введите ПУК в формате VIN_номер, например ABC1234_5678")
        return

    await msg.answer("ℹ️ Пожалуйста, нажмите кнопку 'ПУК новый', чтобы начать процесс отправки ПУК-кода.")