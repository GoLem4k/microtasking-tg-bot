from aiogram.fsm.state import State, StatesGroup


class AdminBroadcastState(StatesGroup):
    waiting_text = State()
    waiting_confirm = State()


class AdminTaskCreateState(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_note = State()
    waiting_reward = State()
    waiting_max_completions = State()
    waiting_city = State()
    waiting_confirm = State()


class AdminTaskEditState(StatesGroup):
    waiting_value = State()


class AdminSupportReplyState(StatesGroup):
    waiting_text = State()
