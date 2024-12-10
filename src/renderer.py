from __future__ import annotations
from typing import Union, Optional, List, Dict, Callable, Any
from secrets import token_hex
from enum import StrEnum
from pydantic import BaseModel, ConfigDict
from pyhtmx import Html, Div
from pyhtmx.html_tag import HTMLTag
from master import MASTER_DOCUMENT
from event_sender import EventSender, global_sender


class ContextType(StrEnum):
    LOCAL = "local"
    GLOBAL = "global"


class Callback(BaseModel):
    model_config = ConfigDict(
        strict=False,
        arbitrary_types_allowed=True,
        populate_by_name=False
    )
    context: ContextType
    event_name: str
    event_id: str
    fn: Callable
    source: HTMLTag
    target: Optional[HTMLTag] = None
    target_level: str = "innerHTML"


class SessionParameter(BaseModel):
    model_config = ConfigDict(
        strict=False,
        arbitrary_types_allowed=True,
        populate_by_name=False
    )
    parameter_name: str
    parameter_id: str
    target: HTMLTag


class Renderer:
    event_sender: EventSender = global_sender

    def __init__(self: Renderer):
        self._clients = []
        self._root: Div = Div(
            _id="root",
            _class="flex flex-col",
            hx_ext="sse",
            sse_connect="/updates",
            sse_swap="root",
        )
        self._master: Html = MASTER_DOCUMENT
        body, = self._master.find_elements_by_tag(tag="body")
        body.add_child(self._root)
        self._routes: List[str] = []
        self._pages: List[HTMLTag] = []
        self._global_callbacks: Dict[str, Callback] = {}
        self._local_callbacks: Dict[str, Callback] = {}
        self._session_parameters: Dict[str, Dict[str, SessionParameter]] = {}

    @property
    def document(self: Renderer) -> str:
        return self._master.to_string()

    def register_client(self: Renderer, client_id: str) -> None:
        self._clients.append(client_id)
        print(f"Number of clients in registry: {len(self._clients)}")

    def deregister(self: Renderer, client_id: str) -> None:
        self._clients.remove(client_id)
        print(f"Number of clients in registry: {len(self._clients)}")

    def register_session_parameter(
        self: Renderer,
        route: str,
        parameter: str,
        target: HTMLTag,
    ) -> None:
        # Set new id
        _id: str = token_hex(4)
        parameter_id = f"{parameter}-{_id}"
        target.update_attributes(
            attributes={
                "sse-swap": parameter_id,
            }
        )
        if route not in self._session_parameters:
            self._session_parameters[route] = {}
        self._session_parameters[route][parameter] = SessionParameter(
            parameter_name=parameter,
            parameter_id=parameter_id,
            target=target,
        )

    def register_callback(
        self: Renderer,
        context: Union[str, ContextType],
        event: str,
        fn: Callable,
        source: HTMLTag,
        target: Optional[HTMLTag] = None,
        target_level: str = "innerHTML",
    ) -> None:
        # Set root container if target was not specified
        target = target if target is not None else self._root
        # Set new id
        _id: str = token_hex(4)
        event_id = '-'.join([*event.split(), _id])
        if context == ContextType.LOCAL:
            # Add necessary attributes to elements for local action
            if "id" not in target.attributes:
                target_id = f"target-{_id}"
                target.update_attributes(
                    attributes={
                        "id": target_id,
                    }
                )
            source.update_attributes(
                attributes={
                    "hx-get": f"/events/{event_id}",
                    "hx-trigger": event,
                    "hx-target": target.attributes["id"],
                    "hx-swap": target_level,
                }
            )
            callback_mapping = self._local_callbacks
        elif context == ContextType.GLOBAL:
            # Add necessary attributes to elements for global action
            target.update_attributes(
                attributes={
                    "sse-swap": event_id,
                }
            )
            source.update_attributes(
                attributes={
                    "hx-post": f"/events/{event_id}",
                    "hx-trigger": event,
                    "hx-target": target.attributes["id"] if target is not None else "#root",
                    "hx-swap": "none",
                }
            )
            callback_mapping = self._global_callbacks
        else:
            print("Unknown context type. Callback not registered.")
            return
        # Register callback
        callback_mapping[event_id] = Callback(
            context=context,
            event_name=event,
            event_id=event_id,
            fn=fn,
            source=source,
            target=target,
            target_level=target_level,
        )

    def update_attributes(
        self: Renderer,
        route: str,
        parameter: str,
        attribute: Dict[str, Any],
    ) -> None:
        if route not in self._routes or route not in self._session_parameters:
            return
        if parameter not in self._session_parameters[route]:
            return
        session_parameter = self._session_parameters[route][parameter]
        for attr_name, attr_value in attribute.items():
            parameter_id = session_parameter.parameter_id
            component = session_parameter.target
            if attr_name == "inner_content":
                component.update_attributes(text_content=attr_value)
            else:
                component.update_attributes(attributes={attr_name: attr_value})
            self.update(attr_value, event_id=parameter_id)
            tag = component.tag
            # print(f"Updated parameter: {route}:{component} -> {parameter}")

    def close_component(
        self: Renderer,
        route: str,
        component: Any,
    ) -> None:
        if route != self._routes[-1]:
            return
        # Implement me

    def open_component(
        self: Renderer,
        route: str,
        component: HTMLTag,
    ) -> None:
        if route != self._routes[-1]:
            return
        # Implement me

    def show(
        self: Renderer,
        route: str,
        page: HTMLTag,
    ) -> None:
        if route in self._routes and route != self._routes[-1]:
            index = self._routes.index(page.route)
            # Move route
            route = self._routes.pop(index)
            self._routes.append(route)
            # Move root page
            _page = self._pages.pop(index)
            self._pages.append(_page)
        elif route not in self._routes:
            self._routes.append(route)
            self._pages.append(page)
            print(f"Page added to renderer: {route}.")
        else:
            print(f"Page already exists: {route}.")
            pass
        self.update_root()

    def close(self: Renderer) -> None:
        _ = self._routes.pop()
        _ = self._pages.pop()
        print(f"Removed last page from renderer.")
        self.update_root()

    def go_to(self: Renderer, route: str) -> None:
        if route not in self._routes:
            return
        index = self._routes.index(route)
        # Move route
        route = self._routes.pop(index)
        self._routes.append(route)
        # Move root page
        _page = self._pages.pop(index)
        self._pages.append(_page)
        # Move shown pages
        print(f"Routed to page: {route}.")
        self.update_root()

    def go_back(self: Renderer, level: int = -1) -> None:
        # Move route
        route = self._routes.pop(level - 1)
        self._routes.append(route)
        # Move root page
        _page = self._pages.pop(level - 1)
        self._pages.append(_page)
        print(f"Routed back to page: {route}.")
        self.update_root()

    def update_root(self: Renderer) -> None:
        _page = self._pages[-1]
        self._root.text = None
        self._root.add_child(_page)
        self.update(_page.to_string(), event_id="root")

    def update(
        self: Renderer,
        data: str,
        event_id: Optional[str] = None,
    ) -> None:
        # Don't send message without clients
        if not self._clients:
            return
        # Format SSE message
        msg: str = f"data: {data}\n\n"
        if event_id is not None:
            msg = f"event: {event_id}\n{msg}"
        self.event_sender.send(msg)

# Instantiate global renderer
global_renderer: Renderer = Renderer()
