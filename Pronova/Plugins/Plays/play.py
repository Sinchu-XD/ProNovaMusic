from pyrogram import filters
from traceback import format_exc

from Config import OWNER_ID
from Pronova.Bot import bot, engine
from Pronova.Utils.Assistant import get_ass
from Pronova.Utils.Font import sc
from Pronova.Utils.Allow import admin_only, check_ban
from Pronova.Utils.Logger import LOGGER

from Pronova.Database.Songs import inc_song_play
from Pronova.Database.Users import add_user
from Pronova.Database.Chats import add_chat
from Pronova.Database import is_admin_only


STICKER_ID = "CAACAgUAAxkBAAKqc2nhU5hE-49YvygFZrIj1_CvmiMVAALbHwACgUMJV5yYypdtH9s2HgQ"


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

    try:
        mode = await is_admin_only(chat_id)
    except Exception:
        mode = False

    if force:
        if not await admin_only(bot, message=m):
            return
    else:
        if mode:
            if not await admin_only(bot, message=m):
                return

    if not await get_ass(chat_id, m):
        return

    if force:
        try:
            await engine.vc.stop(chat_id)
        except Exception as e:
            LOGGER.error(f"[Force Stop Error] {e}")

    reply = m.reply_to_message

    if reply and (reply.voice or reply.audio or reply.video):
        try:
            path = await reply.download()
        except Exception:
            LOGGER.error(f"[DOWNLOAD ERROR]\n{format_exc()}")
            return await m.reply(sc("download failed"))

        try:
            song, pos = await engine.vc.play_file(
                chat_id,
                path,
                m.from_user.mention,
                reply=reply,
                video=video,
            )
        except Exception as e:
            err = str(e)
            LOGGER.error(format_exc())
            if "CHAT_ADMIN_REQUIRED" in err:
                return await m.reply(sc("voice chat is not started — start it first"))
            return await m.reply(sc(f"❌ Media Play Error:\n{e}"))

        if not song:
            return await m.reply(sc("unable to play media"))

        song_title = getattr(song, "title", None) or "file"
        try:
            await inc_song_play(chat_id, uid, song_title)
        except Exception:
            pass
        return

    if len(m.command) < 2:
        return await m.reply(sc("give song name"))

    query = m.text.split(None, 1)[1]

    try:
        song, pos = await engine.vc.play(
            chat_id,
            query,
            m.from_user.mention,
            video=video,
        )

    except Exception as e:
        LOGGER.error(format_exc())

        err = str(e)

        if "CHANNEL_PRIVATE" in err:
            return await m.reply(sc("assistant banned or not in chat"))
        elif "CHAT_ADMIN_REQUIRED" in err:
            return await m.reply(
                "⚠️ **Voice chat is not active.**\n\n"
                "Please start a voice chat in this group first, then use /play."
            )
        elif "ffmpeg" in err.lower():
            return await m.reply(sc("ffmpeg issue on server"))

        return await m.reply(sc(f"❌ Error:\n{err}"))

    if not song:
        return await m.reply(sc("unable to play song"))

    song_title = getattr(song, "title", None) or "file"
    try:
        await inc_song_play(chat_id, uid, song_title)
    except Exception:
        pass


@bot.on_message(filters.command(["play"]) & filters.group)
async def play(_, m):
    try:
        await safe_delete(m)
        await register_usage(m)
        await handle_play(m)
    except Exception:
        LOGGER.error(f"[PLAY HANDLER ERROR]\n{format_exc()}")


@bot.on_message(filters.command(["playforce"]) & filters.group)
async def playforce(_, m):
    try:
        await safe_delete(m)
        await register_usage(m)
        await handle_play(m, force=True)
    except Exception:
        LOGGER.error(f"[PLAYFORCE HANDLER ERROR]\n{format_exc()}")


@bot.on_message(filters.command(["vplay"]) & filters.group)
async def vplay(_, m):
    try:
        await safe_delete(m)
        await register_usage(m)
        await handle_play(m, video=True)
    except Exception:
        LOGGER.error(f"[VPLAY HANDLER ERROR]\n{format_exc()}")


@bot.on_message(filters.command(["vplayforce"]) & filters.group)
async def vplayforce(_, m):
    try:
        await safe_delete(m)
        await register_usage(m)
        await handle_play(m, force=True, video=True)
    except Exception:
        LOGGER.error(f"[VPLAYFORCE HANDLER ERROR]\n{format_exc()}")
