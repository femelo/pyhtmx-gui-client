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

    @property
    def num_pages(self: PageGroup) -> int:
        return len(self.page_ids)

    def insert_page(
        self: PageGroup,
        page_id: str,
        uri: str,
        session_data: Dict[str, Any],
        position: int,
    ) -> None:
        if page_id not in self.page_ids:
            if not validate_position(position, self.num_pages - 1):
                position = self.fix_position(position)
            self.ids.insert(position, page_id)
        else:
            index = self.ids.index(page_id)
            if index != position:
                page_id = self.ids.pop(index)
                if not validate_position(position, self.num_pages - 1):
                    position = fix_position(position, self.num_pages - 1)
                self.ids.insert(position, page_id)
            logger.info(
                f"Page '{page_id}' already exists. "
                f"Page manager will be updated."
            )
        self.pages[page_id] = PageManager(
            page_id=page_id,
            uri=uri,
            session_data=session_data,
        )

    def get_page_id(self: PageGroup, position: int) -> Optional[str]:
        if not validate_position(position, self.num_pages - 1):
            return None
        return self.page_ids[position]

    def get_page(self: PageGroup, page_id: str) -> Optional[Any]:
        page_items = self.pages.get(page_id, None)
        if not page_items:
            logger.warning(
                f"Page '{page_id}' not in page group '{self.namespace}'. "
                f"Page not retrieved."
            )
            return
        return page_items.page

    def get_page_tag(self: PageGroup, page_id: str) -> Optional[HTMLTag]:
        page_items = self.pages.get(page_id, None)
        if not page_items:
            logger.warning(
                f"Page '{page_id}' not in page group '{self.namespace}'. "
                f"Page not retrieved."
            )
            return
        return page_items.page_tag

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
                f"Page '{page_id}' does not exist. "
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
                from_position, self.num_pages - 1
            )
        if invalid_position:
            logger.warning(
                f"Page '{id}' does not exist. "
                f"Nothing to move."
            )
            return
        if not validate_position(to_position, self.num_pages):
            to_position = fix_position(to_position, self.num_pages)
        # Switch position
        item = self.page_ids.pop(from_position)
        self.page_ids.insert(to_position, item)

    def activate_page(self: PageGroup, id: Union[int, str]) -> None:
        if isinstance(id, int) and validate_position(id, self.num_pages - 1):
            self.active_index = id
        elif isinstance(id, str) and id in self.page_ids:
            self.active_index = self.page_ids.index(id)
        else:
            logger.warning(
                f"Page '{id}' does not exist. "
                f"Nothing to activate."
            )

    def get_active_page_id(self: PageGroup) -> Optional[str]:
        if self.active_index:
            return self.get_page_id(self.active_index)
        return None

    def get_active_page(self: PageGroup) -> Optional[HTMLTag]:
        if self.active_index:
            active_page_id = self.get_page_id(self.active_index)
            return self.get_page(active_page_id)
        return None

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

    def update_data(
        self: PageGroup,
        page_id: str,
        session_data: Dict[str, Any],
    ) -> None:
        page_items = self.pages.get(page_id, None)
        if not page_items:
            logger.warning(
                f"Page '{page_id}' not in page group '{self.namespace}'. "
                f"Nothing to update."
            )
            return
        page_object = page_items.page
        if hasattr(page_object, "update_session_data"):
            page_object.update_session_data(
                session_data=session_data,
                page_manager=self,
            )

    def update_state(
        self: PageGroup,
        page_id: str,
        ovos_event: str,
    ) -> None:
        page_items = self.pages.get(page_id, None)
        if not page_items:
            logger.warning(
                f"Page '{page_id}' not in page group '{self.namespace}'. "
                f"Nothing to update."
            )
            return
        page_object = page_items.page
        if hasattr(page_object, "update_trigger_state"):
            page_object.update_trigger_state(
                ovos_event=ovos_event,
                page_manager=self,
            )
