from datetime import datetime
from .Core import db
from .Stats import inc_lifetime, inc_daily
from Pronova.Utils.Logger import LOGGER


def _chat_id(chat):
    try:
        return int(chat.id) if hasattr(chat, "id") else int(chat)
    except:
        return None


async def add_chat(chat):
    cid = _chat_id(chat)
    if not cid:
        return

    res = await db.chats.update_one(
        {"chat_id": cid},
        {
            "$setOnInsert": {
                "chat_id": cid,
                "join_date": datetime.utcnow(),
            }
        },
        upsert=True,
    )


    await db.group_stats.update_one(
        {"chat_id": cid},
        {
            "$setOnInsert": {
                "chat_id": cid,
                "songs": 0,
                "users": {},   # 👈 for top users
            }
        },
        upsert=True,
    )

    if res.upserted_id:
        await inc_lifetime("chats")
        await inc_daily("chats")
        LOGGER.info(f"New chat added: {cid}")
