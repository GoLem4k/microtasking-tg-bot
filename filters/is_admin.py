
# Список Telegram ID админов
ADMIN_IDS = [
    1061011426,    # твой ID
    111    # другой админ
]

def is_admin(user_id: int) -> bool:
 
    result = user_id in ADMIN_IDS
    print(f"[DEBUG] Проверка админа для user_id={user_id}: {result}")
    return result