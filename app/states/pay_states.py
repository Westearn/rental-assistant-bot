from aiogram.fsm.state import State, StatesGroup


class PayState(StatesGroup):
    pay = State()