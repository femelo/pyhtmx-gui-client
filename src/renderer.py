from __future__ import annotations
from typing import Union, Optional, List, Dict, Callable, Any
from secrets import token_hex
from copy import deepcopy
from enum import Enum
from pydantic import BaseModel, ConfigDict
from pyhtmx import Html, Div, Dialog
from pyhtmx.html_tag import HTMLTag
from logger import logger
from master import MASTER_DOCUMENT
from event_sender import EventSender, global_sender


class ContextType(str, Enum):
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
            # hx_ext="sse",
            # sse_connect="/updates",
            sse_swap="root",
        )
        self._dialog_root: Dialog = Dialog(
            _id="dialog",
            _class="modal",
            # hx_ext="sse",
            # sse_connect="/updates",
            sse_swap="dialog",
            hx_swap="outerHTML",
        )
        self._master: Html = MASTER_DOCUMENT
        body, = self._master.find_elements_by_tag(tag="body")
        body.add_child(self._root)
        body.add_child(self._dialog_root)
        self._routes: List[str] = []
        self._pages: List[HTMLTag] = []
        self._dialogs: Dict[str, HTMLTag] = {}
        self._global_callbacks: Dict[str, Callback] = {}
        self._local_callbacks: Dict[str, Callback] = {}
        self._session_parameters: \
            Dict[str, Dict[str, List[SessionParameter]]] = {}

    @property
    def document(self: Renderer) -> Html:
        return self._master

    def register_client(self: Renderer, client_id: str) -> None:
        if client_id not in self._clients:
            self._clients.append(client_id)
        logger.info(f"Number of clients in registry: {len(self._clients)}")

    def deregister(self: Renderer, client_id: str) -> None:
        if client_id in self._clients:
            self._clients.remove(client_id)
        logger.info(f"Number of clients in registry: {len(self._clients)}")

    def register_session_parameter(
        self: Renderer,
        route: str,
        parameter: str,
        target: HTMLTag,
        target_level: Optional[str] = "innerHTML",
    ) -> None:
        # Set new id
        _id: str = token_hex(4)
        parameter_id = f"{parameter}-{_id}"
        target.update_attributes(
            attributes={
                "sse-swap": parameter_id,
                "hx-swap": target_level,
            }
        )
        if route not in self._session_parameters:
            self._session_parameters[route] = {}
        if parameter not in self._session_parameters[route]:
            self._session_parameters[route][parameter] = []
        self._session_parameters[route][parameter].append(
            SessionParameter(
                parameter_name=parameter,
                parameter_id=parameter_id,
                target=target,
            )
        )
        # parameter_full_id: str = (
        #     f"{route}/"
        #     f"{parameter}/"
        #     f"{parameter_id}/"
        #     f"{target.tag}/"
        #     f"{target.attributes.get('id', '')}"
        # )
        # logger.info(f"Parameter registered: {parameter_full_id}")

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
                    "hx-get": f"/local-event/{event_id}",
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
                    "hx-post": f"/global-event/{event_id}",
                    "hx-trigger": event,
                    # "hx-target": (
                    #     target.attributes["id"]
                    #     if target is not None else "none"
                    # ),
                    # "hx-swap": "none",
                }
            )
            callback_mapping = self._global_callbacks
        else:
            logger.warning("Unknown context type. Callback not registered.")
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

    def register_dialog(
        self: Renderer,
        dialog_id: str,
        dialog_content: HTMLTag,
    ) -> None:
        if dialog_id not in self._dialogs:
            self._dialogs[dialog_id] = dialog_content

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
        for session_parameter in self._session_parameters[route][parameter]:
            for attr_name, attr_value in attribute.items():
                parameter_id = session_parameter.parameter_id
                component = session_parameter.target
                if attr_name == "inner_content":
                    component.update_attributes(text_content=attr_value)
                    self.update(
                        attr_value,
                        event_id=parameter_id,
                    )
                else:
                    component.update_attributes(
                        attributes={attr_name: attr_value}
                    )
                    self.update(
                        component.to_string(),
                        event_id=parameter_id,
                    )
                # parameter_full_id = (
                #     f"{route}:"
                #     f"{component.tag}:"
                #     f"{component.attributes.get('id', 'no-id')}:"
                #     f"{parameter} -> {attr_value}"
                # )
                # logger.debug(
                #   f"Updated parameter: {parameter_full_id}"
                # )

    def close_dialog(
        self: Renderer,
        dialog_id: str,
    ) -> None:
        if dialog_id not in self._dialogs:
            logger.warning("Dialog '{dialog_id}' not registered.")
            return
        self._dialog_root.text = None
        _ = self._dialog_root.detach_children()
        dialog = deepcopy(self._dialog_root)
        self.update(dialog.to_string(), event_id="dialog")

    def open_dialog(
        self: Renderer,
        dialog_id: str,
    ) -> None:
        if dialog_id not in self._dialogs:
            logger.warning("Dialog '{dialog_id}' not registered.")
            return
        self._dialog_root.text = None
        _ = self._dialog_root.detach_children()
        self._dialog_root.add_child(self._dialogs[dialog_id])
        dialog = deepcopy(self._dialog_root)
        dialog.update_attributes(attributes={"open": ''})
        self.update(dialog.to_string(), event_id="dialog")

    def show(
        self: Renderer,
        route: str,
        page: HTMLTag,
    ) -> None:
        if route in self._routes and route != self._routes[-1]:
            index = self._routes.index(route)
            # Move route
            route = self._routes.pop(index)
            self._routes.append(route)
            # Move root page
            _page = self._pages.pop(index)
            self._pages.append(_page)
            logger.info(
                f"Retrieved page in history: {route}. "
                "Page ready to be displayed."
            )
        elif route not in self._routes:
            self._routes.append(route)
            self._pages.append(page)
            logger.info(
                f"Page added to renderer: {route}. "
                "Page ready to be displayed."
            )
        else:
            logger.info(
                f"Page already exists: {route}. "
                "Page ready to be displayed."
            )
            pass
        self.update_root()

    def close(self: Renderer, route: Optional[str] = None) -> None:
        if route is None:
            route = self._routes[-1]
        if not self._routes or route != self._routes[-1]:
            logger.warning(f"Page {route} is not active, nothing to close.")
            return

        _ = self._routes.pop()
        _ = self._pages.pop()
        logger.info(
            f"Removed page {route} from renderer. "
            "Previous page in history ready to be shown."
        )
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
        logger.info(
            f"Routed to page: {route}. "
            "Page ready to be displayed."
        )
        self.update_root()

    def go_back(self: Renderer, level: int = -1) -> None:
        # Move route
        route = self._routes.pop(level - 1)
        self._routes.append(route)
        # Move root page
        _page = self._pages.pop(level - 1)
        self._pages.append(_page)
        logger.info(
            f"Routed back to page: {route}. "
            "Page ready to be displayed."
        )
        self.update_root()

    def update_root(self: Renderer) -> None:
        _page = self._pages[-1]
        self._root.text = None
        _ = self._root.detach_children()
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
        data = data.replace('\n', '')
        msg: str = f"data: {data}\n\n"
        if event_id is not None:
            msg = f"event: {event_id}\n{msg}"
        self.event_sender.send(msg)

    def trigger_callback(
        self: Renderer,
        context: ContextType,
        event_id: str
    ) -> Optional[Union[HTMLTag, str]]:
        if context == ContextType.LOCAL:
            callback_mapping = self._local_callbacks
        else:
            callback_mapping = self._global_callbacks
        content: Optional[Union[HTMLTag, str]] = None
        if event_id in callback_mapping:
            # Call
            content = callback_mapping[event_id].fn()
        return content


# Instantiate global renderer
global_renderer: Renderer = Renderer()
