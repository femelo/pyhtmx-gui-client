from __future__ import annotations
from typing import Optional, Dict, Any
from pyhtmx.html_tag import HTMLTag
from pyhtmx import Div
from pyhtmx_gui.kit import Page, SessionItem, Trigger
from .types import EventType


class StatusBar(Page):
    _parameters = ("ovos_event", "utterance")
    _is_page = False

    def __init__(
        self: StatusBar,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            name="status",
            session_data=session_data
        )
        self._utterance = Div(
            _id="utterance",
            _class="text-2xl text-white font-['Roboto mono'] font-bold italic",
        )
        self.add_interaction(
            "utterance",
            SessionItem(
                parameter="status-utterance",
                attribute="inner_content",
                component=self._utterance,
                format_value=self.get_utterance,
            ),
        )
        self._spinner = HTMLTag(
            tag="lottie-player",
            _id="spinner",
            src="assets/animations/spinner2.json",
            background="transparent",
            loop="",
            autoplay="",
        )
        spinner_trigger = Trigger(
            event="status-spinner",
            attribute=("class", ),
            component=self._spinner,
            get_value={
                "class": self.get_spinner_class,
            },
            target_level="outerHTML",
        )
        for ovos_event in [
            EventType.WAKEWORD,
            EventType.RECORD_BEGIN,
            EventType.RECORD_END,
            EventType.UTTERANCE,
            EventType.UTTERANCE_HANDLED,
            EventType.UTTERANCE_CANCELLED,
        ]:
            self.add_interaction(
                ovos_event.value,
                spinner_trigger,
            )
        self._widget = Div(
            [
                self._utterance,
                self._spinner,
            ],
            _id="status-bar",
            _class=[
                "flex",
                "flex-row",
                "items-start",
                "w-full",
                # "h-[10vh]",
                "bg-transparent",
                "text-white",
                "px-[1vw]",
            ],
            style={
                "height": "15%",
                "width": "100%",
                "position": "fixed",
                "z-index": 1,
                "top": "0",
                "left": "0",
                "background-color": "rgba(0, 0, 0, 0)",
                "overflow-y": "hidden",
                "transition": "1.0s",
            },
        )

    def get_utterance(self: StatusBar, value: Any = None) -> str:
        utterance: str = self._session_data.get("utterance")
        return utterance[0].upper() + utterance[1:]

    def get_spinner_class(self: StatusBar, ovos_event: str) -> str:
        if ovos_event in (EventType.WAKEWORD, EventType.RECORD_BEGIN):
            return "visible"  # Activate fade-in
        elif ovos_event == EventType.RECORD_END:
            return "fade-out"  # Activate fade-out
