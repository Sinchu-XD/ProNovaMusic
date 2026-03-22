import asyncio

from AbhiCalls.yt import resolve_query
from AbhiCalls.models import Song
from AbhiCalls.player import Player
from AbhiCalls.settings import settings


class VoiceController:
    def __init__(self, engine, cookies: str | None = None):
        self.cookies = cookies or settings.cookies
        self.engine = engine
        self.player = Player(engine)

        self.engine.on_end = self._on_end
        self.engine.on_vc_closed = self._on_vc_closed

        self.plugins = []
        self._ending = set()

    def load_plugin(self, plugin):
        self.plugins.append(plugin)

    async def _hook(self, name, *args):
        for p in self.plugins:
            fn = getattr(p, name, None)

            if not fn:
                continue

            try:
                if asyncio.iscoroutinefunction(fn):
                    await fn(*args)
                else:
                    fn(*args)
            except Exception:
                pass

    async def play(self, chat_id, query, requested_by, video: bool = False):
        try:
            results = await resolve_query(query, self.cookies, video=video)
        except Exception:
            return False, "Resolver failed"

        if not results:
            return None, "No results found"

        first_pos = None
        last_song = None

        for data in results:
            song = Song(
                title=data.get("title"),
                url=data.get("url"),
                duration=data.get("duration"),
                views=data.get("views"),
                stream=data.get("stream"),
                requested_by=requested_by,
                thumb=data.get("thumb"),
                is_video=data.get("is_video", False),
                channel=data.get("channel")
            )

            try:
                pos = await self.player.play(chat_id, song, video=song.is_video)
            except Exception:
                return False, "Player error"

            await self._hook("on_queue_add", chat_id, song, pos)

            if first_pos is None:
                first_pos = pos

            last_song = song

        if first_pos == 1 and last_song:
            await asyncio.sleep(0.8)
            await self._hook("on_song_start", chat_id, last_song)

        return last_song, first_pos

    async def play_file(
        self,
        chat_id,
        file_path,
        requested_by,
        reply=None,
        video: bool = False
    ):
        duration = 0

        if reply:
            if getattr(reply, "voice", None) and reply.voice.duration:
                duration = reply.voice.duration
            elif getattr(reply, "audio", None) and reply.audio.duration:
                duration = reply.audio.duration
            elif getattr(reply, "video", None) and reply.video.duration:
                duration = reply.video.duration

        try:
            duration = int(duration)
        except Exception:
            duration = 0

        song = Song(
            title="Telegram Media",
            url=None,
            duration=duration,
            views=None,
            stream=file_path,
            requested_by=requested_by,
            thumb=None,
            is_video=video,
            channel="telegram"
        )

        try:
            pos = await self.player.play(chat_id, song, video=song.is_video)
        except Exception:
            return False, "Player error"

        await self._hook("on_queue_add", chat_id, song, pos)

        if pos == 1:
            await asyncio.sleep(0.8)
            await self._hook("on_song_start", chat_id, song)

        return song, pos

    async def seek(self, chat_id, seconds: int):
        result = await self.player.seek(chat_id, seconds)

        if result:
            q = self.player.queues.get(chat_id)

            if q and q.current():
                await self._hook("on_seek", chat_id, q.current(), seconds)

        return result

    async def skip(self, chat_id):
        return await self.player.skip(chat_id)

    async def previous(self, chat_id):
        return await self.player.previous(chat_id)

    async def pause(self, chat_id):
        await self.player.pause(chat_id)

    async def resume(self, chat_id):
        await self.player.resume(chat_id)

    async def stop(self, chat_id):
        await self.player.stop(chat_id)

    async def mute(self, chat_id):
        await self.player.mute(chat_id)

    async def unmute(self, chat_id):
        await self.player.unmute(chat_id)

    async def volume(self, chat_id, volume: int):
        await self.player.volume(chat_id, volume)

    def loop(self, chat_id, count=None):
        return self.player.set_loop(chat_id, count)

    def eta(self, chat_id):
        return self.player.eta(chat_id)

    async def _on_end(self, chat_id):
        if chat_id in self._ending:
            return

        self._ending.add(chat_id)

        try:
            q = self.player.queues.get(chat_id)
            old_song = q.current() if q else None

            if old_song:
                await self._hook("on_song_end", chat_id, old_song)

            try:
                next_song = await self.player.skip(chat_id)
            except Exception:
                return

            if next_song:
                await asyncio.sleep(0.8)
                await self._hook("on_song_start", chat_id, next_song)
            else:
                await self._on_vc_closed(chat_id)

        finally:
            self._ending.discard(chat_id)

    async def _on_vc_closed(self, chat_id):
        try:
            await self.player.stop(chat_id)
        except Exception:
            pass

        await self._hook("on_vc_closed", chat_id)
