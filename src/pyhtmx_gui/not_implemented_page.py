from __future__ import annotations
from typing import Any, Optional, Dict
from pyhtmx import Div, Strong, Button  # type: ignore
from pyhtmx_gui.kit import Widget, SessionItem, Control, Page


class NotImplementedWidget(Widget):
    _parameters = ("namespace", )

    def __init__(
        self: NotImplementedWidget,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        session_data = session_data or {}
        super().__init__(
            name="not-implemented-widget",
            session_data=session_data,
        )

        # Title
        self._title: Div = Div(
            inner_content="Not Implemented",
            _id="title",
            _class="text-[4vw] font-bold text-[currentColor] mt-[20vh]",
        )
        self.add_interaction(
            "title",
            SessionItem(
                parameter="title",
                attribute="inner_content",
                component=self._title,
            ),
        )

        # Text
        self._text: Div = Div(
            inner_content=[
                "Page for",
                Strong(session_data.get("namespace")),
                "not received."
            ],
            _id="text",
            _class="text-[3vw] text-[currentColor] mt-[5vh] mb-[5vh]",
        )
        self.add_interaction(
            "text",
            SessionItem(
                parameter="text",
                attribute="inner_content",
                component=self._text,
            ),
        )

        # Button
        self._button: Button = Button(
            "Back to Home",
            _id="btn-close",
            _class="btn btn-outline btn-lg"  # daisyUI classes
        )
        self.add_interaction(
            "btn-close-click",
            Control(
                context="global",
                event="click",
                # will close the window
                callback=lambda renderer, _: renderer.close(),
                source=self._button,
                target=None,  # no target
                target_level="innerHTML",
            ),
        )

        # Main container
        self._widget: Div = Div(
            [
                self._title,
                self._text,
                self._button,
            ],
            _id="not-implemented-widget",
            _class=[
                "p-[1vw]",
                "flex",
                "grow",
                "flex-col",
                "justify-start",
                "items-center",
                "bg-transparent",
            ],
        )


class NotImplementedPage(Page):

    def __init__(
        self: NotImplementedPage,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name="not-implemented-page", session_data=session_data)

        widget = NotImplementedWidget(session_data=session_data)
        self.add_component(widget)

        # Create page element
        self._page: Div = Div(
            widget.widget,
            _id="not-implemented-page",
            _class="flex flex-col bg-blue-400 dark:bg-blue-900 fade-in",
            style={"width": "100vw", "height": "100vh"},
        )
