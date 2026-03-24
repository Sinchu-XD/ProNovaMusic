from pyrogram import filters

from Pronova.Bot import bot
from Pronova.Utils.Font import sc

from Pronova.Utils.Allow import sudo_only, check_ban
from Pronova.Utils.Logger import LOGGER

from Pronova.Database import *


USER_CACHE = {}
CHAT_CACHE = {}


@bot.on_message(filters.command("stats"))
async def stats(client, m):

    LOGGER.info("Stats command triggered")

    if not m.from_user:
        LOGGER.warning("Stats: Message without user (ignored)")
        return

    user_id = m.from_user.id
    chat_id = m.chat.id

    LOGGER.info(f"Stats requested by user={user_id} in chat={chat_id}")

    if await check_ban(m):
        LOGGER.warning(f"Stats blocked (banned user): {user_id}")
        return

    if not await sudo_only(client, m):
        LOGGER.warning(f"Stats denied (not sudo): {user_id}")
        return

    msg = await m.reply(sc("fetching analytics..."))

    try:
        LOGGER.info("Fetching database stats...")

        users = await total_users()
        chats = await total_chats()
        songs = await get_lifetime("songs")
        commands = await get_lifetime("commands")

        banned = await total_banned()
        gbanned = await db.gbanned.count_documents({})

        weekly_users = await sum_range(7, "users")
        monthly_users = await sum_range(30, "users")

        tg = await top_groups(3)
        tu = await top_users(3)
        mp = await most_played(3)

        total_sudo = await db.sudo_users.count_documents({})
        total_auth = await db.auth_users.count_documents({})

        LOGGER.info("Database stats fetched successfully")

    except Exception as e:
        LOGGER.exception(f"Stats Fetch Error: {e}")
        return await msg.edit(sc("failed to fetch stats"))

    text = f"📊 {sc('bot analytics')}\n\n"

    text += f"{sc('users')} : {users}\n"
    text += f"{sc('chats')} : {chats}\n"
    text += f"{sc('songs')} : {songs}\n"
    text += f"{sc('commands')} : {commands}\n\n"

    text += f"{sc('sudo users')} : {total_sudo}\n"
    text += f"{sc('auth users')} : {total_auth}\n\n"

    text += f"{sc('banned (groups)')} : {banned}\n"
    text += f"{sc('gbanned (global)')} : {gbanned}\n\n"

    text += f"📈 {sc('growth')}\n"
    text += f"7 {sc('days')} : {weekly_users}\n"
    text += f"30 {sc('days')} : {monthly_users}\n\n"

    text += f"🏆 {sc('top groups')}\n"

    if tg:
        for i, (cid, s) in enumerate(tg, 1):
            try:
                cid = int(cid)

                if cid in CHAT_CACHE:
                    LOGGER.debug(f"Chat cache hit: {cid}")
                    name = CHAT_CACHE[cid]
                else:
                    LOGGER.debug(f"Chat cache miss: {cid}")
                    chat = await client.get_chat(cid)
                    name = chat.title
                    CHAT_CACHE[cid] = name

            except Exception as e:
                LOGGER.warning(f"Failed to fetch chat {cid}: {e}")
                name = cid

            text += f"{i}. {name} → {s}\n"
    else:
        LOGGER.info("No top groups data")
        text += f"{sc('no data')}\n"

    text += f"\n👤 {sc('top users')}\n"

    if tu:
        for i, (uid, c) in enumerate(tu, 1):
            try:
                uid = int(uid)

                if uid in USER_CACHE:
                    LOGGER.debug(f"User cache hit: {uid}")
                    mention = USER_CACHE[uid]
                else:
                    LOGGER.debug(f"User cache miss: {uid}")
                    user = await client.get_users(uid)
                    mention = user.mention
                    USER_CACHE[uid] = mention

            except Exception as e:
                LOGGER.warning(f"Failed to fetch user {uid}: {e}")
                mention = uid

            text += f"{i}. {mention} → {c}\n"
    else:
        LOGGER.info("No top users data")
        text += f"{sc('no data')}\n"

    text += f"\n🎧 {sc('most played')}\n"

    if mp:
        for i, (name, c) in enumerate(mp, 1):
            text += f"{i}. {name} → {c}\n"
    else:
        LOGGER.info("No most played data")
        text += f"{sc('no data')}\n"

    try:
        await msg.edit(text)
        LOGGER.info(f"Stats sent successfully to chat={chat_id}")

    except Exception as e:
        LOGGER.exception(f"Stats Edit Error: {e}")
