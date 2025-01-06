from __future__ import annotations
from typing import Any, Type, Union, Optional, List, Dict, Callable
from secrets import token_hex
from functools import partial
from .types import (
    InteractionParameter,
    Callback,
    PageItem,
    CallbackContext,
    InputItem,
    OutputItem,
)
from .kit import Page
from .utils import build_page
from .logger import logger
from pyhtmx.html_tag import HTMLTag


class PageRegistrationInterface:
    @staticmethod
    def register_interaction_parameter(
        cls: PageManager,
        parameter: str,
        target: HTMLTag,
        target_level: Optional[str] = "innerHTML",
    ) -> None:
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
        cls.set_item(
            item_type=PageItem.PARAMETER,
            key=parameter,
            value=interaction_parameter,
        )

    @staticmethod
    def register_callback(
        cls: PageManager,
        event: str,
        context: Union[str, CallbackContext],
        fn: Callable,
        source: HTMLTag,
        target: Optional[HTMLTag] = None,
        target_level: str = "innerHTML",
    ) -> None:
        # Set root container if target was not specified
        target = target if target else cls.renderer._root
        # Set new id
        _id: str = token_hex(4)
        event_id = '-'.join([*event.split(), _id])
        if context == CallbackContext.LOCAL:
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
            item_type = PageItem.LOCAL_CALLBACK
        elif context == CallbackContext.GLOBAL:
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
            item_type = PageItem.GLOBAL_CALLBACK
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
        cls.set_item(
            item_type=item_type,
            key=event_id,
            value=callback,
        )

    @staticmethod
    def register_dialog(
        cls: PageManager,
        dialog_id: str,
        dialog_content: HTMLTag,
    ) -> None:
        # Register callback
        cls.set_item(
            item_type=PageItem.DIALOG,
            key=dialog_id,
            value=dialog_content,
        )


class PageManager:
    def __init__(
        self: PageManager,
        namespace: str,
        page_id: str,
        page_src: Union[str, Page, HTMLTag],
        renderer: Any,  # type: Renderer
        session_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.namespace: str = namespace
        self.page_id: str = page_id
        self.page_src: Union[str, Page, HTMLTag] = page_src
        self.renderer: Any = renderer
        self.session_data: Dict[str, Any] = session_data or {}
        self.route: Optional[str] = None
        self._interface: Type[PageRegistrationInterface] \
            = PageRegistrationInterface
        self._dialogs: Dict[str, HTMLTag] = {}
        self._parameters: Dict[str, List[InteractionParameter]] = {}
        self._global_callbacks: Dict[str, Callback] = {}
        self._local_callbacks: Dict[str, Callback] = {}
        self._page: Optional[Union[Page, HTMLTag]] = None
        self._item_map: Dict[PageItem, OutputItem] = {}
        self.model_post_init()

    @property
    def page(self: PageManager) -> Any:
        return self._page

    @property
    def page_tag(self: PageManager) -> HTMLTag:
        if isinstance(self._page, HTMLTag):
            return self._page
        elif isinstance(self._page, Page):
            return self._page.page
        else:
            pass

    def __getattr__(self: PageManager, name: str) -> Any:
        # Borrow methods from page registration interface and renderer
        if hasattr(self._interface, name):
            return partial(getattr(self._interface, name), self)
        if hasattr(self.renderer, name):
            return getattr(self.renderer, name)
        else:
            return self[name]

    def model_post_init(self: PageManager, context: Any = None) -> None:
        self.set_item_map()
        self.build_page()
        self.set_route()
        self.post_set_up()

    def set_route(self: PageManager) -> None:
        if hasattr(self._page, "_route"):
            self.route = self._page.route
        else:
            self.route = f"/{self.page_id}"

    def build_page(self: PageManager) -> None:
        if isinstance(self.page_src, (Page, HTMLTag)):
            self._page = self.page_src
        else:
            self._page = build_page(
                file_path=self.page_src,
                module_name=self.page_id,
                session_data=self.session_data,
            )

    def post_set_up(self: PageManager) -> None:
        if self._page is None:
            logger.warning(
                f"Page '{self.page_id}' not built. "
                "Nothing to setup."
            )
            return
        if hasattr(self._page, "set_up"):
            self._page.set_up(page_manager=self)

    def set_item_map(self: PageManager) -> None:
        self._item_map[PageItem.DIALOG] = self._dialogs
        self._item_map[PageItem.PARAMETER] = self._parameters
        self._item_map[PageItem.LOCAL_CALLBACK] = self._local_callbacks
        self._item_map[PageItem.GLOBAL_CALLBACK] = self._global_callbacks

    def set_item(
        self: PageManager,
        item_type: PageItem,
        key: str,
        value: InputItem,
    ) -> None:
        item = self._item_map.get(item_type, None)
        if item is None:
            logger.warning(
                f"Unknown page group item: {item_type}. "
                f"Pair ({key}, {value}) not set."
            )
            return
        if item_type == PageItem.PARAMETER:
            if key not in item:
                item[key] = []
            item[key].append(value)
        else:
            item[key] = value

    def get_item(
        self: PageManager,
        item_type: PageItem,
        key: str
    ) -> Optional[OutputItem]:
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

    def update_data(
        self: PageManager,
        session_data: Dict[str, Any],
    ) -> None:
        if hasattr(self._page, "update_session_data"):
            self._page.update_session_data(
                session_data=session_data,
                renderer=self.renderer,
            )

    def update_state(
        self: PageManager,
        ovos_event: str,
    ) -> None:
        if hasattr(self._page, "update_trigger_state"):
            self._page.update_trigger_state(
                ovos_event=ovos_event,
                renderer=self.renderer,
            )
