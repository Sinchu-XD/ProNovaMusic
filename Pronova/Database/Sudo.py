from traceback import format_exc
from Pronova.Utils.Logger import LOGGER
from . import Core


async def add_sudo(user_id: int) -> bool:
    try:
        db = Core.db
        existing = await db.sudo_users.find_one({"user_id": user_id})
        if existing:
            return False
        await db.sudo_users.insert_one({"user_id": user_id})
        return True
    except Exception:
        LOGGER.error(f"[ADD SUDO ERROR]\n{format_exc()}")
        return False


async def remove_sudo(user_id: int):
    try:
        await Core.db.sudo_users.delete_one({"user_id": user_id})
    except Exception:
        LOGGER.error(f"[REMOVE SUDO ERROR]\n{format_exc()}")


async def is_sudo(user_id: int) -> bool:
    try:
        doc = await Core.db.sudo_users.find_one({"user_id": user_id})
        return doc is not None
    except Exception:
        LOGGER.error(f"[IS SUDO ERROR]\n{format_exc()}")
        return False


async def get_all_sudo():
    try:
        return [
            doc["user_id"]
            async for doc in Core.db.sudo_users.find({}, {"user_id": 1})
        ]
    except Exception:
        LOGGER.error(f"[GET ALL SUDO ERROR]\n{format_exc()}")
        return []
