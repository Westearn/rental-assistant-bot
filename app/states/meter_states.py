from aiogram.fsm.state import State, StatesGroup


class MeterState(StatesGroup):
    hot = State()
    cold = State()
    electricity = State()