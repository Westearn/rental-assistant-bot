from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def settings_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                    text="Посмотреть тарифы", 
                    callback_data="info_tariffs")],
            [InlineKeyboardButton(
                    text="Изменить тарифы", 
                    callback_data="settings_tariffs")]
    ])