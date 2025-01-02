from __future__ import annotations
from typing import Any, Union, Optional, List, Dict
from pydantic import BaseModel, ConfigDict
from pyhtmx.html_tag import HTMLTag
from .types import InteractionParameter, Callback, PageItem
from .page_manager import PageManager
from .logger import logger


class PageGroup(BaseModel):
    model_config = ConfigDict(strict=False, arbitrary_types_allowed=True)
    gui_manager: Any
    namespace: str
    ids: List[str] = []
    pages: Dict[str, PageManager] = {}

    def validate_position(
        self: PageGroup,
        position: int,
    ) -> bool:
        length = len(self.ids)
        valid = abs(position) <= length
        if not valid:
            logger.warning("Provided position out of range.")
        return valid

    def fix_position(self: PageGroup, position: int) -> int:
        length = len(self.ids)
        logger.info("Position set to nearest bound.")
        return max(min(position, length), -length)

    def insert_page(
        self: PageGroup,
        page_id: str,
        uri: str,
        session_data: Dict[str, Any],
        position: int,
    ) -> None:
        if page_id not in self.ids:
            if not self.validate_position(position):
                position = self.fix_position(position)
            self.ids.insert(position, page_id)
        else:
            index = self.ids.index(page_id)
            if index != position:
                page_id = self.ids.pop(index)
                if not self.validate_position(position):
                    position = self.fix_position(position)
                self.ids.insert(position, page_id)
            logger.info(
                f"Manager for page '{page_id}' already exists. "
                f"Manager will be updated."
            )
        self.pages[page_id] = PageManager(
            page_group=self,
            page_id=page_id,
            uri=uri,
            session_data=session_data,
        )

    def get_page_id(self: PageGroup, position: int) -> Optional[str]:
        if not self.validate_position(position + 1):
            return None
        return self.ids[position]

    def get_page(self: PageGroup, page_id: str) -> Optional[HTMLTag]:
        page_items = self.pages.get(page_id, None)
        if not page_items:
            logger.warning(
                f"Page '{page_id}' not in page group '{self.namespace}'. "
                f"Page not retrieved."
            )
            return
        return page_items.page

    def remove_page(
        self: PageGroup,
        id: Union[int, str],
    ) -> None:
        if isinstance(id, int):
            page_id = self.get_page_id(id)
        else:
            page_id = id
        if page_id in self.page_ids:
            self.page_ids.remove(page_id)
            del self.pages[page_id]
        else:
            logger.warning(
                f"Item collection for page '{page_id}' does not exist. "
                f"Nothing to remove."
            )

    def move_page(
        self: PageGroup,
        id: Union[int, str],
        to_position: int,
    ) -> None:
        if isinstance(id, str):
            from_position = self.get_page_id(id)
            invalid_position = from_position is None
        else:
            from_position = id
            invalid_position = not self.validate_position(from_position + 1)
        if invalid_position:
            logger.warning(
                f"Item collection for page '{id}' does not exist. "
                f"Nothing to move."
            )
            return
        if not self.validate_position(to_position):
            to_position = self.fix_position(to_position)
        # Switch position
        item = self.page_ids.pop(from_position)
        self.page_ids.insert(to_position - 1, item)

    def add_to_page(
        self: PageGroup,
        page_id: str,
        item_type: PageItem,
        key: str,
        value: Union[HTMLTag, InteractionParameter, Callback],
    ) -> None:
        page_items = self.pages.get(page_id, None)
        if not page_items:
            logger.warning(
                f"Page '{page_id}' not in page group '{self.namespace}'. "
                f"Pair ({key}, {value}) not added."
            )
            return
        page_items.set_item(item_type=item_type, key=key, value=value)

    def get_from_page(
        self: PageGroup,
        page_id: str,
        item_type: PageItem,
        key: str,
    ) -> Union[HTMLTag, List[InteractionParameter], Callback, None]:
        page_items = self.pages.get(page_id, None)
        if not page_items:
            logger.warning(
                f"Page '{page_id}' not in page group '{self.namespace}'. "
                f"Value for '{key}' not retrieved."
            )
            return
        return page_items.get_item(item_type=item_type, key=key)

    def navigate(
        self: PageGroup,
        namespace: str,
        page_id: str,
    ) -> None:
        # Forward up navigation request to GUI manager context
        self.gui_manager.navigate(
            namespace=namespace,
            page_id=page_id,
        )

    def show(
        self: PageGroup,
        page_id: str,
    ) -> None:
        page_items = self.pages.get(page_id, None)
        if not page_items:
            logger.warning(
                f"Page '{page_id}' not in page group '{self.namespace}'. "
                f"Nothing to show."
            )
            return
        page_items.show()

    def close(
        self: PageGroup,
        page_id: str,
    ) -> None:
        page_items = self.pages.get(page_id, None)
        if not page_items:
            logger.warning(
                f"Page '{page_id}' not in page group '{self.namespace}'. "
                f"Nothing to close."
            )
            return
        page_items.close()

    def update_data(
        self: PageGroup,
        session_data: Dict[str, Any],
    ) -> None:
        for page_items in self.pages.values():
            page_items.update_data(session_data)

    def update_state(
        self: PageGroup,
        ovos_event: str,
    ) -> None:
        for page_items in self.pages.values():
            page_items.update_state(ovos_event)
