import os
import asyncio
from traceback import format_exc

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity
from pyrogram import enums

from Pronova.Utils.thumbnail import get_thumb

import random
import re


def clean_html(text: str):
    return re.sub(r"<.*?>", "", text)


CUSTOM_EMOJI_IDS = [
    6089195853908548095,
    6334453153823459140,
    6334525760245597578,
    6334832949191509666,
    6334540251465254516,
    6334555537253860831,
    6332440708242212451,
    6097980951814475221,
    6334719188392740438,
    6269122341859495184,
    6271346172846149465,
    6271719066201755333,
    6217467341421154237,
    6237977283433338540,
    6235677650568878393,
    6113826782681502268,
    6116320024081731477
]


def utf16_len(text: str):
    return len(text.encode("utf-16-le")) // 2


def build_caption(title, url, duration, requester, header="Nᴏᴡ Pʟᴀʏɪɴɢ", position=None):
    title = (title or "Unknown")[:30]

    if isinstance(requester, dict):
        user_id = requester.get("id")
        name = clean_html(str(requester.get("first_name", "User")))
    else:
        user_id = None
        name = clean_html(str(requester))

    text = (
        f"▫ {header} ▫\n\n"
        f"▫ Tɪᴛʟᴇ : {title} ▫\n\n"
        f"▫ Dᴜʀᴀᴛɪᴏɴ : {duration} ▫\n\n"
        f"▫ Rᴇǫᴜᴇsᴛᴇᴅ Bʏ : {name} ▫"
    )

    if position:
        text += f"\n\n▫ Pᴏsɪᴛɪᴏɴ : {position} ▫"

    full = text
    entities = []

    for i, char in enumerate(full):
        if char == "▫":
            entities.append(
                MessageEntity(
                    type=enums.MessageEntityType.CUSTOM_EMOJI,
                    offset=utf16_len(full[:i]),
                    length=1,
                    custom_emoji_id=random.choice(CUSTOM_EMOJI_IDS)
                )
            )

    title_pos = full.find(title)
    if title_pos != -1 and url:
        entities.append(
            MessageEntity(
                type=enums.MessageEntityType.TEXT_LINK,
                offset=utf16_len(full[:title_pos]),
                length=utf16_len(title),
                url=url
            )
        )

    if user_id:
        name_pos = full.find(name)
        if name_pos != -1:
            entities.append(
                MessageEntity(
                    type=enums.MessageEntityType.TEXT_LINK,
                    offset=utf16_len(full[:name_pos]),
                    length=utf16_len(name),
                    url=f"tg://user?id={user_id}"
                )
            )

    return full, entities


QUEUE_DELETE_AFTER = 30
VC_END_DELETE_AFTER = 10


def control_buttons():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("▷", callback_data="vc_resume"),
        InlineKeyboardButton("II", callback_data="vc_pause"),
        InlineKeyboardButton("▢", callback_data="vc_end"),
        InlineKeyboardButton("‣‣I", callback_data="vc_skip"),
    ]])


class Plugin:
    name = "base"

    def __init__(self, app):
        self.app = app
        self.now_playing_msg = {}

    async def on_song_start(self, chat_id, song):
        caption, entities = build_caption(
            song.get("title"),
            song.get("url"),
            song.get("duration_text"),
            song.get("requested_by")
        )

        old = self.now_playing_msg.get(chat_id)

        if old:
            try:
                await old.delete()
            except:
                pass

        try:
            thumb = await get_thumb(
                title=song.get("title"),
                duration=song.get("duration_text"),
                thumbnail=song.get("thumb"),
                channel=song.get("channel", "YouTube"),
                views=song.get("views", "Unknown"),
                videoid="np"
            )

            msg = await self.app.send_photo(
                chat_id,
                photo=thumb,
                caption=caption,
                caption_entities=entities,
                reply_markup=control_buttons()
            )

            self.now_playing_msg[chat_id] = msg

        except Exception:
            print(format_exc())

    async def on_queue_add(self, chat_id, song, position):
        if position == 1:
            return

        caption, entities = build_caption(
            song.get("title"),
            song.get("url"),
            song.get("duration_text"),
            song.get("requested_by"),
            header="Aᴅᴅᴇᴅ Tᴏ Qᴜᴇᴜᴇ",
            position=position
        )

        try:
            thumb = await get_thumb(
                title=song.get("title"),
                duration=song.get("duration_text"),
                thumbnail=song.get("thumb"),
                videoid="queue"
            )

            msg = await self.app.send_photo(
                chat_id,
                photo=thumb,
                caption=caption,
                caption_entities=entities
            )

            asyncio.create_task(self._auto_delete(msg, QUEUE_DELETE_AFTER))

        except Exception:
            print(format_exc())

    async def on_seek(self, chat_id, song, seconds):

        msg = self.now_playing_msg.get(chat_id)
        if not msg:
            return

        direction = "Fᴏʀᴡᴀʀᴅᴇᴅ" if seconds > 0 else "Rᴇᴡɪɴᴅᴇᴅ"

        caption, entities = build_caption(
            song.title,
            song.url,
            song.duration_text,
            song.requested_by,
            header=f"{direction} {abs(seconds)}s\n\nNᴏᴡ Pʟᴀʏɪɴɢ"
        )

        try:
            await msg.delete()
        except:
            pass

        try:
            thumb = await get_thumb(
                title=song.title,
                duration=song.duration_text,
                thumbnail=song.thumb,
                videoid="seek"
            )

            new_msg = await self.app.send_photo(
                chat_id,
                photo=thumb,
                caption=caption,
                caption_entities=entities,
                reply_markup=control_buttons()
            )

            self.now_playing_msg[chat_id] = new_msg

        except Exception:
            print(format_exc())

    

    async def on_song_end(self, chat_id, song):
        msg = self.now_playing_msg.pop(chat_id, None)

        if msg:
            try:
                await msg.delete()
            except:
                pass

    async def on_vc_closed(self, chat_id):
        msg = self.now_playing_msg.pop(chat_id, None)

        if msg:
            try:
                await msg.delete()
            except:
                pass

        try:
            msg = await self.app.send_message(
                chat_id,
                "🔴 Vᴏɪᴄᴇ Cʜᴀᴛ Eɴᴅᴇᴅ\n\n🧹 Qᴜᴇᴜᴇ Cʟᴇᴀʀᴇᴅ & Pʟᴀʏᴇʀ Sᴛᴏᴘᴘᴇᴅ."
            )

            asyncio.create_task(self._auto_delete(msg, VC_END_DELETE_AFTER))

        except Exception:
            print(format_exc())

    async def _auto_delete(self, msg, delay):
        try:
            await asyncio.sleep(delay)
            await msg.delete()
        except:
            pass
