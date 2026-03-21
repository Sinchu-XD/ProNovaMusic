import os
from motor.motor_asyncio import AsyncIOMotorClient
from Config import MONGO_URL

DB_NAME = os.getenv("DB_NAME", "Pronova")


client = AsyncIOMotorClient(
    MONGO_URL,
    maxPoolSize=100,
    minPoolSize=10,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=5000,
)

db = client[DB_NAME]


async def setup_database():
    try:
        await client.admin.command("ping")
        print("✅ MongoDB Connected")
    except Exception as e:
        print("❌ MongoDB Connection Failed:", e)
        return

    try:
        await db.users.create_index("user_id", unique=True)
        await db.users_backup.create_index("user_id", unique=True) 

        await db.chats.create_index("chat_id", unique=True)
        await db.group_stats.create_index("chat_id", unique=True)
        await db.songs_stats.create_index("title", unique=True)

        await db.banned.create_index(
            [("chat_id", 1), ("user_id", 1)],
            unique=True
        )

        await db.gbanned.create_index("user_id", unique=True)
        await db.daily.create_index("date", unique=True)
        await db.gc_activity.create_index("chat_id", unique=True)
        await db.afk.create_index("user_id", unique=True)
        await db.play_mode.create_index("chat_id", unique=True)

        await db.sudo_users.create_index(
            "user_id",
            unique=True
        )

        await db.auth_users.create_index(
            [("chat_id", 1), ("user_id", 1)],
            unique=True
        )

        await db.yt_stream_cache.create_index("_id", unique=True)

        print("✅ MongoDB Indexes Ready")

    except Exception as e:
        print("❌ Index Creation Error:", e)
