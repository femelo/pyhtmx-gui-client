from __future__ import annotations
from typing import Any, Tuple, Dict, List, Optional, Callable, Union
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
    attribute: Union[str, Tuple[str], List[str]]
    component: HTMLTag
    format_value: Union[Callable, Dict[str, Callable], None] = None
    target_level: Optional[str] = "innerHTML"


class Trigger(Registrable):
    event: str
    attribute: Union[str, Tuple[str], List[str]]
    component: HTMLTag
    get_value: Union[Callable, Dict[str, Callable], None] = None
    target_level: Optional[str] = "innerHTML"


class Control(Registrable):
    context: str
    event: str
    callback: Callable
    source: Union[HTMLTag, str, None] = None
    target: Union[HTMLTag, str, None] = None
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
        self._session_items: Dict[str, List[SessionItem]] = {}
        self._triggers: Dict[str, List[Trigger]] = {}
        self._controls: Dict[str, Control] = {}
        self._ghost_elements: List[HTMLTag] = []
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
    def ghost_elements(self: Widget) -> List[HTMLTag]:
        return self._ghost_elements

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
            # NOTE: this presetting/restructuring was added here to avoid them
            # during update execution. This simplifies the update method and is
            # likely better for performance.
            # Restructure session item for updates
            if isinstance(value.attribute, str):
                value.attribute = (value.attribute, )
            value.format_value = value.format_value or {}
            if isinstance(value.format_value, Callable):
                if len(value.attribute) > 1:
                    logger.warning(
                        "Single value formatter provided for "
                        "multiple attributes in session item. "
                        "All attributes will use the same formatter."
                    )
                value.format_value = dict.fromkeys(
                    value.attribute,
                    value.format_value,
                )
            if "attribute" in value.target_level:
                pass
            elif set(value.attribute) == {"inner_content"}:
                # Ensure innerHTML is targeted
                target_level = list(
                    filter(lambda e: "outerHTML" not in e, value.target_level.split())
                )
                if "innerHTML" not in value.target_level:
                    target_level.insert(0, "innerHTML")
                value.target_level = ' '.join([*target_level])
            else:
                # Ensure outerHTML is targeted
                target_level = list(
                    filter(lambda e: "innerHTML" not in e, value.target_level.split())
                )
                if "outerHTML" not in value.target_level:
                    target_level.insert(0, "outerHTML")
                value.target_level = ' '.join([*target_level])
            if key not in self._session_items:
                self._session_items[key] = []
            self._session_items[key].append(value)
        elif isinstance(value, Trigger):
            # NOTE: this presetting/restructuring was added here to avoid them
            # during update execution. This simplifies the update method and is
            # likely better for performance.
            # Restructure trigger for updates
            if isinstance(value.attribute, str):
                value.attribute = (value.attribute, )
            value.get_value = value.get_value or {}
            if isinstance(value.get_value, Callable):
                if len(value.attribute) > 1:
                    logger.warning(
                        "Single value getter provided for "
                        "multiple attributes in event trigger. "
                        "Only the first attribute will be set."
                    )
                value.get_value = {
                    value.attribute[0]: value.get_value
                }
            if "attribute" in value.target_level:
                pass
            elif set(value.attribute) == {"inner_content"}:
                # Ensure innerHTML is targeted
                target_level = list(
                    filter(lambda e: "outerHTML" not in e, value.target_level.split())
                )
                if "innerHTML" not in value.target_level:
                    target_level.insert(0, "innerHTML")
                value.target_level = ' '.join([*target_level])
            else:
                # Ensure outerHTML is targeted
                target_level = list(
                    filter(lambda e: "innerHTML" not in e, value.target_level.split())
                )
                if "outerHTML" not in value.target_level:
                    target_level.insert(0, "outerHTML")
                value.target_level = ' '.join([*target_level])
            if key not in self._triggers:
                self._triggers[key] = []
            self._triggers[key].append(value)
        elif isinstance(value, Control):
            if value.source is None:
                # Create a ghost element
                ghost_source: HTMLTag = HTMLTag(
                    "div",
                    _style={"display: none"},
                )
                self._ghost_elements.append(ghost_source)
                value.source = ghost_source
            self._controls[key] = value
        else:
            logger.error(
                "Invalid item: it must be a session item, "
                "a trigger or a control."
            )

    def has(self: Widget, parameter: str) -> bool:
        return parameter in self._session_items

    def acts_on(self: Widget, ovos_event: str) -> bool:
        return ovos_event in self._triggers

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


# TODO: create a generic class with methods for registering
# and setting up parameters so that widgets can be rendered
# without the need for a page
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
        self._namespace: str = f"{self.id}-ns"
        self._page_id: str = self.id
        self._route: str = f"/{self.id}"
        self._widgets: List[Widget] = [self]
        self._page: HTMLTag = HTMLTag("div")

    @property
    def namespace(self: Page) -> str:
        return self._namespace

    @property
    def page_id(self: Page) -> str:
        return self._page_id

    @property
    def route(self: Page) -> str:
        return self._route

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
                    # Get session item
                    for session_item in widget.session_items[parameter]:
                        # Collect attributes to be updated
                        attributes = {}
                        formatters = session_item.format_value
                        for attr_name in session_item.attribute:
                            attr_value = (
                                formatters[attr_name](value)
                                if attr_name in formatters else value
                            )
                            attributes[attr_name] = attr_value
                        # Update
                        renderer.update_attributes(
                            namespace=self.namespace,
                            page_id=self.page_id,
                            parameter=session_item.parameter,
                            attribute=attributes,
                        )

    def update_trigger_state(
        self: Page,
        ovos_event: str,
        renderer: Any,
    ) -> None:
        for widget in self._widgets:
            # Check whether the session parameter pertains to the widget
            if widget.acts_on(ovos_event):
                # Get trigger
                for trigger in widget.triggers[ovos_event]:
                    # Collect attributes to be updated
                    attributes = {}
                    getters = trigger.get_value
                    for attr_name in trigger.attribute:
                        if attr_name in getters:
                            attr_value = getters[attr_name](ovos_event)
                            attributes[attr_name] = attr_value
                    # Update
                    renderer.update_attributes(
                        namespace=self.namespace,
                        page_id=self.page_id,
                        parameter=trigger.event,
                        attribute=attributes,
                    )

    def include_ghost_elements(
        self: Page,
        widget: Widget,
    ) -> None:
        for element in widget.ghost_elements:
            self._page.insert_child(0, element)

    def register_session_items(
        self: Page,
        widget: Widget,
        page_manager: Any,
    ) -> None:
        # Register session parameters
        for session_group in widget.session_items.values():
            for session_item in session_group:
                # Prevent objects from being registered twice
                if session_item.registered:
                    continue
                page_manager.register_interaction_parameter(
                    parameter=session_item.parameter,
                    target=session_item.component,
                    target_level=session_item.target_level,
                )
                session_item.registered = True

    def register_triggers(
        self: Page,
        widget: Widget,
        page_manager: Any,
    ) -> None:
        # Register triggers
        for trigger_group in widget.triggers.values():
            for trigger in trigger_group:
                # Prevent objects from being registered twice
                if trigger.registered:
                    continue
                page_manager.register_interaction_parameter(
                    parameter=trigger.event,
                    target=trigger.component,
                    target_level=trigger.target_level,
                )
                trigger.registered = True

    def register_callbacks(
        self: Page,
        widget: Widget,
        page_manager: Any,
    ) -> None:
        # Register callbacks
        for control in widget.controls.values():
            # Prevent objects from being registered twice
            if control.registered:
                continue
            page_manager.register_callback(
                event=control.event,
                context=control.context,
                fn=partial(control.callback, page_manager),
                source=control.source,
                target=control.target,
                target_level=control.target_level,
            )
            control.registered = True

    def register_dialog(
        self: Page,
        widget: Widget,
        page_manager: Any,
    ) -> None:
        if widget.type == WidgetType.DIALOG:
            page_manager.register_dialog(
                dialog_id=widget.id,
                dialog_content=widget.widget,
            )

    def set_up(self: Page, page_manager: Any) -> Page:
        # Set namespace and page id
        self._namespace = page_manager.namespace
        self._page_id = page_manager.page_id
        # Propagate session data from widgets
        self.propagate_session_data()
        for widget in self._widgets:
            # Register ghost elements
            self.include_ghost_elements(widget)
            # Register session parameters
            self.register_session_items(widget, page_manager)
            # Register triggers
            self.register_triggers(widget, page_manager)
            # Register callbacks
            self.register_callbacks(widget, page_manager)
            # Register dialog
            self.register_dialog(widget, page_manager)
        return self
