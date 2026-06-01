from traceback import format_exc

import asyncio
from pyrogram import filters

from Pronova.Bot import bot
from Pronova.Database import set_admin_only, is_admin_only
from Pronova.Utils.Allow import admin_only
from Pronova.Utils.Logger import LOGGER


@bot.on_message(filters.command("adminplay") & filters.group)
async def admin_play(_, m):
    try:
        if not m.from_user:
            return

        if not await admin_only(bot, message=m):
            return

        await set_admin_only(m.chat.id, True)

        LOGGER.info(f"[PlayMode] AdminOnly Enabled in {m.chat.id} by {m.from_user.id}")

        await m.reply(
            "🔒 **Admin Play Mode Enabled**\n\n"
            "Now only admins can use play commands."
        )
    except Exception:
        LOGGER.error(f"[AdminPlay Error]\n{format_exc()}")


@bot.on_message(filters.command("allplay") & filters.group)
async def all_play(_, m):
    try:
        if not m.from_user:
            return

        if not await admin_only(bot, message=m):
            return

        await set_admin_only(m.chat.id, False)

        LOGGER.info(f"[PlayMode] Everyone Mode Enabled in {m.chat.id} by {m.from_user.id}")

        await m.reply(
            "🌍 **Everyone Play Mode Enabled**\n\n"
            "Now everyone can use play commands."
        )
    except Exception:
        LOGGER.error(f"[AllPlay Error]\n{format_exc()}")


@bot.on_message(filters.command("playmode") & filters.group)
async def playmode(_, m):
    try:
        if not m.from_user:
            return

        mode = await is_admin_only(m.chat.id)

        if mode:
            text = "🔒 **Play Mode : Admin Only**"
        else:
            text = "🌍 **Play Mode : Everyone**"

        await m.reply(text)

    except Exception as e:
        LOGGER.error(f"[PlayMode Error] {e}")
        try:
            await m.reply("❌ Failed to fetch play mode.")
        except Exception:
            pass
