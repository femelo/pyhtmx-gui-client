from __future__ import annotations
from typing import Any, Optional, Dict, List, Tuple, Callable
from functools import partial
from pyhtmx.html_tag import HTMLTag
from pyhtmx import Div, Button


# TODO: move this to 'types.py'
class SessionData:
    def __init__(
        self: SessionData,
        parameter: str,
        attribute: str,
        component: HTMLTag,
        format_value: Optional[Callable] = None,
        target_level: Optional[str] = "innerHTML",
    ):
        self.parameter = parameter
        self.attribute = attribute
        self.component = component
        self.format_value = format_value
        self.target_level = target_level


class Control:
    def __init__(
        self: Control,
        context: str,
        event: str,
        callback: Callable,
        source: HTMLTag,
        target: Optional[HTMLTag] = None,
        target_level: str = "innerHTML",
    ):
        self.context = context
        self.event = event
        self.callback = callback
        self.source = source
        self.target = target
        self.target_level = target_level


class Widget:
    _parameters: Tuple[str] = ()

    def __init__(
        self: Widget,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        self._session_data: Dict[str, Any] = {
            parameter: '' for parameter in self._parameters
        }
        self._session_objects: Dict[str, Optional[SessionData]] = {
            parameter: None for parameter in self._parameters
        }
        self._controls: Dict[str, Optional[Control]] = {}
        self._widget: Optional[HTMLTag] = None
        self.init_session_data(session_data)

    @property
    def widget(self: Widget) -> Optional[HTMLTag]:
        return self._widget

    @property
    def session_objects(self: Widget) -> Dict[str, Optional[SessionData]]:
        return self._session_objects

    @property
    def controls(self: Widget) -> Dict[str, Optional[Control]]:
        return self._controls

    def has(self: Widget, parameter: str) -> bool:
        return parameter in self._parameters

    def init_session_data(self: Widget, session_data: Optional[Dict[str, Any]]) -> None:
        if session_data:
            self._session_data.update(
                {
                    k: v for k, v in session_data.items()
                    if k in self._session_data
                }
            )


class HelloWorldWidget(Widget):
    _parameters = ("title", "text")

    def __init__(
        self: HelloWorldWidget,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(session_data=session_data)

        # Title
        self._title: Div = Div(
            inner_content=session_data.get("title"),
            _id="title",
            _class="text-[4vw] font-bold",
        )
        self._session_objects["title"] = SessionData(
            parameter="title",
            attribute="inner_content",
            component=self._title,
        )
        # Text
        self._text: Div = Div(
            inner_content=session_data.get("text"),
            _id="text",
            _class="text-[2vw] font-bold",
        )
        self._session_objects["text"] = SessionData(
            parameter="text",
            attribute="inner_content",
            component=self._text,
        )
        # Button
        self._button: Button = Button(
            "Back to Home",
            _id="btn-close",
            _class="btn btn-outline btn-info btn-lg"  # daisyUI classes
        )
        self._controls["btn-close-click"] = Control(
            context="global",
            event="click",
            callback=lambda renderer: renderer.close(),  # will close the window
            source=self._button,
            target=None, # to target the root (to close the page)
            target_level="innerHTML",
        )
        # Main container
        self._widget: Div = Div(
            [
                self._title,
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
                "bg-white",
            ],
        )


class HelloWorldPage:
    _is_page: bool = True

    def __init__(
        self: HelloWorldPage,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        self._route: str = "/hello-world"

        hello_world = HelloWorldWidget(session_data=session_data)
        self._widgets: List[Widget] = [hello_world]

        self._session_data: Dict[str, Any] = {
            k: v for widget in self._widgets
            for k, v in widget._session_data.items()
        }

        self._page: Div = Div(
            hello_world.widget,
            _id="hello-world",
            _class="flex flex-col",
            style={"width": "100vw", "height": "100vh"},
        )

    @property
    def page(self: HelloWorldPage) -> HTMLTag:
        return self._page

    def update_session_data(
        self: HelloWorldPage,
        session_data: Dict[str, Any],
        renderer: Any
    ) -> None:
        for parameter, value in session_data.items():
            for widget in self._widgets:
                if widget.has(parameter):
                    widget._session_data[parameter] = value
                    session_object = widget.session_objects[parameter]
                    attr_name = session_object.attribute
                    attr_value = (
                        session_object.format_value(value)
                        if session_object.format_value else value
                    )
                    renderer.update_attributes(
                        route=self._route,
                        parameter=session_object.parameter,
                        attribute={attr_name: attr_value},
                    )

    def set_up(self: HelloWorldPage, renderer: Any) -> None:
        for widget in self._widgets:
            # Register session parameters
            registered = []
            for parameter, session_object in widget.session_objects.items():
                # Prevent objects from being registered twice
                if id(session_object) in registered:
                    continue
                renderer.register_session_parameter(
                    route=self._route,
                    parameter=session_object.parameter,
                    target=session_object.component,
                    target_level=session_object.target_level,
                )
                registered.append(id(session_object))
            # Register callbacks
            registered = []
            for _, control in widget.controls.items():
                # Prevent objects from being registered twice
                if id(control) in registered:
                    continue
                renderer.register_callback(
                    context=control.context,
                    event=control.event,
                    fn=partial(control.callback, renderer),
                    source=control.source,
                    target=control.target,
                    target_level=control.target_level,
                )
                registered.append(id(session_object))
