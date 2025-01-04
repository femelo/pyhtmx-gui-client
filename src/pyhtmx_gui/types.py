from typing import Any, List, Dict, Union, Optional, Callable, TypeVar
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from pyhtmx.html_tag import HTMLTag


class MessageType(str, Enum):
    GUI_CONNECTED = "mycroft.gui.connected"
    GUI_LIST_INSERT = "mycroft.gui.list.insert"
    GUI_LIST_MOVE = "mycroft.gui.list.move"
    GUI_LIST_REMOVE = "mycroft.gui.list.remove"
    EVENT_TRIGGERED = "mycroft.events.triggered"
    SESSION_SET = "mycroft.session.set"
    SESSION_DELETE = "mycroft.session.delete"
    SESSION_LIST_INSERT = "mycroft.session.list.insert"
    SESSION_LIST_UPDATE = "mycroft.session.list.update"
    SESSION_LIST_MOVE = "mycroft.session.list.move"
    SESSION_LIST_REMOVE = "mycroft.session.list.remove"


class EventType(str, Enum):
    WAKEWORD = "recognizer_loop:wakeword"
    RECORD_BEGIN = "recognizer_loop:record_begin"
    RECORD_END = "recognizer_loop:record_end"
    UTTERANCE = "recognizer_loop:utterance"
    UTTERANCE_HANDLED = "ovos.utterance.handled"
    UTTERANCE_CANCELLED = "ovos.utterance.cancelled"
    AUDIO_OUTPUT_START = "recognizer_loop:audio_output_start"
    AUDIO_OUTPUT_END = "recognizer_loop:audio_output_end"
    SKILL_HANDLER_START = "mycroft.skill.handler.start"
    SKILL_HANDLER_COMPLETE = "mycroft.skill.handler.complete"
    INTENT_FAILURE = "complete_intent_failure"
    PAGE_GAINED_FOCUS = "page_gained_focus"
    BLINK = "enclosure.eyes.blink"


class Message(BaseModel):
    model_config = ConfigDict(strict=False, populate_by_name=False)
    type: MessageType
    namespace: Optional[str] = None
    gui_id: Optional[str] = None
    framework: Optional[str] = None  # TODO: remove in the future
    property: Optional[str] = None
    position: Optional[int] = None
    from_position: Optional[int] = Field(alias="from", default=None)
    to_position: Optional[int] = Field(alias="to", default=None)
    items_number: Optional[int] = None
    event_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    values: Optional[List[Dict[str, Any]]] = None


class CallbackContext(str, Enum):
    LOCAL = "local"
    GLOBAL = "global"


class PageItem(str, Enum):
    DIALOG = "dialog"
    PARAMETER = "parameter"
    LOCAL_CALLBACK = "local_callback"
    GLOBAL_CALLBACK = "global_callback"


class Callback(BaseModel):
    model_config = ConfigDict(
        strict=False,
        arbitrary_types_allowed=True,
    )
    context: CallbackContext
    event_name: str
    event_id: str
    fn: Callable
    source: HTMLTag
    target: Optional[HTMLTag] = None
    target_level: str = "innerHTML"


class InteractionParameter(BaseModel):
    model_config = ConfigDict(
        strict=False,
        arbitrary_types_allowed=True,
    )
    parameter_name: str
    parameter_id: str
    target: HTMLTag


InputItem = TypeVar[HTMLTag, InteractionParameter, Callback]
OutputItem = TypeVar[HTMLTag, List[InteractionParameter], Callback]
