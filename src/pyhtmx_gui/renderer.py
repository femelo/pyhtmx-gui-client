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


class ContextType(str, Enum):
    LOCAL = "local"
    GLOBAL = "global"


class PageItemType(str, Enum):
    DIALOG = "dialog"
    PARAMETER = "parameter"
    LOCAL_CALLBACK = "local_callback"
    GLOBAL_CALLBACK = "global_callback"


class Callback(BaseModel):
    model_config = ConfigDict(
        strict=False,
        arbitrary_types_allowed=True,
        populate_by_name=False,
    )
    context: ContextType
    event_name: str
    event_id: str
    fn: Callable
    source: HTMLTag
    target: Optional[HTMLTag] = None
    target_level: str = "innerHTML"


class InteractionParameter(BaseModel):
    model_config = ConfigDict(
        strict=False,
        arbitrary_types_allowed=True,
        populate_by_name=False,
    )
    parameter_name: str
    parameter_id: str
    target: HTMLTag


class PageItemCollection(BaseModel):
    model_config = ConfigDict(
        strict=False,
        arbitrary_types_allowed=True,
        populate_by_name=False,
    )
    route: str
    page: HTMLTag
    dialogs: Dict[str, HTMLTag] = {}
    parameters: Dict[str, List[InteractionParameter]] = {}
    global_callbacks: Dict[str, Callback] = {}
    local_callbacks: Dict[str, Callback] = {}
    _item_map: Dict[
        PageItemType,
        Union[HTMLTag, List[InteractionParameter], Callback]
    ] = {}

    def model_post_init(self: PageItemCollection, context: Any = None) -> None:
        self._item_map[PageItemType.DIALOG] = self.dialogs
        self._item_map[PageItemType.PARAMETER] = self.parameters
        self._item_map[PageItemType.LOCAL_CALLBACK] = self.local_callbacks
        self._item_map[PageItemType.GLOBAL_CALLBACK] = self.global_callbacks

    def set_item(
        self: PageItemCollection,
        item_type: PageItemType,
        key: str,
        value: Union[HTMLTag, InteractionParameter, Callback],
    ) -> None:
        item = self._item_map.get(item_type, None)
        if item is None:
            logger.warning(
                f"Unknown page group item: {item_type}. "
                f"Pair ({key}, {value}) not set."
            )
            return
        if item_type == PageItemType.PARAMETER:
            if key not in item:
                item[key] = []
            item[key].append(value)
        else:
            item[key] = value

    def get_item(
        self: PageItemCollection,
        item_type: PageItemType,
        key: str
    ) -> Union[HTMLTag, List[InteractionParameter], Callback, None]:
        item = self._item_map.get(item_type, {})
        value = item.get(key, None)
        if not item:
            logger.warning(
                f"Unknown page group item: {item_type}."
            )
        elif not value:
            logger.warning(
                f"Key '{key}' for item '{item_type}' not found."
            )
        else:
            pass
        return value


class PageGroup(BaseModel):
    model_config = ConfigDict(
        strict=False,
        arbitrary_types_allowed=True,
        populate_by_name=False,
    )
    namespace: str
    routes: List[str] = []
    pages: Dict[str, PageItemCollection] = {}

    def validate_position(self: PageGroup, position: int) -> int:
        length = len(self.routes)
        if abs(position) > length:
            logger.warning(
                "Provided position out of range. "
                "Setting it at nearest bound."
            )
            return max(min(position, length), -length)
        return position

    def insert_page(
        self: PageGroup,
        route: str,
        position: int,
        page: HTMLTag,
    ) -> None:
        if route not in self.routes:
            position = self.validate_position(position)
            self.routes.insert(position, route)
        else:
            index = self.routes.index(route)
            if index != position:
                route = self.routes.pop(index)
                position = self.validate_position(position)
                self.routes.insert(position, route)
            logger.info(
                f"Item collection for page '{route}' already exists. "
                f"Collection will be updated."
            )
        self.pages[route] = PageItemCollection(route=route, page=page)

    def get_page(self: PageGroup, route: str) -> Optional[HTMLTag]:
        page_items = self.pages.get(route, None)
        if not page_items:
            logger.warning(
                f"Route '{route}' not in page group '{self.namespace}'. "
                f"Page not retrieved."
            )
            return
        return page_items.page

    def remove_page(
        self: PageGroup,
        route: str,
    ) -> None:
        if route not in self.routes:
            self.routes.remove(route)
            del self.pages[route]
        else:
            logger.warning(
                f"Item collection for page '{route}' does not exist. "
                f"Nothing to remove."
            )

    def add_to_page(
        self: PageGroup,
        route: str,
        item_type: PageItemType,
        key: str,
        value: Union[HTMLTag, InteractionParameter, Callback],
    ) -> None:
        page_items = self.pages.get(route, None)
        if not page_items:
            logger.warning(
                f"Route '{route}' not in page group '{self.namespace}'. "
                f"Pair ({key}, {value}) not added."
            )
            return
        page_items.set_item(item_type=item_type, key=key, value=value)

    def get_from_page(
        self: PageGroup,
        route: str,
        item_type: PageItemType,
        key: str,
    ) -> Union[HTMLTag, List[InteractionParameter], Callback, None]:
        page_items = self.pages.get(route, None)
        if not page_items:
            logger.warning(
                f"Route '{route}' not in page group '{self.namespace}'. "
                f"Value for '{key}' not retrieved."
            )
            return
        return page_items.get_item(item_type=item_type, key=key)


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
        item_type: PageItemType,
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
        if item_type == PageItemType.DIALOG:
            self._dialog_map[key] = route
        elif item_type in (
            PageItemType.LOCAL_CALLBACK,
            PageItemType.GLOBAL_CALLBACK,
        ):
            self._event_map[key] = route
        else:
            pass

    def get_from_page_group(
        self: Renderer,
        namespace: str,
        route: str,
        item_type: PageItemType,
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

    def register_interaction_parameter(
        self: Renderer,
        namespace: str,
        route: str,
        parameter: str,
        target: HTMLTag,
        target_level: Optional[str] = "innerHTML",
    ) -> None:
        # Check if namespace is in the catalog
        if not self.in_catalog(namespace):
            logger.warning(
                f"Namespace '{namespace}' not in page group catalog. "
                f"Parameter '{route}::{parameter}' not registered."
            )
            return
        # Set new id
        _id: str = token_hex(4)
        parameter_id = f"{parameter}-{_id}"
        target.update_attributes(
            attributes={
                "sse-swap": parameter_id,
                "hx-swap": target_level,
            },
        )
        # Instantiate interaction parameter
        interaction_parameter: InteractionParameter = InteractionParameter(
            parameter_name=parameter,
            parameter_id=parameter_id,
            target=target,
        )
        # Register parameter
        self.add_to_page_group(
            namespace=namespace,
            route=route,
            item_type=PageItemType.PARAMETER,
            key=parameter,
            value=interaction_parameter,
        )

    def register_callback(
        self: Renderer,
        namespace: str,
        route: str,
        event: str,
        context: Union[str, ContextType],
        fn: Callable,
        source: HTMLTag,
        target: Optional[HTMLTag] = None,
        target_level: str = "innerHTML",
    ) -> None:
        # Check if namespace is in the catalog
        if not self.in_catalog(namespace):
            logger.warning(
                f"Namespace '{namespace}' not in page group catalog. "
                f"Callback for '{route}::{event}' not registered."
            )
            return
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
                    },
                )
            source.update_attributes(
                attributes={
                    "hx-get": f"/local-event/{event_id}",
                    "hx-trigger": event,
                    "hx-target": target.attributes["id"],
                    "hx-swap": target_level,
                },
            )
            item_type = PageItemType.LOCAL_CALLBACK
        elif context == ContextType.GLOBAL:
            # Add necessary attributes to elements for global action
            target.update_attributes(
                attributes={
                    "sse-swap": event_id,
                },
            )
            source.update_attributes(
                attributes={
                    "hx-post": f"/global-event/{event_id}",
                    "hx-trigger": event,
                },
            )
            item_type = PageItemType.GLOBAL_CALLBACK
        else:
            logger.warning("Unknown context type. Callback not registered.")
            return
        # Instantiate callback
        callback: Callback = Callback(
            context=context,
            event_name=event,
            event_id=event_id,
            fn=fn,
            source=source,
            target=target,
            target_level=target_level,
        )
        # Register callback
        self.add_to_page_group(
            namespace=namespace,
            route=route,
            item_type=item_type,
            key=event_id,
            value=callback,
        )

    def register_dialog(
        self: Renderer,
        namespace: str,
        route: str,
        dialog_id: str,
        dialog_content: HTMLTag,
    ) -> None:
        # Check if namespace is in the catalog
        if not self.in_catalog(namespace):
            logger.warning(
                f"Namespace '{namespace}' not in page group catalog. "
                f"Dialog '{route}::{dialog_id}' not registered."
            )
            return
        # Register callback
        self.add_to_page_group(
            namespace=namespace,
            route=route,
            item_type=PageItemType.DIALOG,
            key=dialog_id,
            value=dialog_content,
        )

    def update_attributes(
        self: Renderer,
        route: str,
        parameter: str,
        attribute: Dict[str, Any],
    ) -> None:
        namespace: str = self._group_map.get(route, "unknown")
        if not self.in_catalog(namespace):
            logger.warning(f"Page with '{route}' not properly inserted.")
            return
        parameter_list: Optional[
            List[InteractionParameter]
        ] = self.get_from_page_group(
            namespace=namespace,
            route=route,
            item_type=PageItemType.PARAMETER,
            key=parameter,
        )
        if not parameter_list:
            logger.warning(
                f"Parameter '{route}::{parameter}' not properly registered."
            )
            return
        for interaction_parameter in parameter_list:
            parameter_id = interaction_parameter.parameter_id
            component = interaction_parameter.target
            attributes = dict(attribute)
            text_content = attributes.pop("inner_content", None)
            component.update_attributes(
                text_content=text_content,
                attributes=attributes,
            )
            if attribute:
                self.update(
                    component.to_string(),
                    event_id=parameter_id,
                )
            else:
                self.update(
                    text_content,
                    event_id=parameter_id,
                )

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
            item_type=PageItemType.DIALOG,
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

    def trigger_callback(
        self: Renderer,
        context: ContextType,
        event_id: str
    ) -> Optional[Union[HTMLTag, str]]:
        route = self._event_map.get(event_id, "unknown")
        namespace = self._group_map.get(route, "unknown")
        if not self.in_catalog(namespace):
            logger.warning(f"Event '{event_id}' not properly registered.")
            return
        # Retrieve callback
        callback = self.get_from_page_group(
            namespace=namespace,
            route=route,
            item_type=(
                PageItemType.LOCAL_CALLBACK
                if context == ContextType.LOCAL
                else PageItemType.GLOBAL_CALLBACK
            ),
            key=event_id,
        )
        # Call and return content
        content: Optional[Union[HTMLTag, str]] = None
        if callback:
            content = callback.fn()
        return content


# Instantiate global renderer
global_renderer: Renderer = Renderer()
