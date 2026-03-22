from collections import deque
import random


class SongQueue:
    def __init__(self):
        self.items = []
        self.history = deque(maxlen=20)
        self.infinite_loop = False

    def add(self, song):
        try:
            self.items.append(song)
            return len(self.items)
        except Exception:
            return None

    def pop_last(self):
        try:
            if not self.items:
                return None

            return self.items.pop()

        except Exception:
            return None

    def current(self):
        try:
            if not self.items:
                return None
            return self.items[0]
        except Exception:
            return None

    def next(self):
        try:
            if not self.items:
                return None

            current = self.items[0]
            self.history.appendleft(current)

            if getattr(current, "loop_left", 0) > 0:
                current.loop_left -= 1
                return current

            if self.infinite_loop:
                return current

            self.items.pop(0)
            return self.current()

        except Exception:
            return None

    def previous(self):
        try:
            if not self.history:
                return None

            prev = self.history.popleft()
            self.items.insert(0, prev)
            return prev

        except Exception:
            return None

    def shuffle(self):
        try:
            if len(self.items) <= 1:
                return False

            current = self.items.pop(0)
            random.shuffle(self.items)
            self.items.insert(0, current)

            return True

        except Exception:
            return False

    def clear(self):
        try:
            self.items.clear()
            self.history.clear()
            self.infinite_loop = False
        except Exception:
            pass
