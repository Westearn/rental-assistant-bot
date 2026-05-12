from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def actions_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                    text="Внести показания счетчиков", 
                    callback_data="set_meter")],
            [InlineKeyboardButton(
                    text="Долг", 
                    callback_data="get_debt")],
            [InlineKeyboardButton(
                    text="Внести оплату", 
                    callback_data="make_pay")],
            [InlineKeyboardButton(
                    text="Изменить комментарий", 
                    callback_data="edit_comment")],
            [InlineKeyboardButton(
                    text="Информация об объекте", 
                    callback_data="get_info")]
    ])