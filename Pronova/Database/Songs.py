from .Core import db
from .Stats import inc_lifetime, inc_daily


def normalize_title(title: str) -> str:
    if not title:
        return ""
    return str(title).strip().lower()


def _to_int(x):
    try:
        return int(x.id) if hasattr(x, "id") else int(x)
    except:
        return None


async def inc_song_play(chat=None, title=None):
    await inc_lifetime("songs")
    await inc_daily("songs")

    cid = _to_int(chat)
    if cid:
        await db.group_stats.update_one(
            {"chat_id": cid},
            {"$inc": {"songs": 1}},
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


async def most_played(limit: int = 10):
    result = []

    async for s in db.songs_stats.find(
        {},
        {"title": 1, "played": 1, "_id": 0}
    ).sort("played", -1).limit(limit):

        try:
            title = s["title"]
            played = int(s.get("played", 0))
        except:
            continue

        if played > 0:
            result.append((title, played))

    return result
