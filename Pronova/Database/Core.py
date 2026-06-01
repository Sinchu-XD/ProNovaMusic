import asyncio
from traceback import format_exc

import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING
from datetime import datetime, timedelta

from Pronova.Utils.Logger import LOGGER
from Config import DATABASE_URI, DATABASE_NAME


client = None
db = None


async def setup_database():
    global client, db

    LOGGER.info("[DB] Connecting to MongoDB...")

    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
        db = client[DATABASE_NAME]

        await client.admin.command("ping")
        LOGGER.info("[DB] Connected successfully")

        await _create_indexes()
        LOGGER.info("[DB] Indexes ensured")

    except Exception:
        LOGGER.error(f"[DB SETUP ERROR]\n{format_exc()}")
        raise


async def _safe_create_index(collection, keys, **kwargs):
    try:
        await collection.create_index(keys, **kwargs)
    except Exception:
        LOGGER.error(f"[INDEX ERROR] {collection.name}\n{format_exc()}")


async def _create_indexes():
    await _safe_create_index(db.users, [("user_id", ASCENDING)], unique=True)
    await _safe_create_index(db.chats, [("chat_id", ASCENDING)], unique=True)
    await _safe_create_index(db.banned, [("chat_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
    await _safe_create_index(db.gbanned, [("user_id", ASCENDING)], unique=True)
    await _safe_create_index(db.sudo_users, [("user_id", ASCENDING)], unique=True)
    await _safe_create_index(db.auth_users, [("chat_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
    await _safe_create_index(db.analytics, [("date", ASCENDING)])
    await _safe_create_index(db.songs, [("title", ASCENDING)])
    await _safe_create_index(db.songs, [("plays", DESCENDING)])
