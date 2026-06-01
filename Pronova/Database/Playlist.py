from datetime import datetime
from traceback import format_exc
from bson import ObjectId

from Pronova.Utils.Logger import LOGGER
from . import Core

MAX_PLAYLISTS = 10
MAX_SONGS = 50


async def create_playlist(user_id: int, name: str) -> dict | None:
    try:
        db = Core.db
        count = await db.user_playlists.count_documents({"user_id": user_id})
        if count >= MAX_PLAYLISTS:
            return None
        existing = await db.user_playlists.find_one({"user_id": user_id, "name": name})
        if existing:
            return None
        result = await db.user_playlists.insert_one({
            "user_id": user_id,
            "name": name,
            "songs": [],
            "created": datetime.utcnow(),
        })
        doc = await db.user_playlists.find_one({"_id": result.inserted_id})
        return doc
    except Exception:
        LOGGER.error(f"[PLAYLIST CREATE ERROR]\n{format_exc()}")
        return None


async def delete_playlist(user_id: int, playlist_id: str) -> bool:
    try:
        result = await Core.db.user_playlists.delete_one({
            "_id": ObjectId(playlist_id),
            "user_id": user_id,
        })
        return result.deleted_count > 0
    except Exception:
        LOGGER.error(f"[PLAYLIST DELETE ERROR]\n{format_exc()}")
        return False


async def get_playlists(user_id: int) -> list:
    try:
        results = []
        async for doc in Core.db.user_playlists.find(
            {"user_id": user_id},
            {"name": 1, "songs": 1, "created": 1}
        ).sort("created", 1):
            results.append({
                "id": str(doc["_id"]),
                "name": doc["name"],
                "count": len(doc.get("songs", [])),
            })
        return results
    except Exception:
        LOGGER.error(f"[PLAYLIST GET ALL ERROR]\n{format_exc()}")
        return []


async def get_playlist(user_id: int, playlist_id: str) -> dict | None:
    try:
        doc = await Core.db.user_playlists.find_one({
            "_id": ObjectId(playlist_id),
            "user_id": user_id,
        })
        if not doc:
            return None
        return {
            "id": str(doc["_id"]),
            "name": doc["name"],
            "songs": doc.get("songs", []),
        }
    except Exception:
        LOGGER.error(f"[PLAYLIST GET ERROR]\n{format_exc()}")
        return None


async def add_song_to_playlist(user_id: int, playlist_id: str, song: dict) -> bool:
    try:
        db = Core.db
        doc = await db.user_playlists.find_one({
            "_id": ObjectId(playlist_id),
            "user_id": user_id,
        })
        if not doc:
            return False
        songs = doc.get("songs", [])
        if len(songs) >= MAX_SONGS:
            return False
        for s in songs:
            if s.get("url") == song.get("url"):
                return False
        await db.user_playlists.update_one(
            {"_id": ObjectId(playlist_id), "user_id": user_id},
            {"$push": {"songs": {
                "title": song.get("title", "Unknown")[:80],
                "url": song.get("url", ""),
                "duration": song.get("duration_text") or song.get("duration", "0:00"),
            }}}
        )
        return True
    except Exception:
        LOGGER.error(f"[PLAYLIST ADD SONG ERROR]\n{format_exc()}")
        return False


async def remove_song_from_playlist(user_id: int, playlist_id: str, index: int) -> bool:
    try:
        db = Core.db
        doc = await db.user_playlists.find_one({
            "_id": ObjectId(playlist_id),
            "user_id": user_id,
        })
        if not doc:
            return False
        songs = doc.get("songs", [])
        if index < 0 or index >= len(songs):
            return False
        songs.pop(index)
        await db.user_playlists.update_one(
            {"_id": ObjectId(playlist_id), "user_id": user_id},
            {"$set": {"songs": songs}}
        )
        return True
    except Exception:
        LOGGER.error(f"[PLAYLIST REMOVE SONG ERROR]\n{format_exc()}")
        return False


async def rename_playlist(user_id: int, playlist_id: str, new_name: str) -> bool:
    try:
        result = await Core.db.user_playlists.update_one(
            {"_id": ObjectId(playlist_id), "user_id": user_id},
            {"$set": {"name": new_name}}
        )
        return result.modified_count > 0
    except Exception:
        LOGGER.error(f"[PLAYLIST RENAME ERROR]\n{format_exc()}")
        return False
