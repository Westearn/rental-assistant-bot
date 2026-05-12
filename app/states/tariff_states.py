from aiogram.fsm.state import State, StatesGroup


class TariffEditState(StatesGroup):
    waiting_for_value = State()