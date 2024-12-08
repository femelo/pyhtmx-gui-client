from __future__ import annotations
from typing import Mapping, Dict, List, Optional, Union, Any
from flet import Page  # TODO: remove me
from enum import Enum
from threading import Thread
from websocket import WebSocket, create_connection
from pydantic import BaseModel, ConfigDict, Field
from renderer import Renderer, global_renderer
from gui_management import GuiList


class MessageType(str, Enum):
    GUI_CONNECTED = "mycroft.gui.connected"
    GUI_LIST_INSERT = "mycroft.gui.list.insert"
    GUI_LIST_MOVE = "mycroft.gui.list.move"
    GUI_LIST_REMOVE = "mycroft.gui.list.remove"
    EVENT_TRIGGERED = "mycroft.events.triggered"
    SESSION_SET = "mycroft.session.set"
    SESSION_DELETE = "mycroft.session.delete"
    SESSION_LIST_INSERT = "mycroft.session.list.insert"
    SESSION_LIST_UPDATE = "mycroft.session.list.insert"
    SESSION_LIST_MOVE = "mycroft.session.list.move"
    SESSION_LIST_REMOVE = "mycroft.session.list.remove"


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


class OVOSGuiClient:
    id : str = "ovos-gui-flet-client"
    server_url : str = "ws://localhost:18181/gui"
    renderer: Renderer = global_renderer

    def __init__(self: OVOSGuiClient):
        self._ws: Optional[WebSocket] = OVOSGuiClient.connect()
        self._component_map: Mapping[str, Any] = {}
        self._thread: Optional[Thread] = self.listen()
        self._session: Dict[str, Any] = {}
        self._active_skills: List[str] = []
        self._gui_list: Dict[str, List[Dict[str, str]]] = {}
        self.announce()

    @property
    def page(self: OVOSGuiClient) -> Page:
        return self._page

    @page.setter
    def page(self: OVOSGuiClient, value: Page) -> None:
        self._page = value

    @property
    def component_map(self: OVOSGuiClient) -> Mapping[str, Any]:
        return self._component_map

    @component_map.setter
    def component_map(self: OVOSGuiClient, value: Mapping[str, Any]) -> None:
        self._component_map = value

    # Connect to OVOS-GUI WebSocket
    @staticmethod
    def connect() -> Optional[WebSocket]:
        try:
            ws = create_connection(OVOSGuiClient.server_url)  # Use the correct host, port, and route
            print("Connected to ovos-gui websocket")
            return ws
        except Exception as e:
            print(f"Error connecting to ovos-gui: {e}")
            return None

    def announce(self: OVOSGuiClient) -> None:
        if self._ws:
            message = Message(
                type=MessageType.GUI_CONNECTED,
                gui_id=OVOSGuiClient.id,
                # TODO: force framework in the message root,
                # though the bus code must be changed.
                framework="py-flet",
                data={"framework": "py-flet"}
            )
            self._ws.send(message.model_dump_json(exclude_none=True))

    def listen(self: OVOSGuiClient) -> Thread:
        if self._ws:
            thread = Thread(target=self.receive_message, daemon=True)
            thread.start()
            return thread
        else:
            return None

    # Receive message from GUI web socket
    def receive_message(self: OVOSGuiClient):
        while True:
            try:
                response = self._ws.recv()  # Receive messages from the WebSocket
                if response:
                    print("Received message: ", response)
                    message = Message.model_validate_json(response)
                    self.process_message(message)
            except Exception as e:
               print(f"Error receiving message: {e}")

    # General processing of GUI messages
    def process_message(self: OVOSGuiClient, message: Message) -> None:
        if message.type == MessageType.GUI_LIST_INSERT:
            self.handle_gui_list_insert(
                message.namespace,
                message.position,
                message.data,
                message.values,
            )
        elif message.type == MessageType.GUI_LIST_MOVE:
            self.handle_gui_list_move(
                message.namespace,
                message.from_position,
                message.to_position,
                message.items_number,
            )
        elif message.type == MessageType.GUI_LIST_REMOVE:
            self.handle_gui_list_remove(
                message.namespace,
                message.position,
                message.items_number,
            )
        elif message.type == MessageType.EVENT_TRIGGERED:
            self.handle_event_triggered(
                message.namespace,
                message.event_name,
                message.data,
            )
        elif message.type == MessageType.SESSION_SET:
            self.handle_session_set(
                message.namespace,
                message.data,
            )
        elif message.type == MessageType.SESSION_DELETE:
            self.handle_session_delete(
                message.namespace,
                message.property,
            )
        elif message.type == MessageType.SESSION_LIST_INSERT:
            self.handle_session_list_insert(
                message.namespace,
                message.position,
                message.property,
                message.data,
                message.values,
            )
        elif message.type == MessageType.SESSION_LIST_UPDATE:
            self.handle_session_list_update()
        elif message.type == MessageType.SESSION_LIST_MOVE:
            self.handle_session_list_move()
        elif message.type == MessageType.SESSION_LIST_REMOVE:
            self.handle_session_list_remove(
                message.namespace,
                message.position,
                message.items_number,
            )
        else:
            print(f"No handler defined for this message: {message}")

    def handle_gui_list_insert(
        self: OVOSGuiClient,
        namespace: str,
        position: Optional[int] = None,
        data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        values: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if namespace == "skill-ovos-date-time.openvoiceos":  # ovos-date-time
            # TODO: implement me
            pass
        else:
            if namespace == "skill-ovos-homescreen.openvoiceos":
                # Force local home screen
                # TODO: change actual homescreen skill
                data = [{"url": "home_screen.py", "page": "home_screen"}]

            show = len(self._gui_list) == 0

            if namespace not in self._gui_list:
                self._gui_list[namespace] = GuiList(
                    namespace=namespace,
                    renderer=OVOSGuiClient.renderer,
                )

            if position is None:
                position = 0

            if namespace in self._session:
                session_data = self._session[namespace]
            else:
                session_data = {}

            self._gui_list[namespace].insert(
                position=position,
                values=values if values is not None else data,
                session_data=session_data,
            )
            if show:
                self._gui_list[namespace].show(position)

    def handle_gui_list_move(
        self: OVOSGuiClient,
        namespace: str,
        from_pos: int,
        to_pos: int,
        items_number: int,
    ) -> None:
        if namespace not in self._gui_list:
            self._gui_list[namespace].move(
                from_pos=from_pos,
                to_pos=to_pos,
                items_number=items_number,
            )

    def handle_gui_list_remove(
        self: OVOSGuiClient,
        namespace: str,
        position: int,
        items_number: int,
    ) -> None:
        if namespace not in self._gui_list:
            self._gui_list[namespace].remove(
                position=position,
                items_number=items_number,
            )

    def handle_event_triggered(
        self: OVOSGuiClient,
        namespace: str,
        event_name: str,
        parameters: Mapping[str, Any],
     ) -> None:
        # General event handlers can be added here
        if event_name == "page_gained_focus":
            page_index = parameters.get("number", 0)
            print(f"Focus shifted to view {page_index}")
            if namespace in self._gui_list:
                self._gui_list[namespace].show(page_index)
                # self.send_focus_event(
                #     namespace=namespace,
                #     index=page_index,
                # )

    def handle_session_set(
        self: OVOSGuiClient,
        namespace: str,
        session_data: Mapping[str, Any],
    ) -> None:
        if namespace not in self._session:
            self._session[namespace] = {}
        self._session[namespace].update(session_data)
        if namespace in self._gui_list:
            self._gui_list[namespace].update(session_data)

    def handle_session_delete(
        self: OVOSGuiClient,
        namespace: str,
        property: str,
    ) -> None:
        if (namespace in self._session) and (property in self._session[namespace]):
            del self._session[namespace][property]

    def handle_session_list_insert(
        self: OVOSGuiClient,
        namespace: str,
        position: Optional[int],
        property: Optional[str],
        data: Optional[Mapping[str, Any]],
        values: Optional[List[Mapping[str, Any]]],
        ) -> None:
        if namespace == "mycroft.system.active_skills":
            skill = data[0].get("skill_id", None)
            if skill:
                self._active_skills.insert(position, skill)
        else:
            if namespace not in self._session:
                self._session[namespace] = {}
            if position is None:
                position = 0
            if property is not None and property not in self._session[namespace]:
                self._session[namespace][property] = [None for _ in range(position)]
            for item in reversed(values):
                self._session[namespace][property].insert(position, item)


    def handle_session_list_update(self: OVOSGuiClient) -> None:
        # TODO: Implement me
        pass

    def handle_session_list_move(self: OVOSGuiClient) -> None:
        # TODO: Implement me
        pass

    def handle_session_list_remove(
        self: OVOSGuiClient,
        namespace: str,
        position: int,
        items_number: int,
    ) -> None:
        if namespace == "mycroft.system.active_skills":
            if position < len(self._active_skills):
                del self._active_skills[position]
        else:
            # TODO: what should go here?
            pass

    # Send an event to OVOS-GUI
    def send_focus_event(
        self: OVOSGuiClient,
        namespace: str,
        index: int
    ) -> None:
        if self._ws:
            message = Message(
                type=MessageType.EVENT_TRIGGERED,
                namespace=namespace,
                event_name="page_gained_focus",
                data={"number": index}
            )
            self._ws.send(message.model_dump_json())

    # Function to show the Home screen
    # TODO: example, remove this.
    def show_home(self: OVOSGuiClient):
        namespace = "homescreen"
        position = 0
        values = [{"url": "home_screen.py", "page": "home_screen"}]
        self.handle_gui_list_insert(
            namespace=namespace,
            position=position,
            data=None,
            values=values,
        )
        self.handle_event_triggered(
            namespace=namespace,
            event_name="page_gained_focus",
            parameters={"number": 0},
        )

global_client = OVOSGuiClient()
