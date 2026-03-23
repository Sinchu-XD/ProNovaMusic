from pyrogram.enums import ChatMemberStatus
from Pronova.Database import is_sudo, is_auth, is_banned, is_gbanned
from Pronova.Utils.Font import sc
from Config import OWNER_ID


async def get_user_data(message=None, cq=None):
    if message:
        return message.from_user, message.chat.id
    if cq:
        return cq.from_user, cq.message.chat.id
    return None, None


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


async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
    except:
        return False


async def owner_only(client, message=None, cq=None):
    user, _ = await get_user_data(message, cq)

    if not user:
        return False

    return user.id == OWNER_ID


async def sudo_only(client, message=None, cq=None):
    user, _ = await get_user_data(message, cq)

    if not user:
        return False

    uid = user.id

    if uid == OWNER_ID:
        return True

    return await is_sudo(uid)


async def admin_only(client, message=None, cq=None):
    user, chat_id = await get_user_data(message, cq)

    if not user:
        return False

    uid = user.id

    if await is_gbanned(uid):
        return False

    if await is_banned(chat_id, uid):
        return False

    if uid == OWNER_ID:
        return True

    if await is_sudo(uid):
        return True

    if await is_admin(client, chat_id, uid):
        return True

    if await is_auth(chat_id, uid):
        return True

    return False
