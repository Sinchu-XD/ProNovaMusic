from traceback import format_exc
from Pronova.Utils.Logger import LOGGER
from . import Core


async def add_chat(chat):
    try:
        db = Core.db
        cid = chat.id if hasattr(chat, "id") else int(chat)
        doc = await db.chats.find_one({"chat_id": cid})

        if not doc:
            await db.chats.insert_one({
                "chat_id": cid,
                "title": getattr(chat, "title", "Unknown"),
                "username": getattr(chat, "username", None),
                "joined": __import__("datetime").datetime.utcnow(),
                "songs_played": 0,
                "admin_only": False,
            })

    except Exception:
        LOGGER.error(f"[ADD CHAT ERROR]\n{format_exc()}")


async def total_chats():
    try:
        return await Core.db.chats.count_documents({})
    except Exception:
        LOGGER.error(f"[TOTAL CHATS ERROR]\n{format_exc()}")
        return 0


async def get_all_chats():
    try:
        async for doc in Core.db.chats.find({}, {"chat_id": 1}):
            yield str(doc["chat_id"])
    except Exception:
        LOGGER.error(f"[GET CHATS ERROR]\n{format_exc()}")


async def set_admin_only(chat_id: int, value: bool):
    try:
        await Core.db.chats.update_one(
            {"chat_id": chat_id},
            {"$set": {"admin_only": value}},
            upsert=True,
        )
    except Exception:
        LOGGER.error(f"[SET ADMIN ONLY ERROR]\n{format_exc()}")


async def is_admin_only(chat_id: int) -> bool:
    try:
        doc = await Core.db.chats.find_one({"chat_id": chat_id})
        return bool(doc and doc.get("admin_only"))
    except Exception:
        LOGGER.error(f"[IS ADMIN ONLY ERROR]\n{format_exc()}")
        return False


async def inc_chat_song(chat_id: int):
    try:
        await Core.db.chats.update_one(
            {"chat_id": chat_id},
            {"$inc": {"songs_played": 1}},
        )
    except Exception:
        LOGGER.error(f"[INC CHAT SONG ERROR]\n{format_exc()}")


async def top_groups(limit=5):
    try:
        results = []
        async for doc in Core.db.chats.find(
            {"songs_played": {"$gt": 0}},
            {"chat_id": 1, "songs_played": 1},
        ).sort("songs_played", -1).limit(limit):
            results.append((str(doc["chat_id"]), doc["songs_played"]))
        return results
    except Exception:
        LOGGER.error(f"[TOP GROUPS ERROR]\n{format_exc()}")
        return []
