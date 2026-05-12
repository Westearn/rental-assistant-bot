from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def apartments_keyboard(apartments):
    buttons = []

    for apt in apartments:
        buttons.append([
            InlineKeyboardButton(
                text=apt.address,
                callback_data=f"apt_{apt.id}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)