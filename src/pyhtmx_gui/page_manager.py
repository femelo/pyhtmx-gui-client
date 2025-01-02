from __future__ import annotations
from typing import Any, Type, Union, Optional, List, Dict, Callable
from pydantic import BaseModel, ConfigDict
from secrets import token_hex
from functools import partial
from .types import InteractionParameter, Callback, PageItem, CallbackContext
from .kit import Page
from .tools.utils import build_page
from .renderer import Renderer, global_renderer
from .logger import logger
from pyhtmx.html_tag import HTMLTag


class PageManagementInterface:
    renderer: Renderer = global_renderer

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
        target = target if target else PageManagementInterface.renderer._root
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

    @staticmethod
    def update_attributes(
        cls: PageManager,
        parameter: str,
        attribute: Dict[str, Any],
    ) -> None:
        parameter_list: Optional[
            List[InteractionParameter]
        ] = cls.get_item(
            item_type=PageItem.PARAMETER,
            key=parameter,
        )
        if not parameter_list:
            logger.warning(
                f"Parameter '{cls.page_id}::{parameter}' not registered."
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
                PageManagementInterface.renderer.update(
                    component.to_string(),
                    event_id=parameter_id,
                )
            else:
                PageManagementInterface.renderer.update(
                    text_content,
                    event_id=parameter_id,
                )

    @staticmethod
    def trigger_callback(
        cls: PageManager,
        context: CallbackContext,
        event_id: str
    ) -> Optional[Union[HTMLTag, str]]:
        # Retrieve callback
        callback = cls.get_item(
            item_type=(
                PageItem.LOCAL_CALLBACK
                if context == CallbackContext.LOCAL
                else PageItem.GLOBAL_CALLBACK
            ),
            key=event_id,
        )
        # Call and return content
        content: Optional[Union[HTMLTag, str]] = None
        if callback:
            content = callback.fn()
        return content

    @staticmethod
    def show(
        cls: PageManager,
    ) -> None:
        PageManagementInterface.renderer.show(
            cls.page_id,
            cls.page,
        )

    @staticmethod
    def close(
        cls: PageManager,
    ) -> None:
        PageManagementInterface.renderer.close(
            cls.page_id,
        )


class PageManager(BaseModel):
    model_config = ConfigDict(strict=False, arbitrary_types_allowed=True)
    page_group: Any
    page_id: str
    uri: str
    session_data: Dict[str, Any] = {}
    dialogs: Dict[str, HTMLTag] = {}
    parameters: Dict[str, List[InteractionParameter]] = {}
    global_callbacks: Dict[str, Callback] = {}
    local_callbacks: Dict[str, Callback] = {}
    _route: Optional[str] = None
    _page: Optional[Union[Page, HTMLTag]] = None
    _interface: Type[PageManagementInterface] = PageManagementInterface
    _item_map: Dict[
        PageItem,
        Union[HTMLTag, List[InteractionParameter], Callback]
    ] = {}

    @property
    def route(self: PageManager) -> str:
        return self._route

    @property
    def page(self: PageManager) -> HTMLTag:
        if isinstance(self._page, HTMLTag):
            return self._page
        elif hasattr(self._page, Page):
            return self._page.page
        else:
            pass

    def __getattr__(self: PageManager, name: str) -> Any:
        # Share interface methods with the manager
        if hasattr(self._interface, name):
            return partial(getattr(self._interface, name), self)
        return self[name]

    def model_post_init(self: PageManager, context: Any = None) -> None:
        self.build_page()
        self.set_route()
        self.post_set_up()
        self.init_item_map()

    def set_route(self: PageManager) -> None:
        if hasattr(self._page, "_route"):
            self._route = self._page.route
        else:
            self._route = f"/{self.page_id}"

    def build_page(self: PageManager) -> None:
        self._page = build_page(
            file_path=self.uri,
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
            self._page.set_up(self)

    def init_item_map(self: PageManager) -> None:
        self._item_map[PageItem.DIALOG] = self.dialogs
        self._item_map[PageItem.PARAMETER] = self.parameters
        self._item_map[PageItem.LOCAL_CALLBACK] = self.local_callbacks
        self._item_map[PageItem.GLOBAL_CALLBACK] = self.global_callbacks

    def set_item(
        self: PageManager,
        item_type: PageItem,
        key: str,
        value: Union[HTMLTag, InteractionParameter, Callback],
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
    ) -> Union[HTMLTag, List[InteractionParameter], Callback, None]:
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

    def navigate(
        self: PageManager,
        namespace: str,
        page_id: str,
    ) -> None:
        # Forward up navigation request to page group context
        self.page_group.navigate(
            namespace=namespace,
            page_id=page_id,
        )

    # TODO: is that the best option?
    def update_data(
        self: PageManager,
        session_data: Dict[str, Any],
    ) -> None:
        self._page.update_session_data(
            session_data=session_data,
            page_manager=self,
        )

    def update_state(
        self: PageManager,
        ovos_event: str,
    ) -> None:
        self._page.update_trigger_state(
            ovos_event=ovos_event,
            page_manager=self,
        )
