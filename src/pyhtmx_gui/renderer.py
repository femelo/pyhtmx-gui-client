from __future__ import annotations
from typing import Optional, List, Dict, Any
from copy import deepcopy
from threading import Lock
from pyhtmx import Html, Div, Dialog
from .logger import logger
from .master import MASTER_DOCUMENT
from .kit import Page
from .status_bar import StatusBar
from .gui_manager import GUIManager
from .event_sender import EventSender, global_sender


class Renderer:
    event_sender: EventSender = global_sender

    def __init__(self: Renderer):
        self._clients = []
        self._gui_manager: Optional[GUIManager] = None
        self._page_stack: List[str] = []
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

    def set_gui_manager(self: Renderer, gui_manager: GUIManager) -> None:
        self._gui_manager = gui_manager

    def register_client(self: Renderer, client_id: str) -> None:
        if client_id not in self._clients:
            self._clients.append(client_id)
        logger.info(f"Number of clients in registry: {len(self._clients)}")

    def deregister(self: Renderer, client_id: str) -> None:
        if client_id in self._clients:
            self._clients.remove(client_id)
        logger.info(f"Number of clients in registry: {len(self._clients)}")

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

    # NOTE: this belongs here for the sake of behavior towards updating the display
    # TODO: refactor it
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
        namespace: str,
        page_id: str,
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

    def show(
        self: Renderer,
        namespace: Optional[str] = None,
        page_id: Optional[str] = None,
    ) -> None:
        # If namespace was not provided, use active namespace
        active_namespace = self._gui_manager.get_active_namespace()
        namespace = namespace or active_namespace
        if not self._gui_manager.in_catalog(namespace):
            logger.info(
                f"Namespace {namespace} not available in the catalog. "
                "Nothing to display."
            )
            return
        if namespace != active_namespace:
            self._gui_manager.activate_namespace(namespace=namespace)
            logger.info(f"Namespace activated: {namespace}")

        # If page was not provided, get the active page
        active_page_id = self._gui_manager.get_active_page_id()
        page_id = page_id or active_page_id
        if not self._gui_manager.in_page_group(namespace, page_id):
            logger.info(
                f"Page '{page_id}' not available for namespace '{namespace}'. "
                "Nothing to display."
            )
            return
        if page_id != active_page_id:
            self._gui_manager.activate_page(namespace=namespace, id=page_id)
        # Get page
        active_page = self._gui_manager.get_active_page_tag(
            namespace=namespace,
        )
        if active_page:
            logger.info(
                f"Page activated from the catalog: {namespace}::{page_id}. "
                "Sending to display."
            )
            self._page_stack.append(active_page)
            self.update_root()

    # TODO: finish refactoring
    def close(
        self: Renderer,
        namespace: Optional[str] = None,
        page_id: Optional[str] = None,
    ) -> None:
        # If namespace was not provided, use active namespace
        active_namespace = self._gui_manager.get_active_namespace()
        namespace = namespace or active_namespace
        if not self._gui_manager.in_catalog(namespace):
            logger.info(
                f"Namespace {namespace} not available in the catalog. "
                "Nothing to close."
            )
        if namespace != active_namespace:
            logger.info(f"Namespace '{namespace}' no longer active.")

        # If page was not provided, get the active page
        active_page_id = self._gui_manager.get_active_page_id()
        page_id = page_id or active_page_id
        if not self._gui_manager.in_page_group(namespace, page_id):
            logger.info(
                f"Page '{page_id}' not available for namespace '{namespace}'. "
                "Nothing to display."
            )
        if page_id != active_page_id:
            logger.info(f"Page '{namespace}::{page_id}' no longer active.")

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
