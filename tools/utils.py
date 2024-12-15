from typing import Optional, Dict, Any
import importlib
import inspect
from pyhtmx.html_tag import HTMLTag


def build_page(
    file_path: str,
    session_data: Optional[Dict[str, Any]] = None
) -> Any:
    # Load module
    spec = importlib.util.spec_from_file_location("page", file_path)
    module = importlib.util.module_from_spec(spec)
    # sys.modules[self.name] = module
    spec.loader.exec_module(module)
    objects = []
    # Get relevant objects
    object_names = filter(
        lambda name: (
            not name.startswith("__")
            and hasattr(getattr(module, name), "__module__")
            and getattr(module, name).__module__ == "page"
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
            f"No page view defined on '{file_path}'. "
            "Make sure wrapping classes have the class "
            "attribute _is_page = True"
        )
    else:    
        if len(objects) > 1:
            print(
                f"Multiple page views defined on {file_path}. "
                "Using the first object found."
            )
        page_object = objects[0]
        if inspect.isclass(page_object):
            page_object = page_object(session_data=session_data)
        print(f"Object {page_object} built.")
    return page_object
