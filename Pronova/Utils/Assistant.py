import asyncio

from pyrogram.errors import (
    ChatAdminRequired,
    UserAlreadyParticipant,
    PeerIdInvalid,
    UserBannedInChannel
)

from Pronova.Bot import bot, user
#from Bot.Helper.Font import sc


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

    
        if member.status == "kicked":
            return False

        return True

    except UserBannedInChannel:
        return False

    except Exception as e:
        print(f"[Assistant Check Error] {e}")
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

        link = await bot.export_chat_invite_link(chat_id)

        try:
            await user.join_chat(link)
            await asyncio.sleep(2)
        except UserAlreadyParticipant:
            return True

        return await is_assistant_in_chat(chat_id)

    except UserBannedInChannel:
        try:
            bot_me = await bot.get_me()
            bot_member = await bot.get_chat_member(chat_id, bot_me.id)

            if bot_member.privileges and bot_member.privileges.can_restrict_members:
                await bot.unban_chat_member(chat_id, ASSISTANT_ID)
                await asyncio.sleep(1)

                try:
                    link = await bot.export_chat_invite_link(chat_id)
                    await user.join_chat(link)
                    await asyncio.sleep(2)

                    return await is_assistant_in_chat(chat_id)

                except Exception as e:
                    print(f"[Rejoin Error] {e}")

            if m:
                await m.reply(
                    sc(
                        "assistant was banned and auto unban failed\n"
                        "please unban manually"
                    )
                )
            return False

        except Exception as e:
            print(f"[Auto Unban Error] {e}")

            if m:
                await m.reply(sc("assistant is banned, please unban manually"))
            return False

    except (ChatAdminRequired, PeerIdInvalid):
        if m:
            await m.reply(
                sc(
                    "assistant not in group\n"
                    "give invite permission or add manually"
                )
                + f"\n\n@{ASSISTANT_USERNAME}\n`{ASSISTANT_ID}`"
            )
        return False

    except Exception as e:
        print(f"[Assistant Join Error] {e}")
        if m:
            await m.reply(sc("failed to bring assistant"))
        return False

    finally:
        JOINING.discard(chat_id)
