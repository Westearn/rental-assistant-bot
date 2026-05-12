from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from app.keyboards.main_menu import main_menu

router = Router()


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🏠 Добро пожаловать в систему управления арендой\n"
        "Выберите действие из главного меню",
        reply_markup=main_menu()
    )