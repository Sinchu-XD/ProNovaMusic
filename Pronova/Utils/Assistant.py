import asyncio
from traceback import format_exc

from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import (
    ChatAdminRequired,
    UserAlreadyParticipant,
    PeerIdInvalid,
    UserBannedInChannel,
    UserNotParticipant,
    ChannelPrivate,
    ChannelInvalid,
    InviteHashExpired,
    InviteHashInvalid,
    FloodWait,
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

        try:
            me = await user.get_me()
            ASSISTANT_ID = me.id
            ASSISTANT_USERNAME = me.username
            LOGGER.info(f"[ASSISTANT] Setup complete: {ASSISTANT_ID}")
        except Exception:
            LOGGER.error(f"[ASSISTANT SETUP ERROR]\n{format_exc()}")


async def is_assistant_in_chat(chat_id: int) -> bool:
    """Check if the assistant userbot is a member of the chat."""
    try:
        member = await user.get_chat_member(chat_id, ASSISTANT_ID)
        return member.status not in (
            ChatMemberStatus.LEFT,
            ChatMemberStatus.BANNED,
        )
    except (UserNotParticipant, UserBannedInChannel, ChannelPrivate, ChannelInvalid):
        return False
    except FloodWait as e:
        await asyncio.sleep(e.value + 1)
        return False
    except Exception as e:
        # Don't log CHANNEL_INVALID as an error – it just means not joined yet
        if "CHANNEL_INVALID" not in str(e):
            LOGGER.error(f"[Assistant Check Error] {e}")
        return False


async def _try_join_with_link(chat_id: int, link: str) -> bool:
    """Attempt to join via invite link; return True on success."""
    try:
        await user.join_chat(link)
        await asyncio.sleep(2)
        return True
    except UserAlreadyParticipant:
        return True
    except (InviteHashExpired, InviteHashInvalid):
        LOGGER.warning(f"[JOIN] Invite link expired for {chat_id}, trying add_chat_members")
        return False
    except Exception as e:
        LOGGER.error(f"[JOIN] link join failed for {chat_id}: {e}")
        return False


async def _try_add_directly(chat_id: int) -> bool:
    """Have the bot add the assistant directly (requires add-members permission)."""
    try:
        await bot.add_chat_members(chat_id, ASSISTANT_ID)
        await asyncio.sleep(2)
        return True
    except UserAlreadyParticipant:
        return True
    except Exception as e:
        LOGGER.error(f"[JOIN] Direct add failed for {chat_id}: {e}")
        return False


async def get_ass(chat_id, m=None):
    global ASSISTANT_ID, ASSISTANT_USERNAME

    if not ASSISTANT_ID:
        await setup_assistant()

    if not ASSISTANT_ID:
        LOGGER.error("[ASSISTANT] Not initialized — cannot join chat")
        return False

    # Resolve and validate the chat
    try:
        chat = await bot.get_chat(chat_id)

        if chat.type not in (ChatType.SUPERGROUP, ChatType.CHANNEL):
            if m:
                try:
                    await m.reply("❌ This command only works in supergroups/channels.")
                except Exception:
                    pass
            return False

        # Use the resolved numeric ID (important for CHANNEL_INVALID fix)
        chat_id = chat.id

    except Exception as e:
        LOGGER.error(f"[Chat Validation Error] {e}")
        return False

    # Already in chat?
    if await is_assistant_in_chat(chat_id):
        return True

    # Prevent duplicate concurrent join attempts
    if chat_id in JOINING:
        return False

    JOINING.add(chat_id)

    try:
        # Check bot privileges
        bot_me = await bot.get_me()

        try:
            bot_member = await bot.get_chat_member(chat_id, bot_me.id)
        except ChatAdminRequired:
            if m:
                try:
                    await m.reply("⚠️ Bot must be an admin with invite permission.")
                except Exception:
                    pass
            return False

        can_invite = bool(
            bot_member.privileges and bot_member.privileges.can_invite_users
        )
        can_restrict = bool(
            bot_member.privileges and bot_member.privileges.can_restrict_members
        )

        if not can_invite:
            if m:
                try:
                    await m.reply("⚠️ Bot needs **Invite Users** admin permission.")
                except Exception:
                    pass
            return False

        # ── Strategy 1: add directly (most reliable, no link expiry) ──────
        if await _try_add_directly(chat_id):
            if await is_assistant_in_chat(chat_id):
                return True

        # ── Strategy 2: export a fresh invite link and join ────────────────
        try:
            link = await bot.create_chat_invite_link(chat_id, member_limit=1)
            joined = await _try_join_with_link(chat_id, link.invite_link)
        except Exception as e:
            LOGGER.warning(f"[JOIN] create_chat_invite_link failed: {e}")
            joined = False

        if not joined:
            # Fallback: try the permanent invite link
            try:
                perm_link = await bot.export_chat_invite_link(chat_id)
                joined = await _try_join_with_link(chat_id, perm_link)
            except Exception as e:
                LOGGER.warning(f"[JOIN] export_chat_invite_link fallback failed: {e}")

        if await is_assistant_in_chat(chat_id):
            return True

        # ── Strategy 3: unban then retry (if banned) ──────────────────────
        if can_restrict:
            try:
                await bot.unban_chat_member(chat_id, ASSISTANT_ID)
                await asyncio.sleep(1)
            except Exception as e:
                LOGGER.warning(f"[Unban Error] {e}")

            if await _try_add_directly(chat_id):
                if await is_assistant_in_chat(chat_id):
                    return True

        # All strategies failed
        if m:
            username = f"@{ASSISTANT_USERNAME}" if ASSISTANT_USERNAME else f"`{ASSISTANT_ID}`"
            try:
                await m.reply(
                    f"❌ **Assistant could not join this chat.**\n\n"
                    f"Please add the assistant manually:\n{username}\n`{ASSISTANT_ID}`"
                )
            except Exception:
                pass

        return False

    except (ChatAdminRequired, PeerIdInvalid):
        if m:
            username = f"@{ASSISTANT_USERNAME}" if ASSISTANT_USERNAME else f"`{ASSISTANT_ID}`"
            try:
                await m.reply(
                    sc("Assistant is not in the chat.\nGive invite permission or add manually.")
                    + f"\n\n{username}\n`{ASSISTANT_ID}`"
                )
            except Exception:
                pass
        return False

    except Exception as e:
        LOGGER.error(f"[Assistant Join Error] {e}")
        if m:
            try:
                await m.reply(sc("❌ Failed to bring assistant."))
            except Exception:
                pass
        return False

    finally:
        JOINING.discard(chat_id)
