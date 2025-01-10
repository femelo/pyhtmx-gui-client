from __future__ import annotations
from typing import Optional, List, Tuple, Set, Dict, Any
from copy import deepcopy
from threading import Lock
from queue import Queue
from pyhtmx import Html, Div, Dialog
from .logger import logger
from .master import MASTER_DOCUMENT
from .types import InteractionParameter, PageItem, PageNeighbor
from .kit import Page
from .status_bar import StatusBar
from .page_manager import PageManager
from .event_sender import EventSender, global_sender


SPECIAL_NAMESPACES: Set[str] = {"status"}


class Renderer:
    event_sender: EventSender = global_sender

    def __init__(self: Renderer):
        self._clients = []
        self._gui_manager: Optional[Any] = None  # type: Optional[GUIManager]
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
        self._special_managers: Dict[Tuple[str, str], PageManager] = {}
        status_ns, status_id = ("status", "status-bar")
        status_manager = PageManager(
            namespace=status_ns,
            page_id=status_id,
            page_src=StatusBar(),
            renderer=self,
        )
        self._status: Page = status_manager.page
        self._master: Html = MASTER_DOCUMENT
        body, = self._master.find_elements_by_tag(tag="body")
        body.add_child(self._status.widget)
        body.add_child(self._root)
        body.add_child(self._dialog_root)
        self.set_special_manager(status_ns, status_id, status_manager)

    @property
    def document(self: Renderer) -> Html:
        return self._master

    def is_special(self: Renderer, namespace: str) -> bool:
        return namespace in SPECIAL_NAMESPACES

    def set_special_manager(
        self: Renderer,
        namespace: str,
        page_id: str,
        page_manager: PageManager,
    ) -> None:
        route: Tuple[str, str] = (namespace, page_id)
        self._special_managers[route] = page_manager

    def get_special_manager(
        self: Renderer,
        namespace: str,
        page_id: str,
    ) -> Optional[PageManager]:
        route: Tuple[str, str] = (namespace, page_id)
        if route in self._special_managers:
            return self._special_managers[route]
        return None

    def set_gui_manager(self: Renderer, gui_manager: Any) -> None:
        self._gui_manager = gui_manager

    def register_client(self: Renderer, client_id: str) -> None:
        if client_id not in self._clients:
            self._clients.append(client_id)
        logger.info(f"Number of clients in registry: {len(self._clients)}")

    def deregister(self: Renderer, client_id: str) -> None:
        if client_id in self._clients:
            self._clients.remove(client_id)
        logger.info(f"Number of clients in registry: {len(self._clients)}")

    def update_special_attributes(
        self: Renderer,
        namespace: Optional[str],
        page_id: Optional[str],
        parameter: str,
        attribute: Dict[str, Any],
    ) -> None:
        page_manager: Optional[PageManager] = self.get_special_manager(
            namespace,
            page_id,
        )
        if not page_manager:
            logger.info(
                f"Page '{page_id}' not available for namespace '{namespace}'. "
                "Parameter will not be updated."
            )
            return

        parameter_list: Optional[List[InteractionParameter]] = \
            page_manager.get_item(
                item_type=PageItem.PARAMETER,
                key=parameter,
            )
        if not parameter_list:
            logger.warning(
                f"Parameter '{namespace}::{page_id}::{parameter}' "
                "not registered."
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
                self.send(
                    component.to_string(),
                    event_id=parameter_id,
                )
            else:
                self.send(
                    text_content,
                    event_id=parameter_id,
                )

    def update_attributes(
        self: Renderer,
        namespace: Optional[str],
        page_id: Optional[str],
        parameter: str,
        attribute: Dict[str, Any],
    ) -> None:
        # If namespace was not provided, use active namespace
        active_namespace = self._gui_manager.get_active_namespace()
        namespace = namespace or active_namespace

        if self.is_special(namespace):
            self.update_special_attributes(
                namespace,
                page_id,
                parameter,
                attribute,
            )
            return

        if not self._gui_manager.in_catalog(namespace):
            logger.info(
                f"Namespace {namespace} not available in the catalog. "
                "Parameter will not be updated."
            )
            return

        # If page was not provided, use active page
        active_page_id = self._gui_manager.get_active_page_id()
        page_id = page_id or active_page_id
        if not self._gui_manager.in_page_group(namespace, page_id):
            logger.info(
                f"Page '{page_id}' not available for namespace '{namespace}'. "
                "Parameter will not be updated."
            )
            return

        parameter_list: Optional[List[InteractionParameter]] = \
            self._gui_manager.get_item(
                namespace=namespace,
                page_id=page_id,
                item_type=PageItem.PARAMETER,
                key=parameter,
            )
        if not parameter_list:
            logger.warning(
                f"Parameter '{namespace}::{page_id}::{parameter}' "
                "not registered."
            )
            return

        route: Tuple[str, str] = (namespace, page_id)
        for interaction_parameter in parameter_list:
            parameter_id = interaction_parameter.parameter_id
            component = interaction_parameter.target
            attributes = dict(attribute)
            text_content = attributes.pop("inner_content", None)
            component.update_attributes(
                text_content=text_content,
                attributes=attributes,
            )
            if route == self._last_shown:
                if attribute:
                    self.send(
                        component.to_string(),
                        event_id=parameter_id,
                    )
                else:
                    self.send(
                        text_content,
                        event_id=parameter_id,
                    )

    def close_dialog(
        self: Renderer,
        dialog_id: Optional[str] = None,
    ) -> None:
        # Remove dialog content and show
        self._dialog_root.text = None
        _ = self._dialog_root.detach_children()
        dialog = deepcopy(self._dialog_root)
        self.send(dialog.to_string(), event_id="dialog")

    def open_dialog(
        self: Renderer,
        dialog_id: str,
    ) -> None:
        # Get active namespace and page id
        namespace = self._gui_manager.get_active_namespace()
        if not namespace:
            logger.info(
                "No namespace active. Dialog will not open."
            )
            return
        page_id = self._gui_manager.get_active_page_id()
        if not page_id:
            logger.info(
                "No page active. Dialog will not open."
            )
            return
        # Retrieve dialog content
        dialog_content = self._gui_manager.get_item(
            namespace=namespace,
            page_id=page_id,
            item_type=PageItem.DIALOG,
            key=dialog_id,
        )
        # Update dialog root and show
        self._dialog_root.text = None
        _ = self._dialog_root.detach_children()
        self._dialog_root.add_child(dialog_content)
        dialog = deepcopy(self._dialog_root)
        dialog.update_attributes(attributes={"open": ''})
        if (namespace, page_id) == self._last_shown:
            self.send(dialog.to_string(), event_id="dialog")

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
            "Queueing to display."
        )
        self.update_root()

    def show_next(
        self: Renderer,
    ) -> None:
        self.show_neighbor(PageNeighbor.NEXT)

    def show_previous(
        self: Renderer,
    ) -> None:
        self.show_neighbor(PageNeighbor.PREVIOUS)

    def show_neighbor(
        self: Renderer,
        neighbor: PageNeighbor,
    ) -> None:
        # Get active namespace and page id
        namespace = self._gui_manager.get_active_namespace()
        if not namespace:
            logger.info(
                f"No namespace active. "
                f"{neighbor.title()} page will not be shown."
            )
            return
        page_index = self._gui_manager.get_active_page_index()
        if not page_index:
            logger.info(
                "No page active. "
                f"{neighbor.title()} page will not be shown."
            )
            return
        num_pages = self._gui_manager.get_num_pages()
        if num_pages == 1:
            logger.info(
                "Only one page available. "
                f"{neighbor.title()} page will not be shown."
            )
            return
        # Get neighboring page index
        offset: int = 1 if neighbor == PageNeighbor.NEXT else -1
        n_page_index: int = (page_index + offset) % num_pages
        page_id = self._gui_manager.get_active_page_id()
        # Activate neighboring page
        self._gui_manager.activate_page(namespace, n_page_index)
        n_page_id = self._gui_manager.get_active_page_id()
        # Confirm deactivation of previous page
        if n_page_id != page_id:
            logger.info(
                f"Page deactivated: {namespace}::{page_id}"
            )
            page_id = n_page_id
        # Queue for displaying
        self._queue.put((namespace, page_id))
        logger.info(
            f"Page activated: {namespace}::{page_id}. "
            "Queueing to display."
        )
        self.update_neighbor(neighbor)

    def close(
        self: Renderer,
        namespace: Optional[str] = None,
        page_id: Optional[str] = None,
    ) -> None:
        # Close specified page by deactivating the namespace
        active_namespace = self._gui_manager.get_active_namespace()
        active_page_id = self._gui_manager.get_active_page_id()
        namespace = namespace or active_namespace
        page_id = page_id or active_page_id

        if self._gui_manager.in_catalog(namespace):
            # Deactivate namespace currently active
            if namespace == active_namespace:
                self._gui_manager.deactivate_namespace()
                # New namespace to display
                active_namespace = self._gui_manager.get_active_namespace()
        else:
            logger.info(
                f"Namespace {namespace} not available in the catalog."
            )

        if self._gui_manager.in_page_group(namespace, page_id):
            # Report only if page is currently active
            if page_id == active_page_id:
                logger.info(
                    f"Page deactivated: {namespace}::{page_id}"
                )
            # New page to display (for new namespace)
            active_page_id = self._gui_manager.get_active_page_id()
        else:
            logger.info(
                f"Page '{page_id}' not available for namespace '{namespace}'."
            )

        # Queue for displaying
        logger.info(
            f"Page activated: {active_namespace}::{active_page_id}. "
            "Queueing to display."
        )
        self._queue.put((active_namespace, active_page_id))
        self.update_root()

    def close_page(
        self: Renderer,
        namespace: Optional[str] = None,
        page_id: Optional[str] = None,
    ) -> None:
        # Close specified page by deactivating only the page
        active_namespace = self._gui_manager.get_active_namespace()
        active_page_id = self._gui_manager.get_active_page_id()
        namespace = namespace or active_namespace
        page_id = page_id or active_page_id

        if not self._gui_manager.in_catalog(namespace):
            logger.info(
                f"Namespace {namespace} not available in the catalog."
            )

        if self._gui_manager.in_page_group(namespace, page_id):
            # Deactivate only if page is currenly active
            if page_id == active_page_id:
                logger.info(
                    f"Page deactivated: {namespace}::{page_id}"
                )
                self._gui_manager.deactivate_page(namespace)
                # New page to display
                active_page_id = self._gui_manager.get_active_page_id()
        else:
            logger.info(
                f"Page '{page_id}' not available for namespace '{namespace}'."
            )

        # Queue for displaying
        logger.info(
            f"Page activated: {active_namespace}::{active_page_id}. "
            "Queueing to display."
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
        self.send(page_tag.to_string(), event_id="root")

    def update_neighbor(self: Renderer, neighbor: PageNeighbor) -> None:
        namespace, page_id = route = self._queue.get()
        if route == self._last_shown:
            logger.warning(
                f"Display already showing '{namespace}::{page_id}'. "
                "Update not required."
            )
            return
        # Update
        self._last_shown = route
        page_tag = deepcopy(self._gui_manager.get_active_page_tag(namespace))
        self._root.text = None
        _ = self._root.detach_children()
        self._root.add_child(page_tag)
        page_tag.update_attributes(
            attributes={"class": neighbor},
            incremental=True,
        )
        self.send(page_tag.to_string(), event_id="root")

    def send(
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
