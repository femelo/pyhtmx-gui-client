from __future__ import annotations
from typing import Any, Union, Optional, List, Dict
from pydantic import BaseModel, ConfigDict
from pyhtmx.html_tag import HTMLTag
from .types import InteractionParameter, Callback, PageItem
from .tools.utils import validate_position, fix_position
from .page_manager import PageManager
from .logger import logger


class PageGroup(BaseModel):
    model_config = ConfigDict(strict=False, arbitrary_types_allowed=True)
    namespace: str
    page_ids: List[str] = []
    pages: Dict[str, PageManager] = {}
    active_index: Optional[int] = None

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
            page_id=page_id,
            uri=uri,
            session_data=session_data,
        )

    @property
    def num_pages(self: PageGroup) -> int:
        return len(self.page_ids)

    def get_page_id(self: PageGroup, position: int) -> Optional[str]:
        if not validate_position(position, 0, self.num_pages - 1):
            return None
        return self.page_ids[position]

    def get_page(self: PageGroup, page_id: str) -> Optional[HTMLTag]:
        page_items = self.pages.get(page_id, None)
        if not page_items:
            logger.warning(
                f"Page '{page_id}' not in page group '{self.namespace}'. "
                f"Page not retrieved."
            )
            return
        return page_items.page

    def get_active_page_id(self: PageGroup) -> Optional[str]:
        if self.active_index:
            return self.get_page_id(self.active_index)
        return None

    def get_active_page(self: PageGroup) -> Optional[HTMLTag]:
        if self.active_index:
            active_page_id = self.get_page_id(self.active_index)
            return self.get_page(active_page_id)
        return None

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
            invalid_position = not validate_position(
                from_position, 0, self.num_pages - 1
            )
        if invalid_position:
            logger.warning(
                f"Item collection for page '{id}' does not exist. "
                f"Nothing to move."
            )
            return
        if not validate_position(to_position, 0, self.num_pages):
            to_position = fix_position(to_position, 0, self.num_pages)
        # Switch position
        item = self.page_ids.pop(from_position)
        self.page_ids.insert(to_position, item)

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
