from datetime import datetime, timedelta
from traceback import format_exc
from Pronova.Utils.Logger import LOGGER
from . import Core


def _today():
    return datetime.utcnow().strftime("%Y-%m-%d")


async def inc_lifetime(key: str):
    try:
        await Core.db.lifetime.update_one(
            {"key": key},
            {"$inc": {"value": 1}},
            upsert=True,
        )
    except Exception:
        LOGGER.error(f"[INC LIFETIME ERROR]\n{format_exc()}")


async def get_lifetime(key: str) -> int:
    try:
        doc = await Core.db.lifetime.find_one({"key": key})
        return doc.get("value", 0) if doc else 0
    except Exception:
        LOGGER.error(f"[GET LIFETIME ERROR]\n{format_exc()}")
        return 0


async def inc_daily(key: str):
    try:
        today = _today()
        await Core.db.analytics.update_one(
            {"date": today},
            {"$inc": {key: 1}},
            upsert=True,
        )
    except Exception:
        LOGGER.error(f"[INC DAILY ERROR]\n{format_exc()}")


async def sum_range(days: int, key: str) -> int:
    try:
        start = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        total = 0
        async for doc in Core.db.analytics.find({"date": {"$gte": start}}, {key: 1}):
            total += doc.get(key, 0)
        return total
    except Exception:
        LOGGER.error(f"[SUM RANGE ERROR]\n{format_exc()}")
        return 0
