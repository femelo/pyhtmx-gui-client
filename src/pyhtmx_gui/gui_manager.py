from __future__ import annotations
from typing import Any, Union, Optional, List, Dict
from secrets import token_hex
from pyhtmx.html_tag import HTMLTag
from .renderer import Renderer, global_renderer
from .page_group import PageGroup
from .tools.utils import validate_position, fix_position
from .logger import logger


class GuiManager:
    renderer: Renderer = global_renderer

    def __init__(self: GuiManager) -> None:
        self._namespaces: List[str] = []
        self._catalog: Dict[str, PageGroup] = {}
        GuiManager.renderer.set_gui_manager(self)

    @property
    def num_namespaces(self: GuiManager) -> int:
        return len(self._namespaces)

    def in_catalog(self: GuiManager, namespace: str) -> bool:
        return namespace in self._catalog

    def get_active_namespace(
        self: GuiManager,
    ) -> Optional[str]:
        if not self._namespaces:
            return None
        return self._namespaces[0]

    def activate_namespace(
        self: GuiManager,
        namespace: int,
    ) -> None:
        self.insert_namespace(
            namespace=namespace,
            position=0,
        )

    def insert_namespace(
        self: GuiManager,
        namespace: str,
        position: int,
    ) -> None:
        if namespace in self._namespaces:
            index = self._namespaces.index(namespace)
            self._namespaces.pop(index)
        # Validate position
        if not validate_position(position, self.num_namespaces - 1):
            position = fix_position(position, self.num_namespaces - 1)
        # Insert
        self._namespaces.insert(position, namespace)
        # Add page group
        if not self.in_catalog(namespace):
            self._catalog[namespace] = PageGroup(
                namespace=namespace,
            )

    def remove_namespace(
        self: GuiManager,
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
        self: GuiManager,
        namespace: str,
        page_args: List[Dict[str, str]],
        session_data: Dict[str, Any],
        position: int,
    ) -> None:
        if not self.in_catalog(namespace):
            self._catalog[namespace] = PageGroup(
                namespace=namespace,
            )
        prefix = self.namespace.replace('.', '_')
        for item in reversed(page_args):
            token = token_hex(4)
            self._catalog[namespace].insert_page(
                page_id=item.get("page", f"{prefix}_{token}"),
                uri=item.get("url"),
                session_data=session_data,
                position=position,
            )
        if set(self._namespaces) == {namespace}:
            self.show(namespace=namespace)

    def remove_pages(
        self: GuiManager,
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
                self.close(namespace, position)
            self._catalog[namespace].remove_page(position)

    def move_pages(
        self: GuiManager,
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
        self: GuiManager,
        namespace: str,
    ) -> Optional[str]:
        if not self.in_catalog(namespace):
            return None
        return self._catalog[namespace].get_active_page_id()

    def get_active_page(
        self: GuiManager,
        namespace: str,
    ) -> Optional[HTMLTag]:
        if not self.in_catalog(namespace):
            return None
        return self._catalog[namespace].get_active_page()

    def activate_page(
        self: GuiManager,
        namespace: str,
        id: Union[int, str],
    ) -> None:
        if not self.in_catalog(namespace):
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to move."
            )
            return
        self.activate_namespace(namespace=namespace)
        self._catalog[namespace].activate_page(id=id)

    def show(
        self: GuiManager,
        namespace: str,
        id: Union[str, int, None] = None,
    ) -> None:
        # Get page id
        if isinstance(id, int):
            page_id = self._catalog[namespace].get_page_id(id)
        else:
            page_id = id
        # Show page
        GuiManager.renderer.show(
            namespace=namespace,
            page_id=page_id,
        )

    def close(
        self: GuiManager,
        namespace: str,
        id: Union[str, int, None] = None,
    ) -> None:
        # Get page id
        if isinstance(id, int):
            page_id = self._catalog[namespace].get_page_id(id)
        else:
            page_id = id
        # Close page
        GuiManager.renderer.close(
            namespace=namespace,
            page_id=page_id,
        )

    def update_status(
        self: GuiManager,
        ovos_event: str,
        data: Optional[Dict[str, Any]],
    ) -> None:
        # Update status
        GuiManager.renderer.update_status(
            ovos_event=ovos_event,
            data=data,
        )

    def update_data(
        self: GuiManager,
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
        self: GuiManager,
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
