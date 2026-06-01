from traceback import format_exc
from Pronova.Utils.Logger import LOGGER
from . import Core


async def add_auth(chat_id: int, user_id: int) -> bool:
    try:
        db = Core.db
        existing = await db.auth_users.find_one({"chat_id": chat_id, "user_id": user_id})
        if existing:
            return False
        await db.auth_users.insert_one({"chat_id": chat_id, "user_id": user_id})
        return True
    except Exception:
        LOGGER.error(f"[ADD AUTH ERROR]\n{format_exc()}")
        return False


async def remove_auth(chat_id: int, user_id: int):
    try:
        await Core.db.auth_users.delete_one({"chat_id": chat_id, "user_id": user_id})
    except Exception:
        LOGGER.error(f"[REMOVE AUTH ERROR]\n{format_exc()}")


async def is_auth(chat_id: int, user_id: int) -> bool:
    try:
        doc = await Core.db.auth_users.find_one({"chat_id": chat_id, "user_id": user_id})
        return doc is not None
    except Exception:
        LOGGER.error(f"[IS AUTH ERROR]\n{format_exc()}")
        return False


async def get_auth_users(chat_id: int):
    try:
        return [
            doc["user_id"]
            async for doc in Core.db.auth_users.find({"chat_id": chat_id}, {"user_id": 1})
        ]
    except Exception:
        LOGGER.error(f"[GET AUTH USERS ERROR]\n{format_exc()}")
        return []
