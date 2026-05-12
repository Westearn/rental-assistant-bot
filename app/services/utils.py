from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, timezone


async def clear_buttons(message: Message, state: FSMContext):
    data = await state.get_data()
    old_msg_id = data.get("msg_to_edit") # msg_to_edit - имя ключа необходимого сообщения
    if old_msg_id:
        try:
            await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=old_msg_id, reply_markup=None) # Удаляем inline кнопки указанного сообщения
        except Exception: 
            pass # Игнорируем, если сообщение уже удалено или изменено

def now_time():
    tomsk_tz = timezone(timedelta(hours=7))
    return datetime.now(tomsk_tz)