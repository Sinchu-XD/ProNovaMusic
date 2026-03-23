from pyrogram import filters
from traceback import format_exc
from Config import *

from Pronova.Bot import bot, engine
from Pronova.Utils.Assistant import get_ass
from Pronova.Utils.Font import sc
from Pronova.Utils.Permission import admin_only, check_ban

from Pronova.Database.Songs import inc_song_play
from Pronova.Database.Users import add_user
from Pronova.Database.Chats import add_chat


async def safe_delete(m):
    try:
        await m.delete()
    except Exception:
        pass


async def register_usage(m):
    if not m.from_user:
        return

    try:
        await add_user(m.from_user)
        await add_chat(m.chat)
    except Exception:
        pass


async def handle_play(m, force=False, video=False):

    if not m.from_user:
        return

    uid = m.from_user.id
    chat_id = m.chat.id

    if await check_ban(message=m):
        return

    if force:
        if not await admin_only(bot, message=m):
            return
    else:
        if not await admin_only(bot, message=m):
            return

    if not await get_ass(chat_id, m):
        return

    if force:
        try:
            await engine.vc.stop(chat_id)
        except Exception:
            pass

    reply = m.reply_to_message

    if reply and (reply.voice or reply.audio or reply.video):

        try:
            path = await reply.download()
        except Exception:
            return await m.reply(sc("download failed"))

        try:
            song, title = await engine.vc.play_file(
                chat_id,
                path,
                m.from_user.mention,
                reply=reply,
                video=video
            )
        except Exception:
            return await m.reply(sc("unable to play media"))

        if not song:
            return await m.reply(sc("unable to play media"))

        await inc_song_play(chat_id, title)
        return

    if len(m.command) < 2:
        return await m.reply(sc("give song name"))

    query = m.text.split(None, 1)[1]

    try:
        song, title = await engine.vc.play(
            chat_id,
            query,
            m.from_user.mention,
            video=video
        )
    except Exception:
        return await m.reply(sc("unable to play song"))

    if not song:
        return await m.reply(sc("unable to play song"))

    await inc_song_play(chat_id, title or query)


@bot.on_message(filters.command(["play"]) & filters.group)
async def play(_, m):
    await safe_delete(m)
    await register_usage(m)
    await handle_play(m)


@bot.on_message(filters.command(["playforce"]) & filters.group)
async def playforce(_, m):
    await safe_delete(m)
    await register_usage(m)
    await handle_play(m, force=True)


@bot.on_message(filters.command(["vplay"]) & filters.group)
async def vplay(_, m):
    await safe_delete(m)
    await register_usage(m)
    await handle_play(m, video=True)


@bot.on_message(filters.command(["vplayforce"]) & filters.group)
async def vplayforce(_, m):
    await safe_delete(m)
    await register_usage(m)
    await handle_play(m, force=True, video=True)
