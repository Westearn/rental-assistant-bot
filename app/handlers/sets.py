from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.database.db import SessionLocal
from app.states.tariff_states import TariffEditState
from app.keyboards.settings_keyboard import settings_keyboard
from app.keyboards.tariffs_keyboard import tariffs_keyboard
from app.services.tariff_service import TariffService
from app.services.log_service import LogService

router = Router()


@router.message(F.text == "⚙️ Настройки")
async def process_apartment_choice(message: Message, state: FSMContext):
    # Очищаем активные состояния, если такие имеются
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()

    await message.answer(
        text="Выберите необходимые настройки",
        reply_markup=settings_keyboard())

# ---------------------------
# Информация о тарифах
# ---------------------------
@router.callback_query(F.data == "info_tariffs")
async def select_apartment(call: CallbackQuery):
    # Отвечаем на колбэк, убираем анимацию загрузки кнопки
    await call.answer() 
    
    # Получаем список тарифов из базы
    async with SessionLocal() as session:
        tariffService = TariffService(session)
        tariffs = await tariffService.get_all_tariffs()

    # Подготавливаем текстовое сообщение
    text = "📋 **Текущие тарифы:**\n\n"
    for tariff in tariffs:
        text += f"🔹 **{tariff.name}**: {tariff.value} ₽\n"
    
    # Редактируем сообщение, выводя список
    await call.message.edit_text(
        text=text,
        parse_mode="Markdown" # Чтобы работал жирный шрифт (**)
    )

# ---------------------------
# Информация о тарифах - Редактирование
# ---------------------------
@router.callback_query(F.data == "settings_tariffs")
async def select_apartment(call: CallbackQuery):
    await call.answer() 

    async with SessionLocal() as session:
        tariffService = TariffService(session)
        tariffs = await tariffService.get_all_tariffs()

    # Редактируем старое сообщение, выводим новую клавиатуру
    await call.message.edit_text(
        "Вы перешли в меню изменения тарифов. Выберите тариф:",
        reply_markup=tariffs_keyboard(tariffs) # Ваша новая клавиатура
    )    

# ---------------------------
# Кнопка "Назад" в меню настроек тарифов
# ---------------------------
@router.callback_query(F.data == "back")
async def back_to_settings(call: CallbackQuery):
    await call.answer()

    await call.message.edit_text(
        text="Выберите необходимые настройки",
        reply_markup=settings_keyboard())

# ---------------------------
# Редактирование тарифов - обработка выбора тарифа для редактирования
# ---------------------------
@router.callback_query(F.data.startswith("tar_"))
async def start_edit_tariff(call: CallbackQuery, state: FSMContext):
    await call.answer()
    
    # Извлекаем ID из callback_data (tar_1 -> 1)
    tariff_id = int(call.data.replace("tar_", ""))
    
    async with SessionLocal() as session:
        tariffService = TariffService(session)
        tariff = await tariffService.get_tariff(tariff_id)
    
    # Сохраняем tariff в хранилище FSM, чтобы использовать на следующем шаге
    await state.update_data(
            edit_tariff_id=tariff.id,
            edit_tariff_name=tariff.name,
            edit_tariff_old_value=tariff.value)
    
    await call.message.edit_text(f"Введите новое значение для тарифа {tariff.name} ({tariff.value} ₽):")
    await state.set_state(TariffEditState.waiting_for_value)

# ---------------------------
# Редактирование тарифов - обработка ввода нового значения тарифа
# ---------------------------
@router.message(TariffEditState.waiting_for_value)
async def process_new_tariff_value(message: Message, state: FSMContext):
    # Проверяем, что введено число
    new_value = message.text.strip().replace(",", ".") # Заменяем запятую на точку для float
    try:
        new_value = float(new_value)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число (например, 5.45)")
        return

    if new_value <= 0:
        await message.answer("Значение тарифа должно быть положительным числом.")
        return

    # Достаем данные тарифа, которые мы сохранили ранее
    user_data = await state.get_data()
    t_id = user_data.get("edit_tariff_id")
    t_name = user_data.get("edit_tariff_name")
    t_old_val = user_data.get("edit_tariff_old_value")

    # Обновляем значение в БД
    async with SessionLocal() as session:
        tariff_service = TariffService(session)
        await tariff_service.update_tariff_value(t_id, new_value)

        # Сохраняем информацию о действии в истории
        logService = LogService(session)
        await logService.log(
            user=message.from_user.full_name,
            action=f"Тариф \"{t_name}\" успешно обновлен до {new_value} ₽. Старое значение {t_old_val} ₽")

        await session.commit()

    # Чистим состояние и отправляем ответ
    await state.clear()
    await message.answer(f"✅ Тариф успешно обновлен до {new_value}!")