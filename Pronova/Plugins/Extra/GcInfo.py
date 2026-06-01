from traceback import format_exc

from pyrogram import Client, filters
from pyrogram.enums import ChatType, ParseMode, ChatMemberStatus, ChatMembersFilter
from pyrogram.types import Message

from Pronova.Bot import bot
from Pronova.Utils.Logger import LOGGER


@bot.on_message(filters.command(["groupdata", "chatinfo", "groupinfo"]) & filters.group)
async def group_data_handler(client: Client, message: Message):
    try:
        try:
            await message.delete()
        except Exception:
            pass

        chat = message.chat
        chat_id = chat.id

        try:
            chat_info = await client.get_chat(chat_id)
        except Exception as e:
            return await message.reply_text(
                f"<blockquote>❌ <b>ᴇʀʀᴏʀ ɢᴇᴛᴛɪɴɢ ᴄʜᴀᴛ:</b>\n<code>{str(e)}</code></blockquote>",
                parse_mode=ParseMode.HTML,
            )

        total_members = 0
        admin_count = 0
        bot_count = 0
        banned_count = 0
        deleted_count = 0
        premium_count = 0

        try:
            total_members = await client.get_chat_members_count(chat_id)
        except Exception:
            pass

        try:
            async for _ in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
                admin_count += 1
        except Exception:
            pass

        try:
            async for _ in client.get_chat_members(chat_id, filter=ChatMembersFilter.BOTS):
                bot_count += 1
        except Exception:
            pass

        try:
            async for _ in client.get_chat_members(chat_id, filter=ChatMembersFilter.BANNED):
                banned_count += 1
        except Exception:
            pass

        try:
            async for member in client.get_chat_members(chat_id, filter=ChatMembersFilter.RECENT):
                if getattr(member.user, "is_deleted", False):
                    deleted_count += 1
                if getattr(member.user, "is_premium", False):
                    premium_count += 1
        except Exception:
            pass

        info_lines = ["<b>📊 GROUP INFORMATION</b>\n"]

        info_lines.append(f"<b>📌 ɴᴀᴍᴇ:</b> {chat_info.title}")
        info_lines.append(f"<b>🆔 ɪᴅ:</b> <code>{chat_id}</code>")

        if getattr(chat_info, "username", None):
            info_lines.append(f"<b>🔗 ᴜꜱᴇʀɴᴀᴍᴇ:</b> @{chat_info.username}")

        chat_type_str = (
            "ɢʀᴏᴜᴘ" if chat.type == ChatType.GROUP else "ꜱᴜᴘᴇʀɢʀᴏᴜᴘ"
        )
        info_lines.append(f"<b>📂 ᴛʏᴘᴇ:</b> {chat_type_str}")

        info_lines.append(f"\n<b>👥 ᴍᴇᴍʙᴇʀꜱ:</b> {total_members}")
        info_lines.append(f"<b>👮 ᴀᴅᴍɪɴꜱ:</b> {admin_count}")
        info_lines.append(f"<b>🤖 ʙᴏᴛꜱ:</b> {bot_count}")

        if banned_count > 0:
            info_lines.append(f"<b>🚫 ʙᴀɴɴᴇᴅ:</b> {banned_count}")

        if deleted_count > 0:
            info_lines.append(f"<b>👻 ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛꜱ:</b> {deleted_count}")

        if premium_count > 0:
            info_lines.append(f"<b>⭐ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ:</b> {premium_count}")

        if getattr(chat_info, "description", None):
            desc = chat_info.description
            if len(desc) > 100:
                desc = desc[:100] + "..."
            info_lines.append(f"\n<b>📝 ᴅᴇꜱᴄʀɪᴘᴛɪᴏɴ:</b>\n{desc}")

        if getattr(chat_info, "linked_chat", None):
            info_lines.append(
                f"\n<b>🔗 ʟɪɴᴋᴇᴅ ᴄʜᴀɴɴᴇʟ:</b> {chat_info.linked_chat.title}"
            )
            info_lines.append(
                f"<b>🆔 ᴄʜᴀɴɴᴇʟ ɪᴅ:</b> <code>{chat_info.linked_chat.id}</code>"
            )

        if getattr(chat_info, "invite_link", None):
            info_lines.append(f"\n<b>🔗 ɪɴᴠɪᴛᴇ ʟɪɴᴋ:</b> {chat_info.invite_link}")

        try:
            user_member = await client.get_chat_member(chat_id, message.from_user.id)
            if user_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                role = (
                    "ᴏᴡɴᴇʀ"
                    if user_member.status == ChatMemberStatus.OWNER
                    else "ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀ"
                )
                info_lines.append(f"\n<b>🔐 ʏᴏᴜʀ ʀᴏʟᴇ:</b> {role}")
        except Exception:
            pass

        response = "<blockquote>" + "\n".join(info_lines) + "</blockquote>"

        await message.reply_text(
            response, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )

    except Exception as e:
        LOGGER.error(f"[GCINFO ERROR]\n{format_exc()}")
        try:
            await message.reply_text(
                f"<blockquote>❌ <b>ᴇʀʀᴏʀ ɢᴇᴛᴛɪɴɢ ɢʀᴏᴜᴘ ᴅᴀᴛᴀ:</b>\n<code>{str(e)}</code></blockquote>",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
