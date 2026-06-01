from pyrogram.enums import ChatMemberStatus
from Pronova.Database import is_sudo, is_auth, is_banned, is_gbanned
from Pronova.Utils.Font import sc
from Config import OWNER_ID
from Pronova.Utils.Logger import LOGGER


async def get_user_data(message=None, cq=None):
    if message:
        return message.from_user, message.chat.id, message
    if cq:
        return cq.from_user, cq.message.chat.id, cq.message
    return None, None, None


async def deny(m, text="not allowed"):
    try:
        await m.reply(sc(text))
    except Exception as e:
        LOGGER.error(f"Deny Error: {e}")


async def check_ban(message=None, cq=None):
    user, chat_id, m = await get_user_data(message, cq)

    if not user:
        return True

    uid = user.id

    try:
        if await is_gbanned(uid):
            LOGGER.warning(f"[GBANNED USER] {uid}")
            await deny(m, "you are gbanned")
            return True
    except Exception as e:
        LOGGER.error(f"[GBAN CHECK ERROR] {e}")

    try:
        if await is_banned(chat_id, uid):
            LOGGER.warning(f"[BANNED IN CHAT] {uid} in {chat_id}")
            await deny(m, "you are banned in this chat")
            return True
    except Exception as e:
        LOGGER.error(f"[BAN CHECK ERROR] {e}")

    return False


async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception as e:
        LOGGER.error(f"Admin Check Error: {e}")
        return False


async def owner_only(client, message=None, cq=None):
    if await check_ban(message, cq):
        return False

    user, _, m = await get_user_data(message, cq)

    if user and user.id == OWNER_ID:
        return True

    await deny(m, "only bot owner can use this")
    return False


async def sudo_only(client, message=None, cq=None):
    if await check_ban(message, cq):
        return False

    user, _, m = await get_user_data(message, cq)

    if not user:
        return False

    uid = user.id

    if uid == OWNER_ID or await is_sudo(uid):
        return True

    await deny(m, "only sudo users can use this")
    return False


async def admin_only(client, message=None, cq=None):
    if await check_ban(message, cq):
        return False

    user, chat_id, m = await get_user_data(message, cq)

    if not user:
        return False

    uid = user.id

    if uid == OWNER_ID:
        return True

    try:
        if await is_sudo(uid):
            return True
    except Exception:
        pass

    try:
        if await is_admin(client, chat_id, uid):
            return True
    except Exception:
        pass

    try:
        if await is_auth(chat_id, uid):
            return True
    except Exception:
        pass

    await deny(m, "only admins and authorized users can use this")
    return False
