from __future__ import annotations
from typing import Optional, List, Tuple, Dict, Any
from copy import deepcopy
from threading import Lock
from queue import Queue
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
        self._last_shown: Tuple[str, str] = ()
        self._queue: Queue = Queue()
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
        self._status: Page = StatusBar()  # TODO: what here?
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
        if route in self._queue:
            self._queue.remove(route)

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
            self._gui_manager.activate_namespace(namespace)

        # If page was not provided, use active page
        active_page_id = self._gui_manager.get_active_page_id()
        page_id = page_id or active_page_id
        if not self._gui_manager.in_page_group(namespace, page_id):
            logger.info(
                f"Page '{page_id}' not available for namespace '{namespace}'. "
                "Nothing to display."
            )
            return
        if page_id != active_page_id:
            self._gui_manager.activate_page(namespace, page_id)

        # Queue for displaying
        self._queue.put((namespace, page_id))
        logger.info(
            f"Page activated: {namespace}::{page_id}. "
            "Sending to display."
        )
        self.update_root()

    def close(
        self: Renderer,
        namespace: Optional[str] = None,
        page_id: Optional[str] = None,
    ) -> None:
        # If namespace is explicitly provided, then it shall be deactivated
        deactivate_namespace: bool = namespace is not None
        # Get active namespace
        active_namespace = self._gui_manager.get_active_namespace()
        # Get active page
        active_page_id = self._gui_manager.get_active_page_id()

        if not deactivate_namespace:
            namespace = namespace or active_namespace
        elif self._gui_manager.in_catalog(namespace):
            # Deactivate only if namespace explicitly provided
            if namespace == active_namespace:
                self._gui_manager.deactivate_namespace()
                active_namespace = self._gui_manager.get_active_namespace()
        else:
            logger.info(
                f"Namespace {namespace} not available in the catalog."
            )

        page_id = page_id or active_page_id
        if self._gui_manager.in_page_group(namespace, page_id):
            # Deactivate only if page_id is active
            if page_id == active_page_id:
                logger.info(
                    f"Page deactivated: {namespace}::{page_id}"
                )
                if not deactivate_namespace:
                    self._gui_manager.deactivate_page(namespace)
            active_page_id = self._gui_manager.get_active_page_id()
        else:
            logger.info(
                f"Page '{page_id}' not available for namespace '{namespace}'."
            )

        # Queue for displaying
        logger.info(
            f"Page activated: {active_namespace}::{active_page_id}. "
            "Sending to display."
        )
        self._queue.put((active_namespace, active_page_id))
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
        namespace, page_id = route = self._queue.get()
        if route == self._last_shown:
            logger.warning(
                f"Display already showing '{namespace}::{page_id}'. "
                "Update not required."
            )
            return
        # Update
        self._last_shown = route
        page_tag = self._gui_manager.get_active_page_tag(namespace)
        self._root.text = None
        _ = self._root.detach_children()
        self._root.add_child(page_tag)
        self.update(page_tag.to_string(), event_id="root")

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
