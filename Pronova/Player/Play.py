import time

from Pronova.Utils.Queue import SongQueue


class Player:
    def __init__(self, engine):
        self.engine = engine
        self.queues = {}
        self.start_time = {}

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
            return 0

    async def play(self, chat_id, song, video: bool = False):
        try:
            q = self._queue(chat_id)
            pos = q.add(song)

            if pos == 1:
                try:
                    await self.engine.play(
                        chat_id,
                        song.stream,
                        video=song.is_video
                    )

                    self.start_time[chat_id] = time.time()
                    song.position = 0

                except Exception:
                    q.pop_last()
                    self.start_time.pop(chat_id, None)
                    raise

            return pos

        except Exception:
            raise

    async def seek(self, chat_id, seconds: int):
        try:
            q = self.queues.get(chat_id)

            if not q or not q.current():
                return False

            song = q.current()

            current_elapsed = self.current_time(chat_id)
            new_time = max(current_elapsed + seconds, 0)

            duration = getattr(song, "duration_sec", 0)

            if duration > 0 and new_time >= duration:
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
            return False

    async def skip(self, chat_id):
        try:
            q = self.queues.get(chat_id)

            if not q:
                return None

            current = q.current()

            if current:
                if getattr(current, "loop_left", 0) > 0:
                    current.loop_left -= 1
                    return await self._restart_current(chat_id)

                if getattr(q, "infinite_loop", False):
                    return await self._restart_current(chat_id)

            nxt = q.next()

            if not nxt:
                self.start_time.pop(chat_id, None)

                try:
                    await self.engine.stop(chat_id)
                except Exception:
                    pass

                return None

            await self.engine.play(
                chat_id,
                nxt.stream,
                video=nxt.is_video
            )

            self.start_time[chat_id] = time.time()
            nxt.position = 0

            return nxt

        except Exception:
            return None

    async def _restart_current(self, chat_id):
        try:
            q = self.queues.get(chat_id)

            if not q or not q.current():
                return None

            song = q.current()

            await self.engine.play(
                chat_id,
                song.stream,
                video=song.is_video
            )

            self.start_time[chat_id] = time.time()
            song.position = 0

            return song

        except Exception:
            return None

    async def previous(self, chat_id):
        try:
            q = self.queues.get(chat_id)

            if not q:
                return None

            prev = q.previous()

            if not prev:
                return None

            await self.engine.play(
                chat_id,
                prev.stream,
                video=prev.is_video
            )

            self.start_time[chat_id] = time.time()
            prev.position = 0

            return prev

        except Exception:
            return None

    async def stop(self, chat_id):
        try:
            if chat_id in self.queues:
                self.queues[chat_id].clear()

            self.start_time.pop(chat_id, None)

            await self.engine.stop(chat_id)

        except Exception:
            pass

    async def pause(self, chat_id):
        await self.engine.pause(chat_id)

    async def resume(self, chat_id):
        await self.engine.resume(chat_id)

    async def mute(self, chat_id):
        await self.engine.mute(chat_id)

    async def unmute(self, chat_id):
        await self.engine.unmute(chat_id)

    async def volume(self, chat_id, volume: int):
        volume = max(0, min(volume, 200))
        await self.engine.change_volume(chat_id, volume)

    def set_loop(self, chat_id, count=None):
        q = self._queue(chat_id)

        if count is None:
            q.infinite_loop = not q.infinite_loop
            return q.infinite_loop

        if count <= 0:
            return 0

        cur = q.current()

        if cur:
            cur.loop_left = max(count - 1, 0)
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
            return None
