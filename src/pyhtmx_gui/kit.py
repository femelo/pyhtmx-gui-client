from __future__ import annotations
from typing import Any, Tuple, Dict, List, Iterable, Optional, Callable, Union
from enum import Enum
from pydantic import BaseModel, ConfigDict
from secrets import token_hex
from functools import partial
from pyhtmx.html_tag import HTMLTag
from .logger import logger


class Registrable(BaseModel):
    model_config = ConfigDict(
        strict=False,
        arbitrary_types_allowed=True,
        populate_by_name=False
    )
    _registered: bool = False

    @property
    def registered(self: Registrable) -> bool:
        return self._registered

    @registered.setter
    def registered(self: Registrable, value: bool) -> None:
        self._registered = value


class SessionItem(Registrable):
    parameter: str
    attribute: Union[str, Iterable[str]]
    component: HTMLTag
    format_value: Union[Callable, Dict[str, Callable], None] = None
    target_level: Optional[str] = "innerHTML"


class Trigger(Registrable):
    event: str
    attribute: Union[str, Iterable[str]]
    component: HTMLTag
    get_value: Union[Callable, Dict[str, Callable], None] = None
    target_level: Optional[str] = "innerHTML"


class Control(Registrable):
    context: str
    event: str
    callback: Callable
    source: HTMLTag
    target: Optional[HTMLTag] = None
    target_level: str = "innerHTML"


class WidgetType(str, Enum):
    PAGE = "page"
    COMPONENT = "component"
    DIALOG = "dialog"


class Widget:
    _parameters: Tuple[str] = ()

    def __init__(
        self: Widget,
        type: WidgetType = WidgetType.COMPONENT,
        name: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        self._type: WidgetType = type
        self._name: str = name or f"widget-{token_hex(4)}"
        self._session_data: Dict[str, Any] = (
            dict.fromkeys(self._parameters, '')
        )
        self._session_items: Dict[str, SessionItem] = {}
        self._triggers: Dict[str, Trigger] = {}
        self._controls: Dict[str, Control] = {}
        self._widget: Optional[HTMLTag] = None
        self.init_session_data(session_data)

    @property
    def id(self: Widget) -> str:
        return self._name

    @property
    def type(self: Widget) -> WidgetType:
        return self._type

    @property
    def widget(self: Widget) -> Optional[HTMLTag]:
        return self._widget

    @property
    def session_items(self: Widget) -> Dict[str, SessionItem]:
        return self._session_items

    @property
    def triggers(self: Widget) -> Dict[str, Trigger]:
        return self._triggers

    @property
    def controls(self: Widget) -> Dict[str, Control]:
        return self._controls

    def add_interaction(
        self: Widget,
        key: str,
        value: Union[SessionItem, Trigger, Control],
    ) -> None:
        if isinstance(value, SessionItem):
            self._session_items[key] = value
        elif isinstance(value, Trigger):
            self._triggers[key] = value
        elif isinstance(value, Control):
            self._controls[key] = value
        else:
            logger.error(
                "Invalid item: it must be a session item, "
                "a trigger or a control."
            )

    def has(self: Widget, parameter: str) -> bool:
        return parameter in self._session_items

    def acts_on(self: Widget, event: str) -> bool:
        return event in self._triggers

    def init_session_data(
        self: Widget,
        session_data: Optional[Dict[str, Any]]
    ) -> None:
        if session_data:
            self._session_data.update(
                {
                    k: v for k, v in session_data.items()
                    if k in self._session_data
                }
            )


class Page(Widget):
    _is_page: bool = True  # required class attribute for correct loading

    def __init__(
        self: Page,
        name: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            type=WidgetType.PAGE,
            name=name or f"page-{token_hex(4)}",
            session_data=session_data,
        )
        self._route: str = f"/{self.id}"
        self._widgets: List[Widget] = [self]
        self._page: HTMLTag = HTMLTag("div")

    @property
    def page(self: Page) -> HTMLTag:
        return self._page

    def propagate_session_data(
        self: Page,
    ) -> None:
        self._session_data.update(
            {
                k: v for widget in self._widgets
                for k, v in widget._session_data.items()
            }
        )

    def add_component(
        self: Page,
        widgets: Union[Widget, List[Widget]]
    ) -> None:
        if isinstance(widgets, Widget):
            self._widgets.append(widgets)
        elif isinstance(widgets, list):
            self._widgets.extend(widgets)
        else:
            logger.error(f"Invalid widgets format: {widgets}")

    def update_session_data(
        self: Page,
        session_data: Dict[str, Any],
        renderer: Any,
    ) -> None:
        for parameter, value in session_data.items():
            for widget in self._widgets:
                # Check whether the session parameter pertains to the widget
                if widget.has(parameter):
                    # If so, update the session data
                    widget._session_data[parameter] = value
                    # Collect session item
                    session_item = widget.session_items[parameter]
                    # Collect attributes to be updated
                    attr_names = session_item.attribute
                    formatters = session_item.format_value or {}
                    if isinstance(attr_names, str):
                        attr_names = [attr_names]
                        if isinstance(formatters, Callable):
                            formatters = dict.fromkeys(attr_names, formatters)
                    attributes = {}
                    for attr_name in attr_names:
                        attr_value = (
                            formatters[attr_name](value)
                            if attr_name in formatters else value
                        )
                        attributes[attr_name] = attr_value
                    # Update corresponding attributes
                    renderer.update_attributes(
                        route=self._route,
                        parameter=session_item.parameter,
                        attribute=attributes,
                    )

    def update_trigger_state(
        self: Page,
        triggered_event: str,
        renderer: Any,
    ) -> None:
        for widget in self._widgets:
            # Check whether the session parameter pertains to the widget
            if widget.acts_on(triggered_event):
                # And update the corresponding attribute
                trigger = widget.triggers[triggered_event]
                attr_name = trigger.attribute
                attr_value = trigger.get_value()
                renderer.update_attributes(
                    route=self._route,
                    parameter=trigger.event,
                    attribute={attr_name: attr_value},
                )
                # Collect attributes to be updated
                attr_names = trigger.attribute
                getters = trigger.get_value or {}
                if isinstance(attr_names, str):
                    attr_names = [attr_names]
                if isinstance(getters, Callable):
                    getters = dict.fromkeys(attr_names, getters)
                attributes = {}
                for attr_name in attr_names:
                    if attr_name in getters:
                        attr_value = getters[attr_name]()
                        attributes[attr_name] = attr_value
                # Update corresponding attributes
                renderer.update_attributes(
                    route=self._route,
                    parameter=trigger.event,
                    attribute=attributes,
                )

    def register_session_items(
        self: Page,
        widget: Widget,
        renderer: Any,
    ) -> None:
        # Register session parameters
        for session_item in widget.session_items.values():
            # Prevent objects from being registered twice
            if session_item.registered:
                continue
            renderer.register_session_parameter(
                route=self._route,
                parameter=session_item.parameter,
                target=session_item.component,
                target_level=session_item.target_level,
            )
            session_item.registered = True

    def register_triggers(
        self: Page,
        widget: Widget,
        renderer: Any,
    ) -> None:
        # Register triggers
        for trigger in widget.triggers.values():
            # Prevent objects from being registered twice
            if trigger.registered:
                continue
            renderer.register_session_parameter(
                route=self._route,
                parameter=trigger.parameter,
                target=trigger.component,
                target_level=trigger.target_level,
            )
            trigger.registered = True

    def register_callbacks(
        self: Page,
        widget: Widget,
        renderer: Any,
    ) -> None:
        # Register callbacks
        for control in widget.controls.values():
            # Prevent objects from being registered twice
            if control.registered:
                continue
            renderer.register_callback(
                context=control.context,
                event=control.event,
                fn=partial(control.callback, renderer),
                source=control.source,
                target=control.target,
                target_level=control.target_level,
            )
            control.registered = True

    def register_dialog(
        self: Page,
        widget: Widget,
        renderer: Any,
    ) -> None:
        if widget.type == WidgetType.DIALOG:
            renderer.register_dialog(
                dialog_id=widget.id,
                dialog_content=widget.widget,
            )

    def set_up(self: Page, renderer: Any) -> None:
        # Propagate session data from widgets
        self.propagate_session_data()
        for widget in self._widgets:
            # Register session parameters
            self.register_session_items(widget, renderer)
            # Register triggers
            self.register_triggers(widget, renderer)
            # Register callbacks
            self.register_callbacks(widget, renderer)
            # Register dialog
            self.register_dialog(widget, renderer)
