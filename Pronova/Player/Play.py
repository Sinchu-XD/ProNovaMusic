import time
from traceback import format_exc

from Pronova.Utils.Queue import SongQueue
from Pronova.Utils.Logger import LOGGER

#LOGGER.setLevel("ERROR")

class Player:
    def __init__(self, engine):
        self.engine = engine
        self.queues = {}
        self.start_time = {}

        LOGGER.info("Player initialized")

    def _queue(self, chat_id):
        return self.queues.setdefault(chat_id, SongQueue())

    def current_time(self, chat_id):
        try:
            start = self.start_time.get(chat_id)

            if not start:
                return 0

            elapsed = max(int(time.time() - start), 0)

            q = self.queues.get(chat_id)

            if q and q.current():
                q.current().position = elapsed

            return elapsed

        except Exception:
            LOGGER.error(f"[TIME ERROR]\n{format_exc()}")
            return 0

    async def play(self, chat_id, song, video: bool = False):
        LOGGER.info(f"[PLAY REQUEST] {song.title} in {chat_id}")

        try:
            q = self._queue(chat_id)
            pos = q.add(song)

            LOGGER.info(f"[QUEUE ADD] {song.title} at {pos}")

            if pos == 1:
                try:
                    LOGGER.info(f"[START STREAM] {song.title}")

                    await self.engine.play(
                        chat_id,
                        song.stream,
                        video=song.is_video
                    )

                    self.start_time[chat_id] = time.time()
                    song.position = 0

                except Exception:
                    LOGGER.error(f"[PLAY ENGINE ERROR] {song.title}\n{format_exc()}")
                    q.pop_last()
                    self.start_time.pop(chat_id, None)
                    raise

            return pos

        except Exception:
            LOGGER.error(f"[PLAY ERROR]\n{format_exc()}")
            raise

    async def seek(self, chat_id, seconds: int):
        LOGGER.info(f"[SEEK] Chat: {chat_id} | Seconds: {seconds}")

        try:
            q = self.queues.get(chat_id)

            if not q or not q.current():
                LOGGER.warning("[SEEK FAILED] No current song")
                return False

            song = q.current()

            current_elapsed = self.current_time(chat_id)
            new_time = max(current_elapsed + seconds, 0)

            duration = getattr(song, "duration_sec", 0)

            if duration > 0 and new_time >= duration:
                LOGGER.warning("[SEEK FAILED] Exceeds duration")
                return False

            await self.engine.play(
                chat_id,
                song.stream,
                start_time=new_time,
                video=song.is_video
            )

            self.start_time[chat_id] = time.time() - new_time
            song.position = new_time

            return True

        except Exception:
            LOGGER.error(f"[SEEK ERROR]\n{format_exc()}")
            return False

    async def skip(self, chat_id):
        LOGGER.info(f"[SKIP CALLED] Chat: {chat_id}")

        try:
            q = self.queues.get(chat_id)

            if not q:
                LOGGER.warning("[SKIP FAILED] No queue")
                return None

            current = q.current()

            if current:
                if getattr(current, "loop_left", 0) > 0:
                    current.loop_left -= 1
                    LOGGER.info("[LOOP CONTINUE]")
                    return await self._restart_current(chat_id)

                if getattr(q, "infinite_loop", False):
                    LOGGER.info("[INFINITE LOOP]")
                    return await self._restart_current(chat_id)

            nxt = q.next()

            LOGGER.info(f"[NEXT SONG] {nxt.title if nxt else 'None'}")

            if not nxt:
                LOGGER.warning("[QUEUE EMPTY - STOPPING VC]")

                self.start_time.pop(chat_id, None)

                try:
                    await self.engine.stop(chat_id)
                except Exception:
                    LOGGER.error(f"[STOP ERROR]\n{format_exc()}")

                return None

            await self.engine.play(
                chat_id,
                nxt.stream,
                video=nxt.is_video
            )

            self.start_time[chat_id] = time.time()
            nxt.position = 0

            LOGGER.info(f"[PLAYING NEXT] {nxt.title}")

            return nxt

        except Exception:
            LOGGER.error(f"[SKIP ERROR]\n{format_exc()}")
            return None

    async def _restart_current(self, chat_id):
        try:
            q = self.queues.get(chat_id)

            if not q or not q.current():
                return None

            song = q.current()

            LOGGER.info(f"[RESTART SONG] {song.title}")

            await self.engine.play(
                chat_id,
                song.stream,
                video=song.is_video
            )

            self.start_time[chat_id] = time.time()
            song.position = 0

            return song

        except Exception:
            LOGGER.error(f"[RESTART ERROR]\n{format_exc()}")
            return None

    async def previous(self, chat_id):
        LOGGER.info(f"[PREVIOUS] Chat: {chat_id}")

        try:
            q = self.queues.get(chat_id)

            if not q:
                return None

            prev = q.previous()

            if not prev:
                LOGGER.warning("[NO PREVIOUS SONG]")
                return None

            await self.engine.play(
                chat_id,
                prev.stream,
                video=prev.is_video
            )

            self.start_time[chat_id] = time.time()
            prev.position = 0

            LOGGER.info(f"[PLAYING PREVIOUS] {prev.title}")

            return prev

        except Exception:
            LOGGER.error(f"[PREVIOUS ERROR]\n{format_exc()}")
            return None

    async def stop(self, chat_id):
        LOGGER.warning(f"[STOP PLAYER] Chat: {chat_id}")

        try:
            if chat_id in self.queues:
                self.queues[chat_id].clear()

            self.start_time.pop(chat_id, None)

            await self.engine.stop(chat_id)

        except Exception:
            LOGGER.error(f"[STOP ERROR]\n{format_exc()}")

    async def pause(self, chat_id):
        LOGGER.info(f"[PAUSE] {chat_id}")
        await self.engine.pause(chat_id)

    async def resume(self, chat_id):
        LOGGER.info(f"[RESUME] {chat_id}")
        await self.engine.resume(chat_id)

    async def mute(self, chat_id):
        LOGGER.info(f"[MUTE] {chat_id}")
        await self.engine.mute(chat_id)

    async def unmute(self, chat_id):
        LOGGER.info(f"[UNMUTE] {chat_id}")
        await self.engine.unmute(chat_id)

    async def volume(self, chat_id, volume: int):
        volume = max(0, min(volume, 200))
        LOGGER.info(f"[VOLUME] {chat_id} -> {volume}")
        await self.engine.change_volume(chat_id, volume)

    def set_loop(self, chat_id, count=None):
        q = self._queue(chat_id)

        if count is None:
            q.infinite_loop = not q.infinite_loop
            LOGGER.info(f"[TOGGLE LOOP] {q.infinite_loop}")
            return q.infinite_loop

        if count <= 0:
            return 0

        cur = q.current()

        if cur:
            cur.loop_left = max(count - 1, 0)
            LOGGER.info(f"[SET LOOP COUNT] {count}")
            return count

        return 0

    def eta(self, chat_id):
        try:
            q = self.queues.get(chat_id)

            if not q or not q.current():
                return None

            elapsed = self.current_time(chat_id)
            dur = getattr(q.current(), "duration_sec", 0)

            if dur <= 0:
                return None

            return max(dur - elapsed, 0)

        except Exception:
            LOGGER.error(f"[ETA ERROR]\n{format_exc()}")
            return None
