from __future__ import annotations
from typing import Union, Optional, List, Dict, Callable, Any
from secrets import token_hex
from copy import deepcopy
from enum import Enum
from threading import Lock
from pydantic import BaseModel, ConfigDict
from pyhtmx import Html, Div, Dialog
from pyhtmx.html_tag import HTMLTag
from .logger import logger
from .master import MASTER_DOCUMENT
from .kit import Page
from .status_bar import StatusBar
from .event_sender import EventSender, global_sender


class Renderer:
    event_sender: EventSender = global_sender

    def __init__(self: Renderer):
        self._clients = []
        self._page_stack: List[str] = []
        self._group_catalog: Dict[str, PageGroup] = {}
        self._group_map: Dict[str, str] = {}
        self._event_map: Dict[str, str] = {}
        self._dialog_map: Dict[str, str] = {}
        self._lock: Lock = Lock()
        self._root: Div = Div(
            _id="root",
            _class="flex flex-col",
            sse_swap="root",
            hx_swap="innerHTML",
        )
        self._dialog_root: Dialog = Dialog(
            _id="dialog",
            _class="modal",
            sse_swap="dialog",
            hx_swap="outerHTML",
        )
        status_bar: Page = StatusBar()
        self.insert(
            namespace=status_bar.namespace,
            route=status_bar.route,
            position=0,
            page=status_bar.page,
        )
        self._status: Page = status_bar.set_up(status_bar.namespace, self)
        self._master: Html = MASTER_DOCUMENT
        body, = self._master.find_elements_by_tag(tag="body")
        body.add_child(self._status.widget)
        body.add_child(self._root)
        body.add_child(self._dialog_root)

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

    def in_catalog(self: Renderer, namespace: str) -> bool:
        return namespace in self._group_catalog

    def add_page_group(self: Renderer, namespace: str) -> None:
        with self._lock:
            self._group_catalog[namespace] = PageGroup(namespace=namespace)

    def list_events(self: Renderer, route: Optional[str]) -> List[str]:
        if route:
            return [e for e, r in self._event_map.items() if r == route]
        else:
            return self._event_map.keys()

    def list_dialogs(self: Renderer, route: Optional[str]) -> List[str]:
        if route:
            return [d for d, r in self._dialog_map.items() if r == route]
        else:
            return self._dialog_map.keys()

    def remove_events(self: Renderer, route: str) -> None:
        for event_id in self.list_events(route):
            del self._event_map[event_id]

    def remove_dialogs(self: Renderer, route: str) -> None:
        for dialog_id in self.list_dialogs(route):
            del self._dialog_map[dialog_id]

    def insert_into_page_group(
        self: Renderer,
        namespace: str,
        route: str,
        position: int,
        page: HTMLTag,
    ) -> None:
        with self._lock:
            self._group_catalog[namespace].insert_page(
                route=route,
                position=position,
                page=page,
            )
        self._group_map[route] = namespace

    def remove_from_page_group(
        self: Renderer,
        route: str,
    ) -> None:
        if route in self._page_stack:
            self._page_stack.remove(route)

        if route in self._group_map:
            namespace = self._group_map.pop(route)
            if self.in_catalog(namespace):
                with self._lock:
                    self._group_catalog[namespace].remove_page(
                        route=route,
                    )
        # Remove registered events and dialogs from maps
        self.remove_events(route)
        self.remove_dialogs(route)

    def add_to_page_group(
        self: Renderer,
        namespace: str,
        route: str,
        item_type: PageItem,
        key: str,
        value: Union[HTMLTag, InteractionParameter, Callback],
    ) -> None:
        with self._lock:
            self._group_catalog[namespace].add_to_page(
                route=route,
                item_type=item_type,
                key=key,
                value=value,
            )
        if item_type == PageItem.DIALOG:
            self._dialog_map[key] = route
        elif item_type in (
            PageItem.LOCAL_CALLBACK,
            PageItem.GLOBAL_CALLBACK,
        ):
            self._event_map[key] = route
        else:
            pass

    def get_from_page_group(
        self: Renderer,
        namespace: str,
        route: str,
        item_type: PageItem,
        key: str,
    ) -> Union[HTMLTag, List[InteractionParameter], Callback, None]:
        item: Union[HTMLTag, List[InteractionParameter], Callback, None] = None
        with self._lock:
            item = self._group_catalog[namespace].get_from_page(
                route=route,
                item_type=item_type,
                key=key,
            )
        return item

    def close_dialog(
        self: Renderer,
        dialog_id: str,
    ) -> None:
        route = self._dialog_map.get(dialog_id, "unknown")
        namespace = self._group_map.get(route, "unknown")
        if not self.in_catalog(namespace):
            logger.warning(f"Dialog '{dialog_id}' not properly registered.")
            return
        # Remove dialog content and show
        self._dialog_root.text = None
        _ = self._dialog_root.detach_children()
        dialog = deepcopy(self._dialog_root)
        self.update(dialog.to_string(), event_id="dialog")

    def open_dialog(
        self: Renderer,
        dialog_id: str,
    ) -> None:
        route = self._dialog_map.get(dialog_id, "unknown")
        namespace = self._group_map.get(route, "unknown")
        if not self.in_catalog(namespace):
            logger.warning(f"Dialog '{dialog_id}' not properly registered.")
            return
        # Retrieve dialog content
        dialog_content = self.get_from_page_group(
            namespace=namespace,
            route=route,
            item_type=PageItem.DIALOG,
            key=dialog_id,
        )
        # Update dialog root and show
        self._dialog_root.text = None
        _ = self._dialog_root.detach_children()
        self._dialog_root.add_child(dialog_content)
        dialog = deepcopy(self._dialog_root)
        dialog.update_attributes(attributes={"open": ''})
        self.update(dialog.to_string(), event_id="dialog")

    def insert(
        self: Renderer,
        namespace: str,
        route: str,
        position: int,
        page: HTMLTag,
    ) -> None:
        # Check if namespace is in the catalog
        if not self.in_catalog(namespace):
            self.add_page_group(namespace)

        self.insert_into_page_group(
            namespace=namespace,
            route=route,
            position=position,
            page=page,
        )

        if route not in self._page_stack:
            self._page_stack.insert(0, route)
            logger.info(
                f"Page inserted in the renderer catalog: {route}. "
            )
        else:
            logger.info(
                f"Page already in the renderer catalog: {route}. "
                "Page updated."
            )

    def remove(
        self: Renderer,
        route: str,
    ) -> None:
        if route == self._page_stack[-1]:
            self.close(route)
        elif route in self._page_stack:
            self._page_stack.remove(route)
            logger.info(
                f"Page removed from the renderer catalog: {route}."
            )
        else:
            logger.info(
                f"Page no longer exists in the catalog: {route}. "
                "Nothing to remove."
            )
        # Remove associated parameters, events and dialogs
        self.remove_from_page_group(route)

    def show(
        self: Renderer,
        namespace: str,
        route: str,
        page: HTMLTag,
    ) -> None:
        if route in self._page_stack and route != self._page_stack[-1]:
            index = self._page_stack.index(route)
            # Move route
            route = self._page_stack.pop(index)
            self._page_stack.append(route)
            logger.info(
                f"Page activated from the catalog: {route}. "
                "Sending to display."
            )
        elif route not in self._page_stack:
            self._page_stack.append(route)
            self.insert(
                namespace=namespace,
                route=route,
                position=0,
                page=page,
            )
            logger.info(
                f"Page appended to the renderer catalog: {route}. "
                "Sending to display."
            )
        else:
            logger.info(
                f"Active page: {route}. "
                "Sending to display."
            )
            pass
        self.update_root()

    def close(self: Renderer, route: Optional[str] = None) -> None:
        if route is None:
            route = self._page_stack[-1]
        if not self._page_stack or route != self._page_stack[-1]:
            logger.warning(f"Page {route} is not active, nothing to close.")
            return
        # Deactivate current page and activate previous page
        current_route: str = self._page_stack.pop()
        self._page_stack.insert(-1, current_route)
        active_route: str = self._page_stack[-1]
        logger.info(
            f"Page deactivated: {route}. "
            f"Previous page activated: {active_route}. "
            "Sending to display."
        )
        self.update_root()

    def go_to(self: Renderer, route: str) -> None:
        if route not in self._page_stack:
            return
        index = self._page_stack.index(route)
        # Move route
        route = self._page_stack.pop(index)
        self._page_stack.append(route)
        logger.info(
            f"Page activated: {route}. Sending to display."
        )
        self.update_root()

    def go_back(self: Renderer, level: int = -1) -> None:
        # Move route
        route = self._page_stack.pop(level - 1)
        self._page_stack.append(route)
        logger.info(
            f"Previous page activated: {route}. "
            "Sending to display."
        )
        self.update_root()

    def update_status(
        self: Renderer,
        ovos_event: str,
        data: Optional[Dict[str, Any]],
    ) -> None:
        if data:
            data.update({"ovos_event": ovos_event})
            self._status.update_session_data(
                session_data=data,
                renderer=self,
            )
        self._status.update_trigger_state(
            ovos_event=ovos_event,
            renderer=self,
        )

    def update_root(self: Renderer) -> None:
        route = self._page_stack[-1]
        namespace = self._group_map.get(route, "unknown")
        if not self.in_catalog(namespace):
            logger.warning(
                f"No valid namespace for page with route '{route}'. "
                "Display will not be updated."
            )
            return
        page = self._group_catalog[namespace].get_page(route)
        self._root.text = None
        _ = self._root.detach_children()
        self._root.add_child(page)
        self.update(page.to_string(), event_id="root")

    def update(
        self: Renderer,
        data: Optional[str],
        event_id: Optional[str] = None,
    ) -> None:
        # Don't send message without clients or data
        if not self._clients or data is None:
            return
        # Format SSE message
        data = data.replace('\n', '')
        msg: str = f"data: {data}\n\n"
        if event_id is not None:
            msg = f"event: {event_id}\n{msg}"
        self.event_sender.send(msg)


# Instantiate global renderer
global_renderer: Renderer = Renderer()
