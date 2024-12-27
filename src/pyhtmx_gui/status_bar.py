from __future__ import annotations
from typing import Optional, Dict, Any
from pyhtmx.html_tag import HTMLTag
from pyhtmx import Div
from pyhtmx_gui.kit import Page, SessionItem, Trigger
from .types import EventType


class StatusBar(Page):
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
            "Utterance should appear here.",
            _id="utterance",
            _class="text-xl text-white",
        )
        self.add_interaction(
            "utterance",
            SessionItem(
                parameter="status-utterance",
                attribute="inner_content",
                component=self._utterance,
            ),
        )
        self._spinner_style = {
            "visibility": "hidden",
            "padding": "16px",
            "margin-left": "auto",
            "width": "10vh",
            "height": "10vh",
        }
        self._spinner = HTMLTag(
            tag="lottie-player",
            _id="spinner",
            src="",
            background="transparent",
            style=self._spinner_style,
            loop="",
            autoplay="",
        )
        spinner_trigger = Trigger(
            event="status-spinner",
            attribute=("src", "style"),
            component=self._spinner,
            get_value={
                "src": self.get_spinner,
                "style": self.get_spinner_style,
            },
            target_level="outerHTML",
        )
        # Register the same trigger for the following OVOS events
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
                "items-center",
                "w-full",
                "h-[10vh]",
                "bg-transparent",
                "text-white",
                "px-[1vw]",
            ],
            style={
                "height": "10%",
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

    def get_spinner(self: StatusBar, ovos_event: str) -> None:
        if ovos_event == EventType.WAKEWORD:
            return "assets/animations/eye.json"
        elif ovos_event == EventType.RECORD_BEGIN:
            return "assets/animations/spinner.json"
        elif ovos_event == EventType.RECORD_END:
            return ""
        else:
            return ""

    def get_spinner_style(self: StatusBar, ovos_event: str) -> None:
        if ovos_event == EventType.WAKEWORD:
            self._spinner_style.update(
                {
                    "visibility": "visible",
                    "filter": (
                        "invert(43%) "
                        "sepia(64%) "
                        "saturate(1780%) "
                        "hue-rotate(162deg) "
                        "brightness(96%) "
                        "contrast(101%)"
                    ),
                },
            )
        elif ovos_event == EventType.RECORD_BEGIN:
            self._spinner_style.update(
                {
                    "visibility": "visible",
                    "filter": (
                        "invert(43%) "
                        "sepia(64%) "
                        "saturate(1780%) "
                        "hue-rotate(162deg) "
                        "brightness(96%) "
                        "contrast(101%)"
                    ),
                },
            )
        elif ovos_event == EventType.RECORD_END:
            _ = self._spinner_style.pop("filter", None)
            self._spinner_style.update(
                {
                    "visibility": "hidden",
                },
            )
        else:
            pass
        return self._spinner_style
