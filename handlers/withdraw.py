import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db.services.users_service import UserService
from db.services.withdraw_requests_service import WithdrawRequestService
from keyboards.profile_menu import profile_keyboard
from keyboards.withdraw_menu import (
    get_change_bank_keyboard,
    get_cryptobot_keyboard,
    get_withdraw_methods_keyboard,
)
from states.withdraw import WithdrawState
from texts.withdraw_texts import (
    WITHDRAW_MINIMUMS,
    get_cryptobot_text,
    get_enter_amount_text,
    get_phone_balance_text,
    get_sber_text,
    get_tbank_text,
    get_withdraw_main_text,
    get_yoomoney_text,
)

router = Router()
user_service = UserService()
withdraw_request_service = WithdrawRequestService()

METHOD_NAMES = {
    "yoomoney": "YooMoney",
    "tbank": "Т-БАНК",
    "sber": "СБЕР",
    "cryptobot": "CryptoBot",
    "phone_balance": "На баланс телефона",
}


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


def is_valid_russian_phone(value: str) -> bool:
    digits = normalize_phone(value)
    return len(digits) == 11 and digits.startswith("7")


def is_valid_yoomoney_requisites(value: str) -> bool:
    clean = value.strip()
    if is_valid_russian_phone(clean):
        return True
    digits = re.sub(r"\D", "", clean)
    return 11 <= len(digits) <= 20


async def get_user_balance(user_id: int) -> int:
    user = await user_service.get_by_id(user_id)
    if user is None:
        return 0
    return user.balance


@router.callback_query(F.data == "give_money_pls")
async def open_withdraw_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        get_withdraw_main_text(),
        reply_markup=get_withdraw_methods_keyboard(),
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == "withdraw_change_bank")
async def change_bank(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        get_withdraw_main_text(),
        reply_markup=get_withdraw_methods_keyboard(),
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == "withdraw_yoomoney")
async def withdraw_yoomoney(callback: CallbackQuery, state: FSMContext):
    balance = await get_user_balance(callback.from_user.id)
    await state.set_state(WithdrawState.waiting_requisites)
    await state.update_data(method="yoomoney", method_name=METHOD_NAMES["yoomoney"], balance=balance)
    await callback.message.edit_text(get_yoomoney_text(balance), reply_markup=get_change_bank_keyboard(), disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "withdraw_tbank")
async def withdraw_tbank(callback: CallbackQuery, state: FSMContext):
    balance = await get_user_balance(callback.from_user.id)
    await state.set_state(WithdrawState.waiting_requisites)
    await state.update_data(method="tbank", method_name=METHOD_NAMES["tbank"], balance=balance)
    await callback.message.edit_text(get_tbank_text(balance), reply_markup=get_change_bank_keyboard(), disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "withdraw_sber")
async def withdraw_sber(callback: CallbackQuery, state: FSMContext):
    balance = await get_user_balance(callback.from_user.id)
    await state.set_state(WithdrawState.waiting_requisites)
    await state.update_data(method="sber", method_name=METHOD_NAMES["sber"], balance=balance)
    await callback.message.edit_text(get_sber_text(balance), reply_markup=get_change_bank_keyboard(), disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "withdraw_cryptobot")
async def withdraw_cryptobot(callback: CallbackQuery, state: FSMContext):
    balance = await get_user_balance(callback.from_user.id)
    await state.clear()
    await state.update_data(method="cryptobot", method_name=METHOD_NAMES["cryptobot"], balance=balance)
    await callback.message.edit_text(get_cryptobot_text(balance), reply_markup=get_cryptobot_keyboard(), disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "withdraw_phone_balance")
async def withdraw_phone_balance(callback: CallbackQuery, state: FSMContext):
    balance = await get_user_balance(callback.from_user.id)
    await state.set_state(WithdrawState.waiting_requisites)
    await state.update_data(method="phone_balance", method_name=METHOD_NAMES["phone_balance"], balance=balance)
    await callback.message.edit_text(get_phone_balance_text(balance), reply_markup=get_change_bank_keyboard(), disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "withdraw_crypto_usdt_trc20")
async def withdraw_crypto_usdt(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    balance = data.get("balance", 0)
    await state.set_state(WithdrawState.waiting_amount)
    await state.update_data(currency="USDT TRC20")
    text = get_enter_amount_text(
        method_name="CryptoBot / USDT TRC20",
        balance=balance,
        minimum=WITHDRAW_MINIMUMS["cryptobot"],
        extra="Вы выбрали вывод через CryptoBot в валюте USDT TRC20.",
    )
    await callback.message.edit_text(text, reply_markup=get_change_bank_keyboard(), disable_web_page_preview=True)
    await callback.answer()


@router.message(WithdrawState.waiting_requisites)
async def process_requisites(message: Message, state: FSMContext):
    data = await state.get_data()
    method = data.get("method")
    balance = data.get("balance", 0)
    requisites = (message.text or "").strip()

    if method == "yoomoney":
        if not is_valid_yoomoney_requisites(requisites):
            await message.answer(
                "Неверный формат.\nДля YooMoney отправьте номер телефона РФ или номер счета."
            )
            return
    elif method in ("tbank", "sber", "phone_balance"):
        if not is_valid_russian_phone(requisites):
            await message.answer(
                "Неверный формат номера.\nОтправьте номер телефона РФ в формате 79XXXXXXXXX или 89XXXXXXXXX."
            )
            return
        requisites = normalize_phone(requisites)

    await state.update_data(requisites=requisites)
    await state.set_state(WithdrawState.waiting_amount)
    minimum = WITHDRAW_MINIMUMS[method]
    method_name = METHOD_NAMES[method]
    await message.answer(
        get_enter_amount_text(method_name=method_name, balance=balance, minimum=minimum),
        reply_markup=get_change_bank_keyboard(),
    )


@router.message(WithdrawState.waiting_amount)
async def process_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    method = data.get("method")
    method_name = data.get("method_name")
    balance = data.get("balance", 0)
    requisites = data.get("requisites")
    currency = data.get("currency")

    raw_amount = (message.text or "").strip().replace(" ", "").replace(",", ".")
    try:
        amount = int(float(raw_amount))
    except ValueError:
        await message.answer("Введите сумму числом.")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть больше 0.")
        return

    minimum = WITHDRAW_MINIMUMS[method]
    if amount < minimum:
        await message.answer(f"Минимальная сумма для {method_name} — {minimum} руб.")
        return

    if amount > balance:
        await message.answer(f"Недостаточно средств.\nТекущий баланс: {balance} руб.")
        return

    request = await withdraw_request_service.create(
        user_id=message.from_user.id,
        username=message.from_user.username,
        method=method_name,
        amount=amount,
        requisites=requisites,
        currency=currency,
    )

    text = (
        "Заявка на вывод создана.\n\n"
        f"ID заявки: {request.id}\n"
        f"Платежная система: {method_name}\n"
        f"Сумма: {amount} руб.\n"
    )
    if requisites:
        text += f"Реквизиты: {requisites}\n"
    if currency:
        text += f"Криптовалюта: {currency}\n"
    text += "\nЗаявка передана на обработку."

    admin_users = await user_service.get_admin_users()
    admin_notify_text = (
        "Новая заявка на вывод\n\n"
        f"ID заявки: {request.id}\n"
        + (f"Пользователь: @{message.from_user.username} | ID: {message.from_user.id}\n" if message.from_user.username else f"Пользователь: ID {message.from_user.id}\n")
        + f"Платежная система: {method_name}\n"
        + f"Сумма: {amount} руб.\n"
        + (f"Реквизиты: {requisites}\n" if requisites else "")
        + (f"Криптовалюта: {currency}\n" if currency else "")
    )
    for admin in admin_users:
        try:
            await message.bot.send_message(admin.id, admin_notify_text)
        except Exception:
            continue

    await state.clear()
    await message.answer(text, reply_markup=profile_keyboard)
