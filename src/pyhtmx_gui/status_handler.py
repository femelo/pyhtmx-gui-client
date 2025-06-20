from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Mapping, Union
from threading import Lock, Timer, Thread
from enum import Enum
import time
from queue import Queue
from .logger import logger
from .types import EventType
from .utils import format_utterance


class StatusEvent(str, Enum):
    SPEECH = "speech"
    UTTERANCE = "utterance"
    SPINNER = "spinner"


RESET_EVENT_MAP: Dict[StatusEvent, EventType] = {
    StatusEvent.SPEECH: EventType.SPEAK,
    StatusEvent.UTTERANCE: EventType.UTTERANCE,
    StatusEvent.SPINNER: EventType.UTTERANCE_END,
}


class StatusEventHandler:
    def __init__(
        self: StatusEventHandler,
        status_event: StatusEvent,
        handling_function: Callable,
        timeout: float = 10.0,
    ) -> None:
        self._status_event: StatusEvent = status_event
        self._reset_event: EventType = RESET_EVENT_MAP[status_event]
        self._reset_data: Optional[Dict[str, Any]] = (
            {status_event: ""} if status_event != StatusEvent.SPINNER else {})
        self._handling_function: Callable = handling_function
        self._timeout: float = timeout
        self._timer_lock: Lock = Lock()
        self._timer: Optional[Timer] = None
        self._timestamp: int = 0
        self._queue: Queue = Queue(maxsize=100)
        self._close: bool = False
        self._thread: Thread = Thread(target=self.handle_events, daemon=True)
        self._thread.start()

    def __del__(self: StatusEventHandler) -> None:
        self._close = True
        self._thread.join()

    @property
    def elapsed_time(self: StatusEventHandler) -> int:
        return time.time() - self._timestamp

    def queue_event(
        self: StatusEventHandler,
        event_name: EventType,
        event_data: Optional[Dict[str, Any]] = None,
        persistence: Optional[float] = None,
    ) -> None:
        self._queue.put((event_name, event_data, persistence))

    def handle_events(self: StatusEventHandler) -> None:
        while not self._close:
            try:
                event_name, event_data, persistence = self._queue.get(block=False)
                if persistence:
                    time.sleep(persistence)
                self._handling_function(
                    ovos_event=event_name,
                    data=event_data,
                )
            except:
                pass

    def update_timestamp(self: StatusEventHandler) -> None:
        self._timestamp = time.time()

    def reset_timer(
        self: StatusEventHandler,
        timeout: Optional[float] = None,
    ) -> None:
        timeout = timeout or self._timeout
        with self._timer_lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = Timer(
                timeout,
                self.reset_status,
                kwargs={"timeout": timeout},
            )
            self._timer.start()

    def cancel_timer(self: StatusEventHandler) -> None:
        with self._timer_lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = None


    def reset_status(
        self: StatusEventHandler,
        timeout: Optional[float] = None,
    ) -> None:
        timeout = timeout or self._timeout
        with self._timer_lock:
            elapsed_time: int = self.elapsed_time
            if self._timestamp > 0 and elapsed_time > timeout:
                logger.info(f"Resetting {self._status_event} after {elapsed_time} seconds")
                self._handling_function(
                    ovos_event=self._reset_event,
                    data=self._reset_data,
                )
                self._timestamp = 0
                self._timer = None


class StatusHandler:
    def __init__(
        self: StatusHandler,
        handling_function: Callable,
    ) -> None:
        self._handlers: Dict[StatusEvent, StatusEventHandler] = {
            StatusEvent.SPEECH: StatusEventHandler(
                StatusEvent.SPEECH,
                handling_function,
                timeout=5.0,
            ),
            StatusEvent.UTTERANCE: StatusEventHandler(
                StatusEvent.UTTERANCE,
                handling_function,
                timeout=5.0,
            ),
            StatusEvent.SPINNER: StatusEventHandler(
                StatusEvent.SPINNER,
                handling_function,
                timeout=20.0,
            ),
        }

    def process_event(
        self: StatusHandler,
        event_name: EventType,
        event_data: Mapping[str, Any],
    ) -> None:
        # Collect utterance if any
        utterance: Optional[Union[str, List[str]]] = \
            event_data.get("utterance", None) or event_data.get("utterances", None)
        # Collect skill_id if any
        skill_id: Optional[str] = event_data.get("skill_id", None)
        # Collect exception if any
        exception: Optional[str] = event_data.get("exception", None)
        # Set status event type
        status_event: str = StatusEvent.SPEECH if event_name == EventType.SPEAK else StatusEvent.UTTERANCE
        persistence: int = 0.0
        if utterance:
            self._handlers[status_event].update_timestamp()
            data = {status_event: format_utterance(utterance)}
        else:
            data = None

        # Set flags
        wakeword_detected: bool = event_name == EventType.WAKEWORD
        handler_started: bool = event_name == EventType.SKILL_HANDLER_START
        handler_completed: bool = event_name == EventType.SKILL_HANDLER_COMPLETE
        utterance_handled: bool = event_name == EventType.UTTERANCE_HANDLED
        utterance_cancelled: bool = event_name == EventType.UTTERANCE_CANCELLED
        audio_start: bool = event_name == EventType.AUDIO_OUTPUT_START
        audio_end: bool = event_name == EventType.AUDIO_OUTPUT_END

        # Update timestamp
        if (
            wakeword_detected or
            handler_started or
            handler_completed or
            utterance_handled or
            utterance_cancelled or
            audio_start or
            audio_end
        ):
            # Register timestamp to serve as reference after a timeout
            self._handlers[StatusEvent.SPINNER].update_timestamp()
            # Verify if utterance is undetected
            if skill_id == "skill-ovos-fallback-unknown.openvoiceos" or exception:
                event_name = EventType.UTTERANCE_UNDETECTED
            persistence = 0.0

        self._handlers[status_event].queue_event(
            event_name=event_name,
            event_data=data,
            persistence=persistence,
        )

        if utterance:
            self._handlers[status_event].reset_timer()

        # This timer reset postpones the spinner fade-out
        # based on the horizon expected for the next event
        # TODO: these transitions should be handled by a
        # state machine
        timeout: float = 0.0
        if wakeword_detected:
            timeout = 20.0
        elif handler_started or audio_start:
            timeout = 60.0
        elif audio_end:
            timeout = 10.0
        elif handler_completed or utterance_handled:
            timeout = 8.0
        elif utterance_cancelled:
            timeout = 5.0
        if timeout:
            self._handlers[StatusEvent.SPINNER].reset_timer(timeout=timeout)
