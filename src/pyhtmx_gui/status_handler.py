from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Mapping, Union
from threading import Lock, Timer, Thread
from enum import Enum
import time
from math import exp, log
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
        self._is_handling: bool = False

    def __del__(self: StatusEventHandler) -> None:
        self._close = True
        self._thread.join()

    @property
    def elapsed_time(self: StatusEventHandler) -> int:
        return time.time() - self._timestamp

    @property
    def is_handling(self: StatusEventHandler) -> bool:
        return self._is_handling

    @is_handling.setter
    def is_handling(self: StatusEventHandler, value: bool) -> None:
        self._is_handling = value

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
                self._is_handling = False


class StatusHandler:
    def __init__(
        self: StatusHandler,
        handling_function: Callable,
    ) -> None:
        self._handlers: Dict[StatusEvent, StatusEventHandler] = {
            StatusEvent.SPEECH: StatusEventHandler(
                StatusEvent.SPEECH,
                handling_function,
                timeout=6.0,
            ),
            StatusEvent.UTTERANCE: StatusEventHandler(
                StatusEvent.UTTERANCE,
                handling_function,
                timeout=6.0,
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
        persistence: float = 0.3


        # If utterance is present, queue the event as quick as possible
        if utterance:
            self._handlers[status_event].update_timestamp()
            formatted_utterance: str = format_utterance(utterance)
            data = {status_event: formatted_utterance}
            if not self._handlers[status_event].is_handling:
                self._handlers[status_event].is_handling = True
            else:
                persistence = 1.0 + 1.5 * (
                    1.0 - exp(log(0.75) * len(formatted_utterance) / 10)
                )

            self._handlers[status_event].queue_event(
                event_name=event_name,
                event_data=data,
                persistence=persistence,
            )
            self._handlers[status_event].reset_timer()
            return

        # No utterance, check for other events
        data = None

        # Update timestamp
        if event_name in (
            EventType.WAKEWORD,
            EventType.SKILL_HANDLER_START,
            EventType.SKILL_HANDLER_COMPLETE,
            EventType.UTTERANCE_HANDLED,
            EventType.UTTERANCE_CANCELLED,
            EventType.AUDIO_OUTPUT_START,
            EventType.AUDIO_OUTPUT_END,
        ):
            # Register timestamp to serve as reference after a timeout
            self._handlers[StatusEvent.SPINNER].update_timestamp()
            # Verify if utterance is undetected
            if skill_id == "skill-ovos-fallback-unknown.openvoiceos" or exception:
                event_name = EventType.UTTERANCE_UNDETECTED
            persistence = 0.0

        if event_name in (
            EventType.WAKEWORD,
            # EventType.RECORD_BEGIN,
            # EventType.RECORD_END,
            # EventType.UTTERANCE,
            EventType.SKILL_HANDLER_START,
            # EventType.SKILL_HANDLER_COMPLETE,
            EventType.UTTERANCE_HANDLED,
            EventType.UTTERANCE_CANCELLED,
            EventType.UTTERANCE_UNDETECTED,
            EventType.INTENT_FAILURE,
            EventType.UTTERANCE_END,
            # EventType.AUDIO_OUTPUT_START,
            # EventType.AUDIO_OUTPUT_END,
        ):
            self._handlers[status_event].queue_event(
                event_name=event_name,
                event_data=data,
                persistence=persistence,
            )

        # This timer reset postpones the spinner fade-out
        # based on the horizon expected for the next event
        # TODO: these transitions should be handled by a
        # state machine
        timeout: float = 0.0
        if event_name == EventType.WAKEWORD:
            timeout = 20.0
        elif event_name in (EventType.SKILL_HANDLER_START, EventType.AUDIO_OUTPUT_START):
            timeout = 60.0
        elif event_name == EventType.AUDIO_OUTPUT_END:
            timeout = 10.0
        elif event_name in (EventType.SKILL_HANDLER_COMPLETE, EventType.UTTERANCE_HANDLED):
            timeout = 8.0
        elif event_name == EventType.UTTERANCE_CANCELLED:
            timeout = 5.0
        if timeout:
            self._handlers[StatusEvent.SPINNER].reset_timer(timeout=timeout)
