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
            _class="text-2xl text-white font-bold italic",
        )
        self._utterance_style: HTMLTag = HTMLTag(
            tag="style",
            inner_content="""
                #utterance {
                    margin-left: 0px;
                    animation: slidein 2s;
                }
                @keyframes slidein {
                    0%   { margin-left: -500px; }
                    20%  { margin-left: -500px; }
                    35%  { margin-left: 0px; }
                    100% { margin-left: 0px; }
                }
            """
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
        spinner_style_tag = HTMLTag(
            tag="style",
            inner_content="""
                #spinner {
                    visibility: hidden;
                    opacity: 0;
                    padding: 16px;
                    margin-left: auto;
                    width: 15vh;
                    height: 15vh;
                    transition: opacity 0.5s ease-in-out, visibility 0s linear 0.5s;
                }
                #spinner.visible {
                    visibility: visible;
                    opacity: 1;
                    transition: opacity 1s ease-in-out, visibility 0s linear 0s;
                }
                #spinner.fade-out {
                    opacity: 0;
                    transition: opacity 0.5s ease-in-out, visibility 0s linear 0.5s;
                    visibility: hidden;
                }
            """
        )
        self._spinner = HTMLTag(
            tag="lottie-player",
            _id="spinner",
            src="assets/animations/spinner3.json",  # src wordt niet aangepast
            background="transparent",
            loop="",
            autoplay="",
        )
        spinner_trigger = Trigger(
            event="status-spinner",
            attribute=("class",),  # Alleen klasse wordt aangepast
            component=self._spinner,
            get_value={
                "class": self.get_spinner_class,  # Alleen de klasse wordt gewijzigd
            },
            target_level="outerHTML",
        )
        # Register dezelfde trigger voor de volgende OVOS events
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
                spinner_style_tag,
                self._utterance_style,
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

    def get_spinner(self: StatusBar, ovos_event: str) -> str:
        # src blijft altijd gelijk
        return "assets/animations/spinner2.json"

    def get_spinner_class(self: StatusBar, ovos_event: str) -> str:
        if ovos_event == EventType.WAKEWORD:
            return "visible"  # Activeer fade-in
        elif ovos_event == EventType.RECORD_END:
            return "fade-out"  # Activeer fade-out
        return ""
