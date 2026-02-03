from __future__ import annotations
from typing import Any, Optional, Dict
from pyhtmx import Div, Button  # type: ignore
from pyhtmx_gui.kit import Widget, SessionItem, Control, Page


class HelloWorldWidget(Widget):
    _parameters = ("title", "text")

    def __init__(
        self: HelloWorldWidget,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        session_data = session_data or {}
        super().__init__(
            name="hello-world-widget",
            session_data=session_data,
        )

        # Title
        self._title: Div = Div(
            inner_content=session_data.get("title"),
            _id="title",
            _class="text-[4vw] font-bold text-[currentColor]",
        )
        self.add_interaction(
            "title",
            SessionItem(
                parameter="title",
                attribute="inner_content",
                component=self._title,
            ),
        )

        # Page text
        self._page_text: Div = Div(
            "Page 2",
            _class="text-[3vw] font-bold text-[currentColor] italic",
        )

        # Text
        self._text: Div = Div(
            inner_content=session_data.get("text"),
            _id="text",
            _class="text-[3vw] font-bold text-[currentColor]",
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
                self._page_text,
                self._text,
                self._button,
            ],
            _id="hello-world-widget",
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


class HelloWorldPage2(Page):

    def __init__(
        self: HelloWorldPage2,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name="hello-world-page-2", session_data=session_data)

        hello_world = HelloWorldWidget(session_data=session_data)
        self.add_component(hello_world)

        # Add control to change to the next page
        self.add_interaction(
            "next-page-key-up",
            Control(
                context="global",
                event="keyup[event.code === 'ArrowRight'] from:body",
                callback=(
                    lambda renderer, _: renderer.show_next()
                ),
            ),
        )
        # Add control to change to the previous page
        self.add_interaction(
            "prev-page-key-up",
            Control(
                context="global",
                event="keyup[event.code === 'ArrowLeft'] from:body",
                callback=(
                    lambda renderer, _: renderer.show_previous()
                ),
            ),
        )

        # Create page element
        self._page: Div = Div(
            hello_world.widget,
            _id="hello-world-2",
            _class="flex flex-col bg-emerald-400 dark:bg-emerald-900",
            style={"width": "100vw", "height": "100vh"},
        )
