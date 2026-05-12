from aiogram.fsm.state import State, StatesGroup


class CommentState(StatesGroup):
    comment = State()