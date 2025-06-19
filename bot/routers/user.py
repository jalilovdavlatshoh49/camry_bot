from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards import get_main_kb, get_register_kb
from bot.services.logic import (
    register_user,
    add_user,
    is_registered,
    insert_request
)

from config import ADMIN_ID
from bot.dispatcher import bot

import datetime

router = Router()


# Команда /start — начало работы с ботом
@router.message(CommandStart())
async def start_cmd(msg: types.Message):
    if await is_registered(msg.from_user.id):
        await msg.answer(
            "✅ Вы уже зарегистрированы!",
            reply_markup=get_main_kb()
        )
    else:
        await msg.answer(
            "👋 Добро пожаловать!\n\n"
            "Чтобы использовать бота, необходимо пройти простую регистрацию."
        )
        await msg.answer(
            "📲 Пожалуйста, нажмите на кнопку ниже, чтобы отправить свой номер телефона.",
            reply_markup=get_register_kb()
        )


# Обработка контакта — регистрация пользователя
@router.message(F.contact)
async def register_user_handler(msg: types.Message):
    contact = msg.contact

    # Проверка, что контакт принадлежит самому пользователю
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


# Обработка кнопки "ПУК новый"
@router.message(F.text == "ПУК новый")
async def new_puk(msg: types.Message):
    await msg.answer("Введите ПУК (формат: VIN_номер)")


# Обработка сообщений вида VIN_NUMBER (например, ABC1234_5678)
@router.message(F.text.regexp(r"^[A-Z0-9]+_[0-9]+$"))
async def handle_puk_request(msg: types.Message):
    vin, number = msg.text.split("_")
    now = datetime.datetime.now().isoformat()

    await insert_request(msg.from_user.id, vin, number, now)

    await msg.answer("⏳ Пожалуйста, подождите, пока админ подтвердит вашу заявку.")

    text = (
        f"🔔 Новый запрос на код!\n"
        f"👤 Пользователь: {msg.from_user.full_name}\n"
        f"🆔 ID: {msg.from_user.id}\n"
        f"🚘 VIN: {vin}\n"
        f"🔢 Номер: {number}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve:{msg.from_user.id}:{vin}:{number}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{msg.from_user.id}")
        ]
    ])

    await bot.send_message(ADMIN_ID, text, reply_markup=kb)


# Общий обработчик для прочих сообщений — обработка ПУК-кода
@router.message()
async def process_input(msg: types.Message):
    if not await is_registered(msg.from_user.id):
        return await msg.answer("❗️Сначала зарегистрируйтесь.")
    
    await handle_puk_input(msg)
