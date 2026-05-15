from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import math

from app.database.db import SessionLocal
from app.states.meter_states import MeterState
from app.states.pay_states import PayState
from app.states.comment_states import CommentState
from app.keyboards.apartments_keyboard import apartments_keyboard
from app.keyboards.actions_keyboard import actions_keyboard
from app.keyboards.extra_keyboards import copy_keyboard, cancel_inline_kb, back_inline
from app.services.apartment_service import ApartmentService
from app.services.contact_service import ContactService
from app.services.meter_readings_service import MeterReadingService
from app.services.tariff_service import TariffService
from app.services.log_service import LogService
from app.services.utils import clear_buttons

router = Router()

# ---------------------------
# ВЫБОР КВАРТИРЫ
# ---------------------------
@router.message(F.text == "🏢 Выбор квартиры")
async def process_apartment_choice(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear() # Сбрасываем ввод показаний

    async with SessionLocal() as session: # Получаем список квартир из базы
        service = ApartmentService(session)
        apartments = await service.get_apartments()

    await message.answer(
        text="Выберите объект из списка ниже:",
        reply_markup=apartments_keyboard(apartments))

# ---------------------------
# ДЕЙСТВИЯ С КВАРТИРОЙ
# ---------------------------
@router.callback_query(F.data.startswith("apt_"))
async def select_apartment(call: CallbackQuery, state: FSMContext):
    await call.answer()
    apartment_id = int(call.data.split("_")[1]) # callback в apartments_keyboard задан в формате apt_1
    
    async with SessionLocal() as session:
        service = ApartmentService(session)
        apartment = await service.get_apartment(apartment_id)

    await state.update_data(apartment_id=apartment_id)

    await call.message.edit_text(
        text=f"🏠  *{apartment.address}*",
        reply_markup=actions_keyboard(),
        parse_mode="Markdown")
    
# ---------------------------
# ГОРЯЧАЯ ВОДА
# ---------------------------
@router.callback_query(F.data == "set_meter")
async def select_apartment(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)

    data = await state.get_data()
    apartment_id = data["apartment_id"]
    async with SessionLocal() as session:
        meterReadingService = MeterReadingService(session)
        meters = await meterReadingService.get_meters(apartment_id)
    
    if meters is None:
        await call.message.answer("Вы вносите первые показания для данного объекта. Долг увеличен не будет")
        await state.update_data(old_hot=0, old_cold=0, old_el=0)
    else:
        await call.message.answer(
        f"📊 *Последние показания:*\n"
        f"┣ 🔥 ГВС: `{meters.hot_water}`\n"
        f"┣ ❄️ ХВС: `{meters.cold_water}`\n"
        f"┗ ⚡️ ЭЛТ: `{meters.electricity}`\n",
        parse_mode="Markdown")
    
        await state.update_data(old_hot=meters.hot_water,
                                old_cold=meters.cold_water,
                                old_el=meters.electricity)

    await state.set_state(MeterState.hot)
    sent_message = await call.message.answer(
        "Введите показания 🔥 горячей воды:",
        reply_markup=cancel_inline_kb())
    await state.update_data(msg_to_edit=sent_message.message_id)
    
# ---------------------------
# ХОЛОДНАЯ ВОДА
# ---------------------------
@router.message(MeterState.hot)
async def hot_water(message: Message, state: FSMContext):
    try: 
        hot = int(message.text)
    except ValueError:
        return await message.answer("Пожалуйста, введите корректное число (например, 123)")
    
    data = await state.get_data()
    old_hot = data["old_hot"]
    if hot < old_hot: return await message.answer(f"Значение должно быть больше предыдущего: {old_hot}")

    await state.update_data(hot=hot)
    await clear_buttons(message, state) # msg_to_edit
    await state.set_state(MeterState.cold)
    sent_message = await message.answer("Введите показания ❄ холодной воды:",
                                        reply_markup=cancel_inline_kb())
    await state.update_data(msg_to_edit=sent_message.message_id)

# ---------------------------
# ЭЛЕКТРИЧЕСТВО
# ---------------------------
@router.message(MeterState.cold)
async def cold_water(message: Message, state: FSMContext):
    try: 
        cold = int(message.text)
    except ValueError:
        return await message.answer("Пожалуйста, введите корректное число (например, 123)")
    
    data = await state.get_data()
    old_cold = data["old_cold"]
    if cold < old_cold: return await message.answer(f"Значение должно быть больше предыдущего: {old_cold}")
    
    await state.update_data(cold=cold)
    await clear_buttons(message, state) # msg_to_edit
    await state.set_state(MeterState.electricity)
    sent_message = await message.answer("Введите показания ⚡ электроэнергии:",
                                        reply_markup=cancel_inline_kb())
    await state.update_data(msg_to_edit=sent_message.message_id)

# ---------------------------
# РАСЧЁТ
# ---------------------------
@router.message(MeterState.electricity)
async def electricity(message: Message, state: FSMContext):
    try: 
        el = int(message.text)
    except ValueError:
        return await message.answer("Пожалуйста, введите корректное число (например, 123)")

    data = await state.get_data()
    old_el = data["old_el"]
    if el < old_el: return await message.answer(f"Значение должно быть больше предыдущего: {old_el}")

    await clear_buttons(message, state) # msg_to_edit

    hot = data["hot"]
    cold = data["cold"]
    apartment_id = data["apartment_id"]

    async with SessionLocal() as session:
        apService = ApartmentService(session)
        apartment = await apService.get_apartment(apartment_id)

        meterReadingService = MeterReadingService(session)
        last = await meterReadingService.get_meters(apartment_id)

        tariffService = TariffService(session)
        tariffs = await tariffService.get_all_tariffs()
        tariffs_prices = {t.name: t.value for t in tariffs}

        # если нет предыдущих показаний
        if not last:
            diff_hot = diff_cold = diff_el = 0
        else:
            diff_hot = hot - last.hot_water
            diff_cold = cold - last.cold_water
            diff_el = el - last.electricity

        if apartment.type == "Квартира":
            el_tariff = tariffs_prices["Электроэнергия для квартир"]
        else:
            el_tariff = tariffs_prices["Электроэнергия для гаражей"]

        bill = math.ceil(
            diff_hot * tariffs_prices["Горячая вода"] +
            diff_cold * tariffs_prices["Холодная вода"] +
            (diff_hot + diff_cold) * tariffs_prices["Водоотведение"] +
            diff_el * el_tariff)

        # обновляем долг
        apartment.debt += bill

        # сохраняем показания
        await meterReadingService.save_reading(apartment_id, hot, cold, el)

        # лог
        logService = LogService(session)
        await logService.log(
            user=message.from_user.full_name,
            apartment_id=apartment.id,
            action=f"{apartment.address}: Показания: ГВ={hot}, ХВ={cold}, ЭЛ={el} | Начислено {bill}")

        await session.commit()

    await state.clear()

    await message.answer(
        f"✅ Данные сохранены\n"
        f"Начислено: {bill}\n"
        f"Текущий долг равен: {apartment.debt}",
        reply_markup=copy_keyboard("Скопировать долг", f"{apartment.debt}"))

# ---------------------------
# ВЫВОД ИНФОРМАЦИИ О ДОЛГЕ
# ---------------------------
@router.callback_query(F.data == "get_debt")
async def get_debt(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    apartment_id = data["apartment_id"]
    async with SessionLocal() as session:
        service = ApartmentService(session)
        apartment = await service.get_apartment(apartment_id)

    await call.message.edit_text(f"🏠  *{apartment.address}*\n"
                                f"Долг: {apartment.debt} ₽",
                                reply_markup=copy_keyboard("Скопировать долг", f"{apartment.debt}"),
                                parse_mode="Markdown")

# ---------------------------
# ВНЕСТИ ОПЛАТУ
# ---------------------------
@router.callback_query(F.data == "make_pay")
async def call_pay(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    apartment_id = data["apartment_id"]
    async with SessionLocal() as session:
        service = ApartmentService(session)
        apartment = await service.get_apartment(apartment_id)

    await state.set_state(PayState.pay)
    sent_message = await call.message.edit_text(f"{apartment.address}\n"
                                f"Текущий долг: {apartment.debt} ₽\n"
                                "Укажите сумму оплаты:",
                                reply_markup=cancel_inline_kb(),
                                parse_mode="Markdown")
    
    await state.update_data(msg_to_edit=sent_message.message_id)

@router.message(PayState.pay)
async def make_pay(message: Message, state: FSMContext):
    data = await state.get_data()
    apartment_id = data["apartment_id"]
    try:
        pay = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число (например, 12500)")
        return
    
    await clear_buttons(message, state) # msg_to_edit

    async with SessionLocal() as session:
        service = ApartmentService(session)
        apartment = await service.get_apartment(apartment_id)
        apartment.debt -= pay

        logService = LogService(session)
        await logService.log(
            user=message.from_user.full_name,
            action=f"{apartment.address}: Внесена оплата в размере {pay} ₽"
                    f"Долг обновлен: {apartment.debt} ₽")

        await session.commit()
    
    await message.answer(f"{apartment.address}\n"
                        f"Оплата в размере {pay} ₽ внесена\n"
                        f"Долг обновлен: {apartment.debt} ₽",
                        reply_markup=copy_keyboard("Скопировать долг", f"{apartment.debt}"))
    await state.clear()

# ---------------------------
# ИЗМЕНИТЬ ЗАМЕТКУ
# ---------------------------
@router.callback_query(F.data == "edit_comment")
async def call_comment(call: CallbackQuery, state: FSMContext):
    await call.answer()
    
    data = await state.get_data()
    apartment_id = data["apartment_id"]
    async with SessionLocal() as session:
        service = ApartmentService(session)
        apartment = await service.get_apartment(apartment_id)

    await state.set_state(CommentState.comment)
    sent_message = await call.message.edit_text(f"Текущая заметка: {apartment.comment}\n\n"
                                                "*Введите актуальную заметку:*",
                                                reply_markup=copy_keyboard("Скопировать текущую заметку", f"{apartment.comment}",
                                                parse_mode="Markdown"))
    
    await state.update_data(msg_to_edit=sent_message.message_id)

@router.message(CommentState.comment)
async def edit_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    apartment_id = data["apartment_id"]

    comment = message.text
    
    async with SessionLocal() as session:
        service = ApartmentService(session)
        apartment = await service.get_apartment(apartment_id)
        prev_comment = apartment.comment
        apartment.comment = comment

        logService = LogService(session)
        await logService.log(
            user=message.from_user.full_name,
            action=f"{apartment.address}: Заметка изменена. "
                    f"Прошлая заметка: {prev_comment}. "
                    f"Новая заметка: {comment}")

        await session.commit()
    
    await clear_buttons(message, state) # msg_to_edit

    await message.answer("Комментарий изменен")
    await state.clear()

# ---------------------------
# ИНФОРМАЦИЯ ОБ ОБЪЕКТЕ
# ---------------------------
@router.callback_query(F.data == "get_info")
async def call_comment(call: CallbackQuery, state: FSMContext):
    await call.answer()
    
    data = await state.get_data()
    apartment_id = data["apartment_id"]
    async with SessionLocal() as session:
        service = ApartmentService(session)
        apartment = await service.get_apartment(apartment_id)

        contactService = ContactService(session)
        contacts = await contactService.get_contacts(apartment_id)

        meterReadingService = MeterReadingService(session)
        meters = await meterReadingService.get_meters(apartment_id)
    
    contact_lines = []
    for c in contacts:
        contact_lines.append(f"• *{c.name}* ({c.role}): [{c.phone}](tel:{c.phone})")

    contacts_text = "\n" + "\n".join(contact_lines) if contact_lines else " _не указаны_"

    await call.message.edit_text(
        f"🏠 *Объект:* `{apartment.address}`\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"💰 *Аренда:* `{apartment.rent}` ₽\n"
        f"📅 *Оплата:* `{apartment.due_day}-е число`\n"
        f"💸 *Долг:* `{apartment.debt}` ₽\n"
        f"📊 *Последние показания:*\n"
        f"┣ 🔥 ГВС: `{meters.hot_water if meters else "не указано"}`\n"
        f"┣ ❄️ ХВС: `{meters.cold_water if meters else "не указано"}`\n"
        f"┗ ⚡️ ЭЛТ: `{meters.electricity if meters else "не указано"}`\n"
        f"📝 *Заметка:* _{apartment.comment or 'пусто'}_\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"👥 *Контакты:*{contacts_text}",
        reply_markup=back_inline(),
        parse_mode="Markdown")

# ---------------------------
# ОТМЕНА
# ---------------------------   
@router.callback_query(F.data == "cancel_action")
async def cancel_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    
    data = await state.get_data()
    apartment_id = data["apartment_id"]

    await state.clear()
    # Редактируем сообщение, чтобы убрать кнопку и показать статус
    await call.message.edit_text("🛑 Ввод отменен")
    
    async with SessionLocal() as session:
        service = ApartmentService(session)
        apartment = await service.get_apartment(apartment_id)

    await state.update_data(apartment_id=apartment_id)

    await call.message.answer(
        text=f"🏠  *{apartment.address}*",
        reply_markup=actions_keyboard(),
        parse_mode="Markdown")

# ---------------------------
# НАЗАД
# ---------------------------   
@router.callback_query(F.data == "back_inline")
async def cancel_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()

    data = await state.get_data()
    apartment_id = data["apartment_id"]

    async with SessionLocal() as session:
        service = ApartmentService(session)
        apartment = await service.get_apartment(apartment_id)

    await call.message.edit_reply_markup(reply_markup=None)

    await call.message.answer(
        text=f"🏠  *{apartment.address}*",
        reply_markup=actions_keyboard(),
        parse_mode="Markdown")