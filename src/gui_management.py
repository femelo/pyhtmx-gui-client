from __future__ import annotations
# import sys
from typing import Any, Union, Optional, List, Dict
from pydantic import BaseModel, ConfigDict
from pyhtmx.html_tag import HTMLTag
from renderer import Renderer
import secrets
import inspect
import importlib.util
from logger import logger


class PageLoader(BaseModel):
    model_config = ConfigDict(strict=False, arbitrary_types_allowed=True)
    name: str
    uri: str
    session_data: Dict[str, Any] = {}
    renderer: Renderer
    _page_object: Optional[Any] = None

    @property
    def page_object(self: PageLoader) -> Any:
        return self._page_object

    @property
    def route(self: PageLoader) -> Union[HTMLTag, None]:
        if isinstance(self._page_object, HTMLTag):
            return f"/{secrets.token_hex(4)}"
        elif hasattr(self._page_object, "_route"):
            return self._page_object._route
        else:
            return f"/{secrets.token_hex(4)}"

    @property
    def page(self: PageLoader) -> Union[HTMLTag, None]:
        if isinstance(self._page_object, HTMLTag):
            return self._page_object
        elif hasattr(self._page_object, "_page"):
            return self._page_object._page
        else:
            return None

    def build(self: PageLoader) -> None:
        # Load module
        spec = importlib.util.spec_from_file_location(self.name, self.uri)
        module = importlib.util.module_from_spec(spec)
        # sys.modules[self.name] = module
        spec.loader.exec_module(module)
        objects = []
        # Get relevant objects
        object_names = filter(
            lambda name: (
                not name.startswith("__")
                and hasattr(getattr(module, name), "__module__")
                and getattr(module, name).__module__ == self.name
            ),
            dir(module),
        )
        # Save just views or wrappers with class attribute '_is_page'
        for obj_name in object_names:
            obj = getattr(module, obj_name)
            if isinstance(obj, HTMLTag):
                objects.append(obj)
            elif inspect.isclass(obj) and HTMLTag in obj.__bases__:
                objects.append(obj)
            elif inspect.isclass(obj) and hasattr(obj, "_is_page") and obj._is_page:
                objects.append(obj)
            else:
                pass

        # No objects found
        if len(objects) == 0:
            raise IOError(
                f"No page view defined on '{self.uri}'. "
                "Make sure wrapping classes have the class "
                "attribute _is_page = True"
            )
        else:    
            if len(objects) > 1:
                logger.warning(
                    f"Multiple page views defined on {self.uri}. "
                    "Using the first object found."
                )
            page_object = objects[0]
            if inspect.isclass(page_object):
                self._page_object = page_object(session_data=self.session_data)
            else:
                self._page_object = page_object
            logger.debug(f"Object {self._page_object} built.")
            if hasattr(page_object, "set_up"):
                self._page_object.set_up(self.renderer)

    def update(self: PageLoader, session_data: Dict[str, Any]) -> None:
        self.session_data.update(session_data)
        # NOTE: this method is assumed as implemented
        self._page_object.update_session_data(session_data, self.renderer)

    def show(self: PageLoader) -> None:
        if self._page_object is None:
            self.build()
        self.renderer.show(
            self.route,
            self.page,
        )

    def close(self: PageLoader) -> None:
        if self._page_object:
            self.renderer.close(
                self.route,
            )


class GuiList(BaseModel):
    model_config = ConfigDict(strict=False, arbitrary_types_allowed=True)
    namespace: Optional[str]
    renderer: Renderer
    _shown_page: int = 0
    _pages: List[PageLoader] = []

    def insert(
        self: GuiList,
        position: int,
        values: List[Dict[str, str]],
        session_data: Dict[str, Any],
    ) -> None:
        position = min(position, len(self._pages))
        prefix = self.namespace.replace('.', '_')
        for item in reversed(values):
            token = secrets.token_hex(4)
            self._pages.insert(
                position,
                PageLoader(
                    name=item.get("page", f"{prefix}_{token}"),
                    uri=item.get("url"),
                    session_data=session_data,
                    renderer=self.renderer,
                )
            )

    def move(
        self: GuiList,
        from_pos: int,
        to_pos: int,
        items_number: int = 1,
    ) -> None:
        from_pos = min(from_pos, len(self._pages) - 1)
        to_pos = min(to_pos, len(self._pages))
        for _ in range(items_number):
            item = self._pages.pop(from_pos)
            self._pages.insert(to_pos + 1, item)

    def remove(
        self: GuiList,
        position: int,
        items_number: int = 1,
    ) -> None:
        position = min(position, len(self._pages))
        for _ in range(items_number):
            if position < len(self._pages):
                del self._pages[position]

    def get_page(self: GuiList, position: int) -> Optional[PageLoader]:
        if 0 <= position < len(self._pages):
            return self._pages[position]
        return None

    def show(
        self: GuiList,
        position: int,
    ) -> None:
        if 0 <= position < len(self._pages):
            self._pages[position].show()
            self._shown_page = position

    def close(
        self: GuiList,
        position: int,
    ) -> None:
        if 0 <= position < len(self._pages):
            self._pages[position].close()
            self._shown_page = -1  # TODO: think about this logic

    def update(
        self: GuiList,
        session_data: Dict[str, Any],
    ) -> None:
        if self._shown_page > len(self._pages):
            logger.warning("Last shown page out of range.")
            return
        page_object = self._pages[self._shown_page].page_object
        if page_object is None:
            logger.warning("Unable to update a page that has not been built.")
            return
        valid_session_data = {}
        for key in session_data.keys():
            if key in page_object._session_data:
                valid_session_data[key] = session_data[key]
        if valid_session_data:
            page_object.update_session_data(
                session_data=valid_session_data,
                renderer=self.renderer,
            )
