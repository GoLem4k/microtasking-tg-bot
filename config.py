import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

FAQ_URL = os.getenv("FAQ_URL", "https://t.me/")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/")
REVIEWS_URL = os.getenv("REVIEWS_URL", "https://t.me/")
CHAT_URL = os.getenv("CHAT_URL", "https://t.me/")

NEWS_CHANNEL_URL = os.getenv("NEWS_CHANNEL_URL", CHANNEL_URL)
WORKERS_CHAT_URL = os.getenv("WORKERS_CHAT_URL", CHAT_URL)
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/")



def _get_int_env(name: str) -> int | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


ADMIN_ALERTS_CHAT_ID = _get_int_env("ADMIN_ALERTS_CHAT_ID")
