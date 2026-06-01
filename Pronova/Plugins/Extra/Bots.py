from traceback import format_exc

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMembersFilter, ParseMode

from Pronova.Bot import bot
from Pronova.Utils.Logger import LOGGER


@bot.on_message(filters.command("bots") & filters.group)
async def list_bots(client, message: Message):
    try:
        try:
            await message.delete()
        except Exception:
            pass

        bot_list = []
        bot_count = 0

        status_msg = await message.reply_text(
            "🔍 <b>Scanning for bots...</b>", parse_mode=ParseMode.HTML
        )

        async for member in client.get_chat_members(
            message.chat.id, filter=ChatMembersFilter.BOTS
        ):
            bot_count += 1
            bot_username = (
                f"@{member.user.username}" if member.user.username else "No Username"
            )
            bot_list.append(
                f"{bot_count}. <a href='tg://user?id={member.user.id}'>{member.user.first_name}</a> - {bot_username}"
            )

        if bot_count == 0:
            await status_msg.edit_text(
                "❌ <b>No bots found in this group.</b>", parse_mode=ParseMode.HTML
            )
            return

        response = f"🤖 <b>Bots in {message.chat.title}</b>\n\n"
        response += "<blockquote>" + "\n".join(bot_list) + "</blockquote>"
        response += f"\n\n📊 <b>Total Bots:</b> {bot_count}"

        await status_msg.edit_text(
            response, disable_web_page_preview=True, parse_mode=ParseMode.HTML
        )

    except Exception as e:
        LOGGER.error(f"[BOTS CMD ERROR]\n{format_exc()}")
        try:
            await message.reply_text(
                f"⚠️ <b>Error:</b> {str(e)}", parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
