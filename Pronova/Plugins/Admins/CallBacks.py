from pyrogram import filters
import time

from Pronova.Bot import bot, engine
from Pronova.Utils.Font import sc
from Pronova.Utils.Allow import admin_only


LAST_ACTION = {}


def can_send(chat_id, cooldown=3):
    now = time.time()
    last = LAST_ACTION.get(chat_id, 0)

    if now - last < cooldown:
        return False

    LAST_ACTION[chat_id] = now
    return True


async def safe_action(action, chat_id):
    try:
        return await action(chat_id)
    except:
        return None


async def safe_reply(m, text):
    if can_send(m.chat.id):
        try:
            await m.reply(text, disable_notification=True)
        except:
            pass


@bot.on_callback_query(filters.regex("^vc_"))
async def vc_buttons(_, cq):

    if not cq.message:
        return

    m = cq.message
    chat_id = m.chat.id
    user = cq.from_user

    if not user or user.is_bot:
        return

    if not await admin_only(bot, cq=cq):
        return

    if cq.data == "vc_skip":
        await safe_action(engine.vc.skip, chat_id)
        await safe_reply(m, sc("song skipped"))

    elif cq.data == "vc_end":
        if chat_id in engine.vc.player.queues:
            await safe_action(engine.vc.stop, chat_id)
        await safe_reply(m, sc("playback ended"))

    elif cq.data == "vc_pause":
        await safe_action(engine.vc.pause, chat_id)
        await safe_reply(m, sc("paused"))

    elif cq.data == "vc_resume":
        await safe_action(engine.vc.resume, chat_id)
        await safe_reply(m, sc("resumed"))
