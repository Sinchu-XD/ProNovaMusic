from traceback import format_exc
from Pronova.Utils.Logger import LOGGER
from . import Core


async def ban_user(chat_id: int, user_id: int):
    try:
        db = Core.db
        existing = await db.banned.find_one({"chat_id": chat_id, "user_id": user_id})
        if not existing:
            await db.banned.insert_one({"chat_id": chat_id, "user_id": user_id})
    except Exception:
        LOGGER.error(f"[BAN ERROR]\n{format_exc()}")


async def unban_user(chat_id: int, user_id: int):
    try:
        await Core.db.banned.delete_one({"chat_id": chat_id, "user_id": user_id})
    except Exception:
        LOGGER.error(f"[UNBAN ERROR]\n{format_exc()}")


async def is_banned(chat_id: int, user_id: int) -> bool:
    try:
        doc = await Core.db.banned.find_one({"chat_id": chat_id, "user_id": user_id})
        return doc is not None
    except Exception:
        LOGGER.error(f"[IS BANNED ERROR]\n{format_exc()}")
        return False


async def get_banned(chat_id: int):
    try:
        return [
            doc["user_id"]
            async for doc in Core.db.banned.find({"chat_id": chat_id}, {"user_id": 1})
        ]
    except Exception:
        LOGGER.error(f"[GET BANNED ERROR]\n{format_exc()}")
        return []


async def total_banned():
    try:
        return await Core.db.banned.count_documents({})
    except Exception:
        LOGGER.error(f"[TOTAL BANNED ERROR]\n{format_exc()}")
        return 0


async def gban_user(user_id: int):
    try:
        db = Core.db
        existing = await db.gbanned.find_one({"user_id": user_id})
        if not existing:
            await db.gbanned.insert_one({"user_id": user_id})
    except Exception:
        LOGGER.error(f"[GBAN ERROR]\n{format_exc()}")


async def ungban_user(user_id: int):
    try:
        await Core.db.gbanned.delete_one({"user_id": user_id})
    except Exception:
        LOGGER.error(f"[UNGBAN ERROR]\n{format_exc()}")


async def is_gbanned(user_id: int) -> bool:
    try:
        doc = await Core.db.gbanned.find_one({"user_id": user_id})
        return doc is not None
    except Exception:
        LOGGER.error(f"[IS GBANNED ERROR]\n{format_exc()}")
        return False


async def get_gbanned():
    try:
        return [
            doc["user_id"]
            async for doc in Core.db.gbanned.find({}, {"user_id": 1})
        ]
    except Exception:
        LOGGER.error(f"[GET GBANNED ERROR]\n{format_exc()}")
        return []
