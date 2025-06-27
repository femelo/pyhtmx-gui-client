import os
from typing import Optional, Union, Dict, List, Any
import importlib
import inspect
import re
from PIL import ImageFont
from .kit import Page
from .logger import logger
from pyhtmx.html_tag import HTMLTag


MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(MODULE_DIR, "assets", "fonts")

DEC_DOT_REGEX: re.Pattern = re.compile(r"(?<=\d)[.,](?=\d)")


def build_page(
    file_path: str,
    module_name: str = "page",
    session_data: Optional[Dict[str, Any]] = None,
) -> Union[HTMLTag, Page]:
    # Load module
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    # sys.modules[module_name] = module
    spec.loader.exec_module(module)
    objects = []
    # Get relevant objects
    object_names = filter(
        lambda name: (
            not name.startswith("__")
            and hasattr(getattr(module, name), "__module__")
            and getattr(module, name).__module__ == module_name
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
        elif (
            inspect.isclass(obj) and
            hasattr(obj, "_is_page") and
            obj._is_page
        ):
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
            logger.warning(
                f"Multiple pages defined on {file_path}. "
                "Using the first object found."
            )
        page_object = objects[0]
        if inspect.isclass(page_object):
            page_instance = page_object(session_data=session_data)
        else:
            page_instance = page_object
        logger.debug(f"Object {page_instance} built.")
    return page_instance


def validate_position(position: int, ub: int) -> bool:
    valid = 0 <= position <= ub
    if not valid:
        logger.warning("Provided position out of range.")
    return valid


def fix_position(position: int, ub: int) -> int:
    logger.info("Position set to nearest bound.")
    return max(min(position, ub), 0)


def calculate_text_width(
    text: str,
    font_name: str = "helvetica",
    font_size: int = 24
) -> int:
    font = ImageFont.truetype(os.path.join(ASSETS_DIR, font_name), font_size)
    size = font.getlength(text)
    return round(size + 0.5)


def format_utterance(utterance: Union[str, List[str]]) -> str:
    if isinstance(utterance, list):
        utterance_sentences: List[str] = list(
            map(
                lambda x: DEC_DOT_REGEX.sub(',', x).strip().strip('.').strip(),
                filter(bool, utterance),
            ),
        )
    else:
        utterance_sentences: List[str] = list(
            map(
                str.strip,
                filter(bool, DEC_DOT_REGEX.sub(',', utterance).strip().split('.')),
            )
        )
    formatted_utterance: str = DEC_DOT_REGEX.sub('.', ". ".join(utterance_sentences))
    last_char: str = formatted_utterance[-1] if format_utterance else ''
    if last_char not in list('.:,;?!-'):
        formatted_utterance += '.'
    formatted_utterance += ' '
    return formatted_utterance
