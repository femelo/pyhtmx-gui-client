from __future__ import annotations
from typing import Any, Union, Optional, List, Dict
from pydantic import BaseModel, ConfigDict
from secrets import token_hex
from .renderer import Renderer, global_renderer
from .page_group import PageGroup
from .logger import logger


class GuiManager(BaseModel):
    model_config = ConfigDict(strict=False, arbitrary_types_allowed=True)
    _active_namespace: List[str] = []
    _active_page: List[Optional[str]] = []
    _catalog: Dict[str, PageGroup] = {}
    _renderer: Renderer = global_renderer

    def is_active_page(
        self: GuiManager,
        namespace: str,
        page_id: Optional[str] = None,
    ) -> bool:
        return (
            namespace == self._active_namespace[0] and
            page_id == self._active_page[0]
        )

    def update_active_page(
        self: GuiManager,
        namespace: str,
        page_id: Optional[str] = None,
        position: int = 0,
    ) -> None:
        if namespace in self._active_namespace:
            index = self._active_namespace.index(namespace)
            self._active_namespace.pop(index)
            self._active_page.pop(index)
        # Validate position
        length = len(self._active_namespace)
        if abs(position) > length:
            position = max(min(position, length), -length)
        # Insert
        self._active_namespace.insert(position, namespace)
        self._active_page.insert(position, page_id)

    def remove_active_page(
        self: GuiManager,
        namespace: Optional[str] = None,
        page_id: Optional[str] = None,
    ) -> None:
        if namespace and namespace in self._active_namespace:
            index = self._active_namespace.index(namespace)
        elif page_id and page_id in self._active_page:
            index = self._active_page.index(page_id)
        else:
            return
        self._active_namespace.pop(index)
        self._active_page.pop(index)

    def insert_namespace(
        self: GuiManager,
        namespace: str,
        position: int,
    ) -> None:
        # Add page group
        if namespace not in self._catalog:
            self._catalog[namespace] = PageGroup(
                gui_manager=self,
                namespace=namespace,
            )
        self.update_active_page(namespace=namespace, position=position)

    def remove_namespace(
        self: GuiManager,
        namespace: str,
        position: int,
    ) -> None:
        if namespace not in self._active_namespace:
            logger.info(
                f"Namespace '{namespace}' no longer active. "
                "Nothing to remove."
            )
            return
        # Remove namespace
        self.remove_active_page(namespace=namespace)
        # Remove from catalog
        if namespace in self._catalog:
            del self._catalog[namespace]

    def insert(
        self: GuiManager,
        namespace: str,
        page_args: List[Dict[str, str]],
        session_data: Dict[str, Any],
        position: int,
    ) -> None:
        if namespace not in self._catalog:
            self._catalog[namespace] = PageGroup(
                gui_manager=self,
                namespace=namespace,
            )
        else:
            logger.info(
                f"Page group for '{namespace}' already exists. "
                "Page group will be updated."
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

    def remove(
        self: GuiManager,
        namespace: str,
        position: int,
        items_number: int = 1,
    ) -> None:
        if namespace not in self._catalog:
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to remove."
            )
            return
        # Remove pages
        for _ in range(items_number):
            page_id = self._catalog[namespace].get_page_id(position)
            if self.is_active_page(namespace, page_id):
                self.close(namespace, page_id)
            self._catalog[namespace].remove_page(position)

    def move(
        self: GuiManager,
        namespace: str,
        from_position: int,
        to_position: int,
        items_number: int = 1,
    ) -> None:
        if namespace not in self._catalog:
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

    def navigate(
        self: GuiManager,
        namespace: str,
        id: Union[str, int],
    ) -> None:
        self.show(namespace=namespace, id=id)

    def show(
        self: GuiManager,
        namespace: str,
        id: Union[str, int],
    ) -> None:
        if namespace not in self._catalog:
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to show."
            )
            return
        # Get page id
        if isinstance(id, int):
            page_id = self._catalog[namespace].get_page_id(id)
        else:
            page_id = id
        # Show page
        if page_id in self.page_ids:
            self.update_active_page(namespace=namespace, page_id=page_id)
            self._catalog[namespace].show(page_id)
        else:
            logger.warning(
                f"Page '{page_id}' not in group for '{namespace}'. "
                f"Nothing to show."
            )

    def close(
        self: GuiManager,
        namespace: str,
        id: Union[str, int],
    ) -> None:
        if namespace not in self._catalog:
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to show."
            )
            return
        # Get page id
        if isinstance(id, int):
            page_id = self._catalog[namespace].get_page_id(id)
        else:
            page_id = id
        # Close page
        if page_id in self.page_ids:
            self._catalog[namespace].close(page_id)
            self.remove_active_page(namespace=namespace, page_id=page_id)
        else:
            logger.warning(
                f"Page '{page_id}' not in group for '{namespace}'. "
                f"Nothing to close."
            )

    def update_data(
        self: GuiManager,
        namespace: str,
        session_data: Dict[str, Any],
    ) -> None:
        if namespace not in self._catalog:
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to update."
            )
            return
        # Update data
        self._catalog[namespace].update_data(session_data)

    def update_state(
        self: GuiManager,
        namespace: str,
        event: str,
    ) -> None:
        if namespace not in self._catalog:
            logger.warning(
                f"Page group for '{namespace}' not in catalog. "
                "Nothing to update."
            )
            return
        # Update event
        self._catalog[namespace].update_state(event)
