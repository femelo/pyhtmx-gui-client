from __future__ import annotations
from typing import Optional, Dict, Any
from pyhtmx import Div, Img
from pyhtmx_gui.kit import Page, SessionItem, Trigger


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
            _id="utterance",
            _class="text-white",
        )
        self.add_interaction(
            "status-data",
            SessionItem(
                parameter="utterance",
                attribute="inner_content",
                component=self._utterance,
            ),
        )
        self._spinner = Img(
            _id="spinner",
            src="default.svg",
            width="auto",
            height="auto",
        )
        self.add_interaction(
            "status-trigger",
            Trigger(
                event="spinner",
                attribute="src",
                component=self._spinner,
                get_value=self.get_spinner,
                target_level="outerHTML",
            )
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
            ]
        )

    def get_spinner(self: StatusBar, event: str) -> None:
        pass
