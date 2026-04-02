from aiogram.fsm.state import State, StatesGroup


class TaskFlowState(StatesGroup):
    waiting_city = State()
    waiting_platform_login = State()
    waiting_screenshot = State()
