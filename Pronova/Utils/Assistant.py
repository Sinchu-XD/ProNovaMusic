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
        member = await user.get_chat_member(chat_id, ASSISTANT_ID)

        if member.status in (
            ChatMemberStatus.LEFT,
            ChatMemberStatus.BANNED
        ):
            return False

        return True

    except (UserNotParticipant, UserBannedInChannel, ChannelPrivate):
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

        for _ in range(2):
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
                LOGGER.error(f"[Join Attempt Error] {e}")

        if m:
            await m.reply(sc("Assistant failed to join the chat."))
        return False


    except (UserBannedInChannel, ChannelPrivate):
        try:
            bot_me = await bot.get_me()
            bot_member = await bot.get_chat_member(chat_id, bot_me.id)

            if not (bot_member.privileges and bot_member.privileges.can_restrict_members):
                if m:
                    await m.reply(sc("Bot does not have ban/unban rights."))
                return False

            try:
                member = await bot.get_chat_member(chat_id, ASSISTANT_ID)

                if member.status == ChatMemberStatus.BANNED:
                    await bot.unban_chat_member(chat_id, ASSISTANT_ID)
                    await asyncio.sleep(3)

            except Exception as e:
                LOGGER.error(f"[Unban Check Error] {e}")

            for _ in range(2):
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
                    "Assistant is banned or cannot join.\nPlease unban manually."
                ))

            return False

        except Exception as e:
            LOGGER.error(f"[Auto Unban Error] {e}")

            if m:
                await m.reply(sc(
                    "Auto unban failed.\nPlease unban assistant manually."
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
            await m.reply(sc("Assistant is banned or cannot join.\nPlease unban manually."))

        return False


    finally:
        JOINING.discard(chat_id)
