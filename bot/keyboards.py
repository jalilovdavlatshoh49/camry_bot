from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_register_kb() -> ReplyKeyboardMarkup:
    """
    Клавиатура для регистрации с кнопкой отправки контакта
    """
    keyboard = [
        [KeyboardButton(text="📱 Отправить контакт", request_contact=True)]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_main_kb() -> ReplyKeyboardMarkup:
    """
    Основная клавиатура с кнопкой для запроса нового ПУК-кода
    """
    keyboard = [
        [KeyboardButton(text="ПУК новый")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )