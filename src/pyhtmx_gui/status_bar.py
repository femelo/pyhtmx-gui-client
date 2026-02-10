from __future__ import annotations
from typing import Any, Dict, List, Optional
from functools import partial
from pyhtmx.html_tag import HTMLTag
from pyhtmx import Div
from pyhtmx_gui.kit import Page, SessionItem, Trigger
from .types import EventType, StatusUtterance
from .utils import calculate_duration, calculate_text_width


BG_CIRCLE = HTMLTag(
    tag="circle",
    fill="currentColor",
    cx="75",
    cy="75",
    r="50",
    _class="bg-circle",
)

PULSE_CIRCLE = HTMLTag(
    tag="circle",
    fill="currentColor",
    cx="75",
    cy="75",
    r="75",
    _class="pulse-circle",
)

DOTS: List[HTMLTag] = [
    HTMLTag(
        tag="circle",
        cx=str(15 * i + 5 + 25),
        cy="75",
        r="4",
        _class=f"spinner-dot dot-{i}",
    )
    for i in range(1, 6)
]


SPINNER: HTMLTag = HTMLTag(
    tag="svg",
    inner_content=[  # type: ignore
        PULSE_CIRCLE,
        BG_CIRCLE,
        HTMLTag(
            tag="g",
            inner_content=DOTS,  # type: ignore
            fill="white",
            _class="dots",
        )
    ],
    version="1.1",
    id="L1",
    xmlns="http://www.w3.org/2000/svg",
    xmlns_xlink="http://www.w3.org/1999/xlink",
    x="0px",
    y="0px",
    viewBox="0 0 150 150",
    enable_background="new 0 0 150 150",
    xml_space="preserve",
)


class StatusBar(Page):
    _parameters = ("ovos_event", "utterance", "speech")
    _is_page = False

    def __init__(
        self: StatusBar,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            name="status",
            session_data=session_data
        )
        self._speech = Div(
            _id="speech",
            _class=self.get_speech_class(),
        )
        self.add_interaction(
            "speech",
            SessionItem(
                parameter="status-speech",
                attribute=("inner_content", "class"),
                component=self._speech,
                format_value={
                    "inner_content": partial(
                        self.get_speech_or_utterance,
                        key="speech",
                    ),
                    "class": self.get_speech_class,
                },
                target_level="outerHTML",
            ),
        )
        self._utterance = Div(
            _id="utterance",
            _class=self.get_utterance_class(),
        )
        self.add_interaction(
            "utterance",
            SessionItem(
                parameter="status-utterance",
                attribute=("inner_content", "class"),
                component=self._utterance,
                format_value={
                    "inner_content": partial(
                        self.get_speech_or_utterance,
                        key="utterance",
                    ),
                    "class": self.get_utterance_class,
                },
                target_level="outerHTML",
            ),
        )
        self._spinner = Div(
            inner_content=SPINNER,
            _id="spinner",
            _class="fade-out",
        )
        spinner_trigger = Trigger(
            event="status-spinner",
            attribute=("class", ),
            component=self._spinner,
            get_value={
                "class": self.get_spinner_class,
            },
            target_level="attribute:class",
        )
        for ovos_event in [
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
        ]:
            self.add_interaction(
                ovos_event.value,
                spinner_trigger,
            )
        self._widget = Div(
            [
                Div(
                    [self._utterance, self._speech],
                    _class="flex flex-col grow w-[84%]",
                ),
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
                "height": "25%",
                "width": "100%",
                "position": "fixed",
                "z-index": 1000,
                "top": "0",
                "left": "0",
                "background-color": "rgba(0, 0, 0, 0)",
                "overflow-y": "hidden",
                "pointer-events": "none",
            },
        )

    def get_speech_or_utterance(
        self: StatusBar,
        value: Any = None,
        key: str = "utterance",
    ) -> str:
        text: str = self._session_data.get(key, StatusUtterance()).text
        return text or ""

    def get_speech_class(
        self: StatusBar,
        value: Any = None,
    ) -> list[str]:
        font_size: int = 32
        guard: str = ''
        _class: list[str] = [
            f"text-[{font_size}px]",
            "text-white",
            "font-normal",
            "border-0",
        ]
        value = value or StatusUtterance()
        text: str = value.text
        duration: Optional[float] = value.duration
        if text:
            text += guard
            if duration is None:
                duration = calculate_duration(text)
            width = calculate_text_width(
                text or "",
                font_name="VT323-Regular.ttf",
                font_size=font_size,
            ) + 8
            _class.extend(
                [
                    f"speech-period-{duration:0.2f}",
                    f"w-[{width}px]",
                    "border-r-8",
                ]
            )
        else:
            _class.extend(["no-text", "w-[0px]", "border-r-0"])
        return _class

    def get_utterance_class(
        self: StatusBar,
        value: Any = None,
    ) -> list[str]:
        font_size: int = 24
        guard: str = ' '
        _class: list[str] = [
            f"text-[{font_size}px]",
            "text-white",
            "font-medium",
            "border-0",
        ]
        value = value or StatusUtterance()
        text: str = value.text
        duration: Optional[float] = value.duration
        if text:
            text += guard
            if duration is None:
                duration = calculate_duration(text)
            width = calculate_text_width(
                text or "",
                font_name="Inter-Regular.woff2",
                font_size=font_size,
            ) + 8
            _class.extend(
                [
                    f"utterance-period-{duration:0.2f}",
                    f"w-[{width}px]",
                    "border-r-8",
                ]
            )
        else:
            _class.extend(["no-text", "w-[0px]", "border-r-0"])
        return _class

    def get_spinner_class(self: StatusBar, ovos_event: str) -> Optional[str]:
        if ovos_event in (EventType.WAKEWORD, EventType.SKILL_HANDLER_START):
            return "visible"  # Activate fade-in
        elif ovos_event in (EventType.UTTERANCE_HANDLED, ):
            return "success"  # Activate success
        elif ovos_event in (EventType.UTTERANCE_CANCELLED, ):
            return "cancelled"
        elif ovos_event in (EventType.UTTERANCE_UNDETECTED, EventType.INTENT_FAILURE):
            return "failure"  # Activate failure
        elif ovos_event in (EventType.UTTERANCE_END, ):
            return "fade-out"  # Activate fade-out
        else:
            return None
