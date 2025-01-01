from __future__ import annotations
import os
import gc
from typing import Mapping, Dict, List, Optional, Union, Any
from threading import Thread, Event
from time import sleep
import traceback
from websocket import WebSocket, create_connection
from .logger import logger
from .types import MessageType, EventType, Message
from .renderer import Renderer, global_renderer
from .gui_management import GuiList


CLIENT_DIR = os.path.abspath(os.path.dirname(__file__))


# Termination event
termination_event: Event = Event()


class OVOSGuiClient:
    # TODO: move id and server_url to config/config.toml
    id: str = "ovos-pyhtmx-gui-client"
    server_url: str = "ws://localhost:18181/gui"
    renderer: Renderer = global_renderer

    def __init__(self: OVOSGuiClient):
        self._ws: Optional[WebSocket] = OVOSGuiClient.connect()
        self._thread: Optional[Thread] = self.listen()
        self._session: Dict[str, Any] = {}
        self._active_skills: List[str] = []
        self._gui_list: Dict[str, GuiList] = {}
        self.announce()

    # Connect to OVOS-GUI WebSocket
    @staticmethod
    def connect() -> Optional[WebSocket]:
        try:
            ws = create_connection(OVOSGuiClient.server_url)
            logger.info("Connected to ovos-gui websocket")
            return ws
        except Exception as e:
            logger.error(f"Error connecting to ovos-gui: {e}")
            return None

    def announce(self: OVOSGuiClient) -> None:
        if self._ws:
            message = Message(
                type=MessageType.GUI_CONNECTED,
                gui_id=OVOSGuiClient.id,
                # TODO: force framework in the message root,
                # though the bus code must be changed.
                framework="py-htmx",
                data={"framework": "py-htmx"},
            )
            self._ws.send(message.model_dump_json(exclude_none=True))

    def register(self: OVOSGuiClient, client_id: str) -> None:
        self.renderer.register_client(client_id)

    def deregister(self: OVOSGuiClient, client_id: str) -> None:
        self.renderer.deregister(client_id)

    def listen(self: OVOSGuiClient) -> Thread:
        if self._ws:
            thread = Thread(target=self.receive_message, daemon=True)
            thread.start()
            return thread
        else:
            return None

    def close(self: OVOSGuiClient) -> Thread:
        if self._ws:
            sleep(0.1)
            self._ws.close()
        logger.info("Closed connection with ovos-gui websocket.")

    # Receive message from GUI web socket
    def receive_message(self: OVOSGuiClient):
        while not termination_event.is_set():
            try:
                if self._ws:
                    response = self._ws.recv()
                if response:
                    logger.debug(f"Received message: {response}")
                    message = Message.model_validate_json(response)
                    self.process_message(message)
            except Exception:
                exception_data = traceback.format_exc(limit=50)
                logger.error(f"Error processing message:\n{exception_data}")

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
                message.property,
                message.items_number,
            )
        else:
            logger.warning(f"No handler defined for this message: {message}")

    def handle_gui_list_insert(
        self: OVOSGuiClient,
        namespace: str,
        position: Optional[int] = None,
        data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        values: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if namespace == "skill-ovos-homescreen.openvoiceos":
            # Force local home screen
            # TODO: change actual homescreen skill
            data = [
                {
                    "url": os.path.join(CLIENT_DIR, "home_screen_carousel.py"),
                    "page": "home_screen",
                },
            ]

        data = [data] if isinstance(data, dict) else data
        show = len(self._gui_list) == 0

        if namespace not in self._gui_list:
            self._gui_list[namespace] = GuiList(
                namespace=namespace,
                renderer=OVOSGuiClient.renderer,
            )

        position = position or 0
        values = values or data or []
        session_data = self._session.get(namespace, {})

        self._gui_list[namespace].insert(
            position=position,
            values=values,
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
        if namespace in self._gui_list:
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
        if namespace in self._gui_list:
            self._gui_list[namespace].remove(
                position=position,
                items_number=items_number,
            )
        gc.collect()

    def handle_event_triggered(
        self: OVOSGuiClient,
        namespace: str,
        event_name: str,
        parameters: Mapping[str, Any],
     ) -> None:
        if event_name == EventType.PAGE_GAINED_FOCUS:
            # Page gained focus: display it
            page_index = parameters.get("number", 0)
            if namespace in self._gui_list:
                self._gui_list[namespace].show(page_index)
        elif namespace == "system" and event_name in set(EventType):
            # Handle OVOS system event
            utterance: Optional[str] = parameters.get("utterance", None)
            if utterance:
                data = {"utterance": utterance}
            elif event_name in (EventType.RECORD_END, ):
                data = {"utterance": " "}
            else:
                data = None
            OVOSGuiClient.renderer.update_status(
                ovos_event=event_name,
                data=data,
            )
        else:
            # Handle general event
            if namespace in self._gui_list:
                self._gui_list[namespace].update_state(event_name)

    def handle_session_set(
        self: OVOSGuiClient,
        namespace: str,
        session_data: Mapping[str, Any],
    ) -> None:
        if namespace not in self._session:
            self._session[namespace] = {}
        self._session[namespace].update(session_data)
        if namespace in self._gui_list:
            self._gui_list[namespace].update_data(session_data)

    def handle_session_delete(
        self: OVOSGuiClient,
        namespace: str,
        property: str,
    ) -> None:
        # NOTE: Session parameters are destroyed in the renderer upon
        # destroying the associated page
        if (
            namespace in self._session and
            property in self._session[namespace]
        ):
            del self._session[namespace][property]
        gc.collect()

    def handle_session_list_insert(
        self: OVOSGuiClient,
        namespace: str,
        position: Optional[int],
        property: Optional[str],
        data: Optional[Mapping[str, Any]],
        values: Optional[List[Mapping[str, Any]]],
    ) -> None:
        if namespace == "mycroft.system.active_skills":
            skill = data[0].get("skill_id", None) if data else None
            if skill:
                self._active_skills.insert(position, skill)
        else:
            if namespace not in self._session:
                self._session[namespace] = session_data = {}
            if position is None:
                position = 0
            if property:
                session_data[property] = [
                    None for _ in range(position)
                ]
            for item in reversed(values):
                session_data[property].insert(position, item)
            if namespace in self._gui_list:
                self._gui_list[namespace].update_data(session_data)

    def handle_session_list_update(self: OVOSGuiClient) -> None:
        # TODO: Implement me
        pass

    def handle_session_list_move(self: OVOSGuiClient) -> None:
        # TODO: Implement me
        pass

    def handle_session_list_remove(
        self: OVOSGuiClient,
        namespace: str,
        position: Optional[int],
        property: Optional[str],
        items_number: Optional[int],
    ) -> None:
        if position is None:
            position = 0
        if namespace == "mycroft.system.active_skills":
            if position < len(self._active_skills):
                skill_id = self._active_skills.pop(position)
                if skill_id in self._gui_list:
                    self._gui_list[skill_id].close(position)
        else:
            session_data = self._session.get(namespace, {})
            if property is not None and property in session_data:
                del session_data[property]

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
                data={"number": index},
            )
            self._ws.send(message.model_dump_json())


global_client = OVOSGuiClient()
