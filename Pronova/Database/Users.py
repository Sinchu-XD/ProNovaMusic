from traceback import format_exc
from Pronova.Utils.Logger import LOGGER
from . import Core


async def add_user(user):
    try:
        db = Core.db
        uid = user.id if hasattr(user, "id") else int(user)
        doc = await db.users.find_one({"user_id": uid})

        if not doc:
            await db.users.insert_one({
                "user_id": uid,
                "first_name": getattr(user, "first_name", "Unknown"),
                "username": getattr(user, "username", None),
                "joined": __import__("datetime").datetime.utcnow(),
                "songs_played": 0,
            })

    except Exception:
        LOGGER.error(f"[ADD USER ERROR]\n{format_exc()}")


async def remove_user(user_id: int):
    try:
        await Core.db.users.delete_one({"user_id": user_id})
    except Exception:
        LOGGER.error(f"[REMOVE USER ERROR]\n{format_exc()}")


async def get_users():
    try:
        async for doc in Core.db.users.find({}, {"user_id": 1}):
            yield str(doc["user_id"])
    except Exception:
        LOGGER.error(f"[GET USERS ERROR]\n{format_exc()}")


async def total_users():
    try:
        return await Core.db.users.count_documents({})
    except Exception:
        LOGGER.error(f"[TOTAL USERS ERROR]\n{format_exc()}")
        return 0


async def inc_user_song(user_id: int):
    try:
        await Core.db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"songs_played": 1}},
        )
    except Exception:
        LOGGER.error(f"[INC SONG ERROR]\n{format_exc()}")


async def top_song_players(limit=5):
    try:
        results = []
        async for doc in Core.db.users.find(
            {"songs_played": {"$gt": 0}},
            {"user_id": 1, "songs_played": 1},
        ).sort("songs_played", -1).limit(limit):
            results.append((str(doc["user_id"]), doc["songs_played"]))
        return results
    except Exception:
        LOGGER.error(f"[TOP PLAYERS ERROR]\n{format_exc()}")
        return []
