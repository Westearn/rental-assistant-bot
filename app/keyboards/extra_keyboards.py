from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CopyTextButton


def copy_keyboard(txt: str, copy_txt: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f"{txt}", copy_text=CopyTextButton(text=copy_txt)))
    return builder.as_markup()

def cancel_inline_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action"))
    return builder.as_markup()

def back_inline():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_inline"))
    return builder.as_markup()