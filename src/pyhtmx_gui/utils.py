import os
from typing import Any, Dict, List, Optional, Tuple, Union
import importlib
import importlib.util
import inspect
import re
from PIL import ImageFont
from .kit import Page
from .logger import logger
from pyhtmx.html_tag import HTMLTag
from math import exp, log
from functools import partial


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
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_name} from file '{file_path}'")
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


def calculate_duration(text: str) -> float:
    return 2.0 * (1.0 - exp(log(0.75) * len(text) / 10))


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
    if not formatted_utterance:
        return ""
    last_char: str = formatted_utterance[-1]
    if last_char and last_char not in list('.:,;?!-'):
        formatted_utterance += '.'
    return formatted_utterance[0].upper() + formatted_utterance[1:]


def split_utterance(utterance: str, max_length: Optional[int]) -> List[str]:
    if not utterance:
        return []
    if max_length is None or len(utterance) <= max_length:
        last_char = utterance[-1]
        if last_char and last_char not in list('.:,;?!-'):
            utterance += '.'
        return [utterance + ' ']
    split_groups: List[str] = []
    length: int = 0
    add_len: int = 0
    word_group: str = ""
    for word in utterance.split():
        add_len = (1 if word_group else 0) + len(word)
        if length + add_len <= max_length:
            if word_group:
                word_group += " "
            word_group += word
            length += add_len
        else:
            split_groups.append(word_group + ' ')
            word_group = word
            length = len(word)
    if word_group:
        last_char = word_group[-1]
        if last_char and last_char not in list('.:,;?!-'):
            word_group += '.'
        split_groups.append(word_group + ' ')
    return split_groups


def generate_split_utterance(utterance: str, duration: float, max_length: Optional[int] = 60) -> List[Tuple[str, float]]:
    utterance_sentences: List[str] = split_utterance(utterance, max_length=max_length)
    utt_length = sum(len(s) for s in utterance_sentences)
    utterance_durations: List[float] = list(
        map(lambda x: duration * len(x) / utt_length, utterance_sentences)
    )
    return list(zip(utterance_sentences, utterance_durations))
