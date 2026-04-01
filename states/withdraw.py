from aiogram.fsm.state import State, StatesGroup


class WithdrawState(StatesGroup):
    waiting_requisites = State()
    waiting_amount = State()