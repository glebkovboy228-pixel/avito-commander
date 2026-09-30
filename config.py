import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GIGACHAT_AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY", "")

FREE_DAILY_LIMIT = 5

SUBSCRIPTION_PRICES = {
    "basic": 499,
    "pro": 999,
}

ADMIN_IDS = []
