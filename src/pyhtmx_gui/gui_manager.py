from __future__ import annotations
from typing import Any, Union, Optional, List, Dict
from secrets import token_hex
from pyhtmx.html_tag import HTMLTag
from .types import PageItem, InputItem, OutputItem, CallbackContext
from .renderer import Renderer, global_renderer
from .page_group import PageGroup
from .utils import validate_position, fix_position
from .logger import logger


class GUIManager:
    renderer: Renderer = global_renderer

    def __init__(self: GUIManager) -> None:
        self._namespaces: List[str] = []
        self._catalog: Dict[str, PageGroup] = {}
        GUIManager.renderer.set_gui_manager(self)

    @property
    def num_namespaces(self: GUIManager) -> int:
        return len(self._namespaces)

    def in_catalog(self: GUIManager, namespace: str) -> bool:
        return namespace in self._catalog

    def in_page_group(self: GUIManager, namespace: str, page_id: str) -> bool:
        return (
            self.in_catalog(namespace) and
            self._catalog[namespace].in_group(page_id)
        )

    def get_active_namespace(
        self: GUIManager,
    ) -> Optional[str]:
        if not self._namespaces:
            return None
        return self._namespaces[0]

    def activate_namespace(
        self: GUIManager,
        namespace: str,
    ) -> None:
        if namespace in self._namespaces:
            index = self._namespaces.index(namespace)
            self._namespaces.pop(index)
        self._namespaces.insert(0, namespace)

    def deactivate_namespace(
        self: GUIManager,
    ) -> None:
        if not self._namespaces:
            return
        namespace = self._namespaces.pop(0)
        self._namespaces.insert(1, namespace)

    def insert_namespace(
        self: GUIManager,
        namespace: str,
        position: int,
    ) -> None:
        if namespace in self._namespaces:
            index = self._namespaces.index(namespace)
            self._namespaces.pop(index)
        # Validate position
        if not validate_position(position, self.num_namespaces):
            position = fix_position(position, self.num_namespaces)
        # Insert
        self._namespaces.insert(position, namespace)
        # Add page group
        if not self.in_catalog(namespace):
            self._catalog[namespace] = PageGroup(
                namespace=namespace,
                renderer=GUIManager.renderer,
            )

    def remove_namespace(
        self: GUIManager,
        namespace: str,
    ) -> None:
        if namespace in self._namespaces:
            if namespace == self.get_active_namespace():
                self.close(namespace=namespace)
            self._namespaces.remove(namespace)
        else:
            logger.info(
                f"Namespace '{namespace}' no longer exists. "
                "Nothing to remove."
            )
        # Remove from catalog
        if self.in_catalog(namespace):
            del self._catalog[namespace]

    def insert_pages(
        self: GUIManager,
        namespace: str,
        page_args: List[Dict[str, str]],
        session_data: Dict[str, Any],
        position: int,
    ) -> None:
        if not self.in_catalog(namespace):
            self._catalog[namespace] = PageGroup(
                namespace=namespace,
                renderer=GUIManager.renderer,
            )
        prefix = namespace.replace('.', '_')
        for item in reversed(page_args):
            token = token_hex(4)
            self._catalog[namespace].insert_page(
                page_id=item.get("page", f"{prefix}_{token}"),
                uri=item.get("url"),
                session_data=session_data,
                position=position,
            )
        if set(self._namespaces) == {namespace}:
            self.show(namespace, id=0)

    def remove_pages(
        self: GUIManager,
        namespace: str,
        position: int,
        items_number: int = 1,
    ) -> None:
        if not self.in_catalog(namespace):
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to remove."
            )
            return
        # Remove pages
        for _ in range(items_number):
            if position == self._catalog[namespace].active_index:
                self.close(namespace, id=position)
            self._catalog[namespace].remove_page(position)

    def move_pages(
        self: GUIManager,
        namespace: str,
        from_position: int,
        to_position: int,
        items_number: int = 1,
    ) -> None:
        if not self.in_catalog(namespace):
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to move."
            )
            return
        # Move pages
        for _ in range(items_number):
            self._catalog[namespace].move_page(
                from_position,
                to_position,
            )

    def get_active_page_id(
        self: GUIManager,
        namespace: Optional[str] = None,
    ) -> Optional[str]:
        namespace = namespace or self.get_active_namespace()
        if not self.in_catalog(namespace):
            return None
        return self._catalog[namespace].get_active_page_id()

    def get_active_page(
        self: GUIManager,
        namespace: str,
    ) -> Optional[Any]:
        if not self.in_catalog(namespace):
            return None
        return self._catalog[namespace].get_active_page()

    def get_active_page_tag(
        self: GUIManager,
        namespace: str,
    ) -> Optional[HTMLTag]:
        if not self.in_catalog(namespace):
            return None
        return self._catalog[namespace].get_active_page_tag()

    def activate_page(
        self: GUIManager,
        namespace: str,
        id: Union[int, str],
    ) -> None:
        if not self.in_catalog(namespace):
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to move."
            )
            return
        self.activate_namespace(namespace)
        self._catalog[namespace].activate_page(id)

    def deactivate_page(
        self: GUIManager,
        namespace: str,
    ) -> None:
        if not self.in_catalog(namespace):
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to move."
            )
            return
        self._catalog[namespace].deactivate_page()

    def show(
        self: GUIManager,
        namespace: str,
        id: Union[str, int, None] = None,
    ) -> None:
        # Get page id
        if isinstance(id, int):
            page_id = self._catalog[namespace].get_page_id(id)
        else:
            page_id = id
        # Show page
        GUIManager.renderer.show(
            namespace=namespace,
            page_id=page_id,
        )

    def close(
        self: GUIManager,
        namespace: str,
        id: Union[str, int, None] = None,
    ) -> None:
        # Get page id
        if isinstance(id, int):
            page_id = self._catalog[namespace].get_page_id(id)
        else:
            page_id = id
        # Close page
        GUIManager.renderer.close(
            namespace=namespace,
            page_id=page_id,
        )

    def add_item(
        self: GUIManager,
        namespace: str,
        page_id: str,
        item_type: PageItem,
        key: str,
        value: InputItem,
    ) -> None:
        if not self.in_catalog(namespace):
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Item will not be added."
            )
            return
        return self._catalog[namespace].add_item(
            page_id=page_id,
            item_type=item_type,
            key=key,
            value=value,
        )

    def get_item(
        self: GUIManager,
        namespace: str,
        page_id: str,
        item_type: PageItem,
        key: str,
    ) -> Optional[OutputItem]:
        if not self.in_catalog(namespace):
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Item will not be retrieved."
            )
            return
        return self._catalog[namespace].get_item(
            page_id=page_id,
            item_type=item_type,
            key=key,
        )

    def update_status(
        self: GUIManager,
        ovos_event: str,
        data: Optional[Dict[str, Any]],
    ) -> None:
        # Update status
        GUIManager.renderer.update_status(
            ovos_event=ovos_event,
            data=data,
        )

    def update_data(
        self: GUIManager,
        namespace: str,
        session_data: Dict[str, Any],
    ) -> None:
        if not self.in_catalog(namespace):
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to update."
            )
            return
        # Update data
        page_id = self._catalog[namespace].get_active_page_id()
        if page_id:
            self._catalog[namespace].update_data(
                page_id=page_id,
                session_data=session_data,
            )

    def update_state(
        self: GUIManager,
        namespace: str,
        ovos_event: str,
    ) -> None:
        if not self.in_catalog(namespace):
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to update."
            )
            return
        # Update event
        page_id = self._catalog[namespace].get_active_page_id()
        if page_id:
            self._catalog[namespace].update_state(
                page_id=page_id,
                ovos_event=ovos_event,
            )

    def trigger_callback(
        self: GUIManager,
        context: CallbackContext,
        event_id: str,
    ) -> Any:
        namespace = self.get_active_namespace()
        page_id = self.get_active_page_id()
        self._catalog[namespace].trigger_callback(
            page_id=page_id,
            context=context,
            event_id=event_id,
        )
