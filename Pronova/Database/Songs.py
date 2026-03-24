from .Core import db
from .Stats import inc_lifetime, inc_daily
from Pronova.Utils.Logger import LOGGER


def normalize_title(title: str) -> str:
    if not title:
        return ""
    return str(title).strip().lower()


def _to_int(x):
    try:
        return int(x.id) if hasattr(x, "id") else int(x)
    except:
        return None


async def inc_song_play(chat=None, user=None, title=None):
    await inc_lifetime("songs")
    await inc_daily("songs")

    cid = _to_int(chat)
    uid = _to_int(user)


    if cid:
        update_data = {
            "$inc": {
                "songs": 1,  # total songs in chat
            }
        }

        if uid:
            update_data["$inc"][f"users.{uid}"] = 1 

        await db.group_stats.update_one(
            {"chat_id": cid},
            update_data,
            upsert=True,
        )


    title = normalize_title(title)
    if not title:
        return

    await db.songs_stats.update_one(
        {"title": title},
        {"$inc": {"played": 1}},
        upsert=True,
    )

    LOGGER.debug(f"Song tracked → chat={cid}, user={uid}, title={title}")
