from __future__ import annotations
from typing import Any, Callable, cast, Dict, List, Optional, Mapping, Union
from threading import Lock, Timer, Thread
from enum import Enum
import time
from queue import Queue
from .logger import logger
from .types import EventType, StatusUtterance
from .utils import calculate_duration, format_utterance, generate_split_utterance


class StatusEvent(str, Enum):
    SPEECH = "speech"
    UTTERANCE = "utterance"
    SPINNER = "spinner"


RESET_EVENT_MAP: Dict[StatusEvent, EventType] = {
    StatusEvent.SPEECH: EventType.SPEAK,
    StatusEvent.UTTERANCE: EventType.UTTERANCE,
    StatusEvent.SPINNER: EventType.UTTERANCE_END,
}

UNKNOWN_SKILL: str = "skill-ovos-fallback-unknown.openvoiceos"


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
            {status_event: StatusUtterance()}
            if status_event != StatusEvent.SPINNER
            else {}
        )
        self._handling_function: Callable = handling_function
        self._timeout: float = timeout
        self._timer_lock: Lock = Lock()
        self._timer: Optional[Timer] = None
        self._timestamp: float = 0.0
        self._queue: Queue = Queue(maxsize=100)
        self._close: bool = False
        self._thread: Thread = Thread(target=self.handle_events, daemon=True)
        self._thread.start()

    def __del__(self: StatusEventHandler) -> None:
        self._close = True
        self._thread.join()

    @property
    def timeout(self: StatusEventHandler) -> float:
        return self._timeout

    @property
    def elapsed_time(self: StatusEventHandler) -> float:
        return time.time() - self._timestamp

    def queue_event(
        self: StatusEventHandler,
        event_name: EventType,
        event_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        persistence: Optional[float] = None,
    ) -> None:
        self._queue.put((event_name, event_data, timeout, persistence))

    def handle_events(self: StatusEventHandler) -> None:
        while not self._close:
            try:
                event_name, event_data, timeout, persistence = self._queue.get(
                    block=False
                )
                self._handling_function(
                    ovos_event=event_name,
                    data=event_data,
                )
                if timeout:
                    self.reset_timer(timeout=timeout)
                if persistence:
                    time.sleep(persistence)
            except Exception:
                pass

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
            self._timestamp = time.time()
            self._timer.start()

    def reset_status(
        self: StatusEventHandler,
        timeout: Optional[float] = None,
    ) -> None:
        timeout = timeout or self._timeout
        with self._timer_lock:
            elapsed_time: float = self.elapsed_time
            if self._timestamp > 0 and elapsed_time > timeout:
                logger.info(
                    f"Resetting {self._status_event} after {elapsed_time:0.4f} seconds"
                )
                self._handling_function(
                    ovos_event=self._reset_event,
                    data=self._reset_data,
                )
                self._timestamp = 0.0
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
        utterance: Optional[Union[str, List[str]]] = event_data.get(
            "utterance", None
        ) or event_data.get("utterances", None)
        if utterance is not None and event_name not in (
            EventType.WAKEWORD,
            EventType.UTTERANCE,
            EventType.UTTERANCE_START,
        ):
            return
        duration: Optional[float] = event_data.get("duration", None) or event_data.get(
            "sound_duration", None
        )
        # Collect skill_id if any
        skill_id: Optional[str] = event_data.get("skill_id", None)
        # Collect exception if any
        exception: Optional[str] = event_data.get("exception", None)
        # Set status event type
        status_event: str = (
            StatusEvent.SPEECH
            if event_name == EventType.UTTERANCE_START
            else StatusEvent.UTTERANCE
        )
        persistence: float = 1.0 if event_name == EventType.UTTERANCE_START else 0.5

        # If utterance is present, queue the event as quick as possible
        data: Optional[Dict[str, Any]] = None
        if utterance:
            formatted_utterance = format_utterance(utterance)
            duration = duration or calculate_duration(formatted_utterance)
            for split_utterance, split_duration in generate_split_utterance(
                formatted_utterance, duration
            ):
                data: Optional[Dict[str, Any]] = {
                    status_event: StatusUtterance(
                        text=split_utterance,
                        duration=max(split_duration - 0.25, split_duration),
                    ),
                }
                persistence = split_duration

                self._handlers[status_event].queue_event(
                    event_name=event_name,
                    event_data=cast(Dict[str, Any], data),
                    timeout=self._handlers[status_event].timeout,
                    persistence=persistence,
                )
            if event_name != EventType.WAKEWORD:
                return

        # No utterance, check for other events
        if event_name in (
            EventType.WAKEWORD,
            EventType.SKILL_HANDLER_START,
            EventType.SKILL_HANDLER_COMPLETE,
            EventType.UTTERANCE_HANDLED,
            EventType.UTTERANCE_CANCELLED,
            EventType.AUDIO_OUTPUT_START,
            EventType.AUDIO_OUTPUT_END,
        ):
            # Verify if utterance is undetected
            if skill_id == UNKNOWN_SKILL or exception:
                event_name = EventType.UTTERANCE_UNDETECTED
            persistence = 0.0

        if event_name in (
            # EventType.WAKEWORD,
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
        elif event_name in (
            EventType.SKILL_HANDLER_START,
            EventType.AUDIO_OUTPUT_START,
        ):
            timeout = 60.0
        elif event_name == EventType.AUDIO_OUTPUT_END:
            timeout = 10.0
        elif event_name in (
            EventType.SKILL_HANDLER_COMPLETE,
            EventType.UTTERANCE_HANDLED,
        ):
            timeout = 8.0
        elif event_name == EventType.UTTERANCE_CANCELLED:
            timeout = 5.0
        if timeout:
            self._handlers[StatusEvent.SPINNER].reset_timer(timeout=timeout)
