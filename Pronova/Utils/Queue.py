import asyncio
import time
import random
from collections import deque


class MusicQueue:
    def __init__(self):
        self.queues = {}
        self.history = {}
        self.start_time = {}
        self.votes = {}
        self.loop_count = {}
        self.locks = {}

    def _lock(self, chat_id):
        return self.locks.setdefault(chat_id, asyncio.Lock())

    def _queue(self, chat_id):
        return self.queues.setdefault(chat_id, deque())

    async def add(self, chat_id, song, priority=False):
        async with self._lock(chat_id):
            q = self._queue(chat_id)
            if priority:
                q.appendleft(song)
            else:
                q.append(song)
            return len(q)

    async def get_current(self, chat_id):
        q = self.queues.get(chat_id)
        return q[0] if q else None

    async def next(self, chat_id):
        async with self._lock(chat_id):
            q = self._queue(chat_id)
            if not q:
                return None

            current = q.popleft()
            self.history.setdefault(chat_id, deque(maxlen=20)).append(current)

            loop = self.loop_count.get(chat_id, 1)
            if loop > 1:
                self.loop_count[chat_id] -= 1
                q.appendleft(current)
                return current

            if not q:
                return None

            return q[0]

    async def skip(self, chat_id):
        return await self.next(chat_id)

    async def previous(self, chat_id):
        async with self._lock(chat_id):
            hist = self.history.get(chat_id)
            if not hist:
                return None

            last = hist.pop()
            self._queue(chat_id).appendleft(last)
            return last

    async def insert(self, chat_id, index, song):
        async with self._lock(chat_id):
            q = self._queue(chat_id)
            index = max(0, min(index, len(q)))
            q.insert(index, song)

    async def remove(self, chat_id, index):
        async with self._lock(chat_id):
            q = self._queue(chat_id)
            if 0 <= index < len(q):
                song = q[index]
                del q[index]
                return song
            return None

    async def move(self, chat_id, old, new):
        async with self._lock(chat_id):
            q = self._queue(chat_id)
            if 0 <= old < len(q) and 0 <= new <= len(q):
                song = q[old]
                del q[old]
                q.insert(new, song)

    async def shuffle(self, chat_id):
        async with self._lock(chat_id):
            q = list(self._queue(chat_id))
            if len(q) <= 1:
                return

            current = q[0]
            rest = q[1:]
            random.shuffle(rest)
            self.queues[chat_id] = deque([current] + rest)

    async def remove_by_user(self, chat_id, user_id):
        async with self._lock(chat_id):
            q = self._queue(chat_id)
            self.queues[chat_id] = deque(
                [s for s in q if s.get("requested_by", {}).get("id") != user_id]
            )

    async def clear(self, chat_id):
        async with self._lock(chat_id):
            self.queues.pop(chat_id, None)
            self.history.pop(chat_id, None)
            self.start_time.pop(chat_id, None)
            self.votes.pop(chat_id, None)
            self.loop_count.pop(chat_id, None)

    async def vote_skip(self, chat_id, user_id, total_members=1):
        async with self._lock(chat_id):
            voters = self.votes.setdefault(chat_id, set())
            voters.add(user_id)

            required = max(1, (total_members // 2) + 1)

            if len(voters) >= required:
                self.votes[chat_id] = set()
                return True

            return False

    def set_loop(self, chat_id, count: int):
        if count <= 1:
            self.loop_count.pop(chat_id, None)
            return 1

        self.loop_count[chat_id] = count
        return count

    def get_loop(self, chat_id):
        return self.loop_count.get(chat_id, 1)

    def clear_loop(self, chat_id):
        self.loop_count.pop(chat_id, None)

    def set_start(self, chat_id):
        self.start_time[chat_id] = time.time()

    def elapsed(self, chat_id):
        if chat_id not in self.start_time:
            return 0
        return int(time.time() - self.start_time[chat_id])

    def eta(self, chat_id):
        q = self.queues.get(chat_id)
        if not q:
            return 0

        total = 0

        for i, song in enumerate(q):
            try:
                dur = song.get("duration")

                if isinstance(dur, str) and ":" in dur:
                    m, s = map(int, dur.split(":"))
                    sec = m * 60 + s
                else:
                    sec = int(dur)
            except:
                sec = 0

            if i == 0:
                sec = max(sec - self.elapsed(chat_id), 0)

            total += max(sec, 0)

        return total

    def get_queue(self, chat_id):
        return list(self.queues.get(chat_id, []))

    def length(self, chat_id):
        return len(self.queues.get(chat_id, []))

    def snapshot(self, chat_id):
        return list(self.queues.get(chat_id, []))

    def restore(self, chat_id, data):
        self.queues[chat_id] = deque(data)

    def now_playing(self, chat_id):
        q = self.queues.get(chat_id)
        if not q:
            return None

        song = q[0]

        return {
            "title": song.get("title"),
            "duration": song.get("duration"),
            "elapsed": self.elapsed(chat_id),
            "requested_by": song.get("requested_by"),
            "loop": self.get_loop(chat_id)
        }


queue = MusicQueue()
