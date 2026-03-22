import os


API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")

BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

SESSION_STRING = os.getenv("SESSION_STRING", "assistant_session")

MONGO_URL = os.getenv("MONGO_URL", "")
DB_NAME = os.getenv("DB_NAME", "Pronova")

OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))

COMMAND_PREFIX = os.getenv("PREFIX", "/")


# Optional Buttons
TEXTS = os.getenv("TEXTS", "")
LINKS = os.getenv("LINKS", "")
