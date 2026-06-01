import asyncio
from traceback import format_exc

import aiohttp
from pyrogram import filters
from pyrogram.types import Message

from Pronova.Bot import bot
from Pronova.Utils.Logger import LOGGER


CRICKET_API = "https://api.cricapi.com/v1/currentMatches?apikey={key}&offset=0"
SCORE_API = "https://api.cricapi.com/v1/match_info?apikey={key}&id={match_id}"


async def fetch_json(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    return await r.json()
    except Exception as e:
        LOGGER.error(f"[CRICKET FETCH ERROR] {e}")
    return None


def format_match(match):
    try:
        name = match.get("name", "Unknown Match")
        status = match.get("status", "")
        score = match.get("score", [])
        venue = match.get("venue", "Unknown")

        text = f"🏏 **{name}**\n"
        text += f"📍 {venue}\n"

        for s in score:
            inning = s.get("inning", "")
            runs = s.get("r", 0)
            wickets = s.get("w", 0)
            overs = s.get("o", 0)
            text += f"\n▫ {inning}: {runs}/{wickets} ({overs} ov)"

        if status:
            text += f"\n\n📢 **Status:** {status}"

        return text
    except Exception:
        return "Error formatting match"


@bot.on_message(filters.command("cricket") & filters.group)
async def cricket_live(_, message: Message):
    try:
        try:
            await message.delete()
        except Exception:
            pass

        from Config import CRICKET_API_KEY

        if not CRICKET_API_KEY:
            return await message.reply(
                "❌ **Cricket API key not configured.**\n"
                "Set `CRICKET_API_KEY` in your `.env` file."
            )

        msg = await message.reply("🔎 **Fetching live cricket scores...**")

        url = CRICKET_API.format(key=CRICKET_API_KEY)
        data = await fetch_json(url)

        if not data or data.get("status") != "success":
            return await msg.edit("❌ Could not fetch scores. API may be down.")

        matches = data.get("data", [])

        if not matches:
            return await msg.edit("📭 No live matches at the moment.")

        text = "🏏 **Live Cricket Scores**\n\n"

        for match in matches[:5]:
            text += format_match(match) + "\n\n---\n\n"

        try:
            await msg.edit(text)
        except Exception:
            pass

    except Exception:
        LOGGER.error(f"[CRICKET CMD ERROR]\n{format_exc()}")
        try:
            await message.reply("❌ Error fetching cricket scores.")
        except Exception:
            pass


@bot.on_callback_query(filters.regex("^cricket_refresh$"))
async def cricket_refresh(_, cq):
    try:
        if not cq.message:
            return

        await cq.answer("Refreshing...", show_alert=False)

        from Config import CRICKET_API_KEY

        if not CRICKET_API_KEY:
            return

        url = CRICKET_API.format(key=CRICKET_API_KEY)
        data = await fetch_json(url)

        if not data or data.get("status") != "success":
            return

        matches = data.get("data", [])

        if not matches:
            return

        text = "🏏 **Live Cricket Scores**\n\n"

        for match in matches[:5]:
            text += format_match(match) + "\n\n---\n\n"

        try:
            await cq.message.edit(text)
        except Exception:
            pass

    except Exception:
        LOGGER.error(f"[CRICKET REFRESH ERROR]\n{format_exc()}")
