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
