from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_withdraw_methods_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="YooMoney", callback_data="withdraw_yoomoney")],
            [InlineKeyboardButton(text="Т-Банк", callback_data="withdraw_tbank")],
            [InlineKeyboardButton(text="Сбер", callback_data="withdraw_sber")],
            [InlineKeyboardButton(text="CryptoBot", callback_data="withdraw_cryptobot")],
            [InlineKeyboardButton(text="На баланс телефона", callback_data="withdraw_phone_balance")],
            [InlineKeyboardButton(text="Назад в МЕНЮ", callback_data="main_menu")],
        ]
    )


def get_change_bank_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить банк", callback_data="withdraw_change_bank")],
            [InlineKeyboardButton(text="Назад в МЕНЮ", callback_data="main_menu")],
        ]
    )


def get_cryptobot_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="USDT TRC20", callback_data="withdraw_crypto_usdt_trc20")],
            [InlineKeyboardButton(text="Изменить банк", callback_data="withdraw_change_bank")],
            [InlineKeyboardButton(text="Назад в МЕНЮ", callback_data="main_menu")],
        ]
    )