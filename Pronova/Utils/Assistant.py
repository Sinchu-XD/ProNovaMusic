import asyncio

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    UserAlreadyParticipant,
    PeerIdInvalid,
    UserBannedInChannel,
    UserNotParticipant,
    ChannelPrivate
)

from Pronova.Bot import bot, user
from Pronova.Utils.Font import sc
from Pronova.Utils.Logger import LOGGER


ASSISTANT_ID = None
ASSISTANT_USERNAME = None

JOINING = set()
LOCK = asyncio.Lock()


async def setup_assistant():
    global ASSISTANT_ID, ASSISTANT_USERNAME

    async with LOCK:
        if ASSISTANT_ID:
            return

        me = await user.get_me()
        ASSISTANT_ID = me.id
        ASSISTANT_USERNAME = me.username or str(me.id)


async def is_assistant_in_chat(chat_id):
    try:
        # 🔥 resolve chat first
        chat = await user.get_chat(chat_id)

        member = await user.get_chat_member(chat.id, ASSISTANT_ID)

        return member.status not in (
            ChatMemberStatus.LEFT,
            ChatMemberStatus.BANNED
        )

    except UserNotParticipant:
        return False

    except UserBannedInChannel:
        return False

    except ChannelPrivate:
        return False

    except Exception as e:
        LOGGER.error(f"[Assistant Check Error] {e}")
        return False
        
async def get_ass(chat_id, m=None):
    global ASSISTANT_ID

    if not ASSISTANT_ID:
        await setup_assistant()

    if await is_assistant_in_chat(chat_id):
        return True

    if chat_id in JOINING:
        return False

    JOINING.add(chat_id)

    try:
        bot_me = await bot.get_me()
        bot_member = await bot.get_chat_member(chat_id, bot_me.id)

        if not bot_member.privileges or not bot_member.privileges.can_invite_users:
            raise ChatAdminRequired

        try:
            link = await bot.export_chat_invite_link(chat_id)
            await user.join_chat(link)
            await asyncio.sleep(2)

            if await is_assistant_in_chat(chat_id):
                return True

        except UserAlreadyParticipant:
            if await is_assistant_in_chat(chat_id):
                return True

        except Exception as e:
            LOGGER.error(f"[Join Failed, Trying Unban] {e}")

        if not (bot_member.privileges and bot_member.privileges.can_restrict_members):
            if m:
                username = f"@{ASSISTANT_USERNAME}" if ASSISTANT_USERNAME else "No username"
                
                await m.reply(
                    sc(
                        "Assistant Is Banned In This Group\n"
                        "Bot does not have ban/unban rights.\n"
                        "Please Unban It Manually Using\n"
                        f" /unban {ASSISTANT_ID} or /unban {username}"
                    )
                )
            return False

        try:
            await bot.unban_chat_member(chat_id, ASSISTANT_ID)
            await asyncio.sleep(2)
        except Exception as e:
            LOGGER.error(f"[Unban Error] {e}")

        try:
            link = await bot.export_chat_invite_link(chat_id)
            await user.join_chat(link)
            await asyncio.sleep(3)

            if await is_assistant_in_chat(chat_id):
                return True

        except Exception as e:
            LOGGER.error(f"[Join After Unban Error] {e}")

        if m:
            await m.reply(sc(
                "Assistant could not join.\nPlease unban manually or add it."
            ))

        return False

    except (ChatAdminRequired, PeerIdInvalid):
        if m:
            await m.reply(
                sc(
                    "Assistant is not in the chat.\nGive invite permission or add manually."
                )
                + f"\n\n@{ASSISTANT_USERNAME}\n`{ASSISTANT_ID}`"
            )
        return False

    except Exception as e:
        LOGGER.error(f"[Assistant Join Error] {e}")

        if m:
            await m.reply(sc("Failed to bring assistant to the chat."))

        return False

    finally:
        JOINING.discard(chat_id)
