from aiogram.fsm.state import State, StatesGroup


class AdminBroadcastState(StatesGroup):
    waiting_text = State()
    waiting_confirm = State()
