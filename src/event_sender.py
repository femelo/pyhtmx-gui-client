from __future__ import annotations
from queue import Queue, Full

class EventSender:
    def __init__(self: EventSender, max_size: int = 10):
        self._max_size: int = max_size
        self._listeners: list[Queue] = []

    def listen(self: EventSender) -> Queue:
        q = Queue(maxsize=self._max_size)
        self._listeners.append(q)
        return q

    def send(self: EventSender, msg: str) -> None:
        for listener in reversed(self._listeners):
            try:
                listener.put_nowait(msg)
            except Full:
                # Connection closed, remove listener
                self._listeners.remove(listener)

# Global event sender
global_sender: EventSender = EventSender()
