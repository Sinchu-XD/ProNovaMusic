from pyrogram import filters
from traceback import format_exc
from Config import *
from Pronova.Bot import bot, engine
from Pronova.Utils.Assistant import get_ass
from Pronova.Utils.Font import sc
from Pronova.Utils.Permission import is_allowed

from Pronova.Database.Songs import inc_song_play
from Pronova.Database.Bans import is_banned, is_gbanned
from Pronova.Database.Users import add_user
from Pronova.Database.Chats import add_chat
from Pronova.Database.Auth import is_auth

from Pronova.Utils.Logger import LOGGER


async def check_ban(m):
    if not m.from_user:
        return True

    uid = m.from_user.id
    chat_id = m.chat.id

    if await is_gbanned(uid):
        LOGGER.warning(f"[GBANNED USER] {uid}")
        await m.reply(sc("you are gbanned"))
        return True

    if await is_banned(chat_id, uid):
        LOGGER.warning(f"[BANNED IN CHAT] {uid} in {chat_id}")
        await m.reply(sc("you are banned in this chat"))
        return True

    return False


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
        LOGGER.error(f"[USAGE REGISTER ERROR]\n{format_exc()}")


async def handle_play(m, force=False, video=False):

    if not m.from_user:
        return

    uid = m.from_user.id
    chat_id = m.chat.id

    LOGGER.info(f"[PLAY CMD] User: {uid} | Chat: {chat_id} | Force: {force} | Video: {video}")

    if await check_ban(m):
        return

    if force:
        try:
            member = await bot.get_chat_member(chat_id, uid)
            if member.status not in ("administrator", "creator", "owner"):
                LOGGER.warning(f"[FORCE DENIED] {uid} not admin in {chat_id}")
                return await m.reply(sc("admins only"))
        except Exception:
            LOGGER.error(f"[ADMIN CHECK ERROR]\n{format_exc()}")
            return
    else:
        if not await is_auth(chat_id, uid):
            if not await is_allowed(bot, m, notify=True):
                LOGGER.warning(f"[NOT ALLOWED] {uid} in {chat_id}")
                return

    if not await get_ass(chat_id, m):
        LOGGER.warning(f"[ASSISTANT JOIN FAILED] Chat: {chat_id}")
        return

    if force:
        try:
            LOGGER.info(f"[FORCE STOP] Chat: {chat_id}")
            await engine.vc.stop(chat_id)
        except Exception:
            LOGGER.error(f"[FORCE STOP ERROR]\n{format_exc()}")

    reply = m.reply_to_message

    if reply and (reply.voice or reply.audio or reply.video):

        LOGGER.info(f"[MEDIA PLAY] Chat: {chat_id}")

        try:
            path = await reply.download()
            LOGGER.debug(f"[DOWNLOADED FILE] {path}")
        except Exception:
            LOGGER.error(f"[DOWNLOAD FAILED]\n{format_exc()}")
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
            LOGGER.error(f"[PLAY FILE ERROR]\n{format_exc()}")
            return await m.reply(sc("unable to play media"))

        if not song:
            LOGGER.warning("[PLAY FILE FAILED]")
            return await m.reply(sc("unable to play media"))

        await inc_song_play(chat_id, title)
        LOGGER.info(f"[MEDIA PLAY SUCCESS] {title}")
        return

    if len(m.command) < 2:
        LOGGER.warning("[NO QUERY PROVIDED]")
        return await m.reply(sc("give song name"))

    query = m.text.split(None, 1)[1]

    LOGGER.info(f"[SEARCH QUERY] {query}")

    try:
        song, title = await engine.vc.play(
            chat_id,
            query,
            m.from_user.mention,
            video=video
        )
    except Exception:
        LOGGER.error(f"[PLAY ERROR]\n{format_exc()}")
        return await m.reply(sc("unable to play song"))

    if not song:
        LOGGER.warning(f"[PLAY FAILED] Query: {query}")
        return await m.reply(sc("unable to play song"))

    await inc_song_play(chat_id, title or query)
    LOGGER.info(f"[PLAY SUCCESS] {title or query}")


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
