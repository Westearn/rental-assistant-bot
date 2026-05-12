from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


def tariffs_keyboard(tariffs):
    builder = InlineKeyboardBuilder()
    
    for tariff in tariffs:
        # На кнопке пишем название и цену, в callback отправляем id
        builder.row(InlineKeyboardButton(
            text=f"{tariff.name}: {tariff.value} руб.", 
            callback_data=f"tar_{tariff.id}")
        )

    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    return builder.as_markup()