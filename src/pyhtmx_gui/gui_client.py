from __future__ import annotations
import os
import gc
from typing import Mapping, Dict, List, Optional, Union, Any
from threading import Thread, Event
from time import sleep
import traceback
from websocket import WebSocket, create_connection
from .logger import logger
from .config import config_data
from .types import MessageType, EventType, Message
# from .utils import format_utterance
from .gui_manager import GUIManager
from .status_handler import StatusHandler


CLIENT_DIR = os.path.abspath(os.path.dirname(__file__))


# Termination event
termination_event: Event = Event()


class GUIClient:
    id: str = config_data.get(
        "client-id",
        "pyhtmx-gui-client",
    )

    def __init__(self: GUIClient):
        self.server_url: str = config_data.get(
            "ovos-server-url",
            "ws://localhost:18181/gui",
        )
        self._ws: Optional[WebSocket] = self.connect()
        self._thread: Optional[Thread] = self.listen()
        self._active_skills: List[str] = []
        self._session: Dict[str, Any] = {}
        self._gui_manager: GUIManager = GUIManager()
        self._gui_manager.set_gui_client(self)
        self._status_handler: StatusHandler = StatusHandler(
            self._gui_manager.update_status
        )
        self.announce()

    # Connect to OVOS-GUI WebSocket
    def connect(self: GUIClient) -> Optional[WebSocket]:
        try:
            ws = create_connection(self.server_url)
            logger.info("Connected to ovos-gui websocket")
            return ws
        except Exception as e:
            logger.error(f"Error connecting to ovos-gui: {e}")
            return None

    def announce(self: GUIClient) -> None:
        if self._ws:
            message = Message(
                type=MessageType.GUI_CONNECTED,
                gui_id=GUIClient.id,
                # TODO: force framework in the message root,
                # though the bus code must be changed.
                framework="py-htmx",
                data={"framework": "py-htmx"},
            )
            self._ws.send(message.model_dump_json(exclude_none=True))

    def register(self: GUIClient, client_id: str) -> None:
        self._gui_manager.renderer.register_client(client_id)

    def deregister(self: GUIClient, client_id: str) -> None:
        self._gui_manager.renderer.deregister(client_id)

    def listen(self: GUIClient) -> Thread:
        if self._ws:
            thread = Thread(target=self.receive_message, daemon=True)
            thread.start()
            return thread
        else:
            return None

    def close(self: GUIClient) -> Thread:
        if self._ws:
            sleep(0.1)
            self._ws.close()
        logger.info("Closed connection with ovos-gui websocket.")

    # Receive message from GUI web socket
    def receive_message(self: GUIClient):
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
    def process_message(self: GUIClient, message: Message) -> None:
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
        self: GUIClient,
        namespace: str,
        position: Optional[int] = None,
        data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        values: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if namespace == "ovos-skill-homescreen.openvoiceos":
            # Force local home screen
            # TODO: change actual homescreen skill
            data = [
                {
                    "url": os.path.join(CLIENT_DIR, "home_screen_carousel.py"),
                    "page": "home_screen",
                },
            ]

        data = [data] if isinstance(data, dict) else data

        position = position or 0
        page_args = values or data or []
        session_data = self._session.get(namespace, {})

        self._gui_manager.insert_pages(
            namespace=namespace,
            position=position,
            page_args=page_args,
            session_data=session_data,
        )

    def handle_gui_list_move(
        self: GUIClient,
        namespace: str,
        from_pos: int,
        to_pos: int,
        items_number: int,
    ) -> None:
        self._gui_manager.move_pages(
            namespace=namespace,
            from_pos=from_pos,
            to_pos=to_pos,
            items_number=items_number,
        )

    def handle_gui_list_remove(
        self: GUIClient,
        namespace: str,
        position: int,
        items_number: int,
    ) -> None:
        self._gui_manager.remove_pages(
            namespace=namespace,
            position=position,
            items_number=items_number,
        )
        gc.collect()

    def handle_event_triggered(
        self: GUIClient,
        namespace: str,
        event_name: str,
        parameters: Mapping[str, Any],
     ) -> None:
        if event_name == EventType.PAGE_GAINED_FOCUS:
            # Page gained focus: display it
            page_index = parameters.get("number", 0)
            self._gui_manager.show(
                namespace=namespace,
                id=page_index,
            )
        elif namespace == "system" and event_name in set(EventType):
            # Handle OVOS system event
            self._status_handler.process_event(
                event_name=event_name,
                event_data=parameters,
            )
        else:
            # Handle general event
            self._gui_manager.update_state(
                namespace=namespace,
                ovos_event=event_name,
            )

    def handle_session_set(
        self: GUIClient,
        namespace: str,
        session_data: Mapping[str, Any],
    ) -> None:
        if namespace not in self._session:
            self._session[namespace] = {}
        self._session[namespace].update(session_data)
        self._gui_manager.update_data(
            namespace=namespace,
            session_data=session_data,
        )

    def handle_session_delete(
        self: GUIClient,
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
        self: GUIClient,
        namespace: str,
        position: Optional[int],
        property: Optional[str],
        data: Optional[Mapping[str, Any]],
        values: Optional[List[Mapping[str, Any]]],
    ) -> None:
        if namespace == "mycroft.system.active_skills":
            skill = data[0].get("skill_id", None) if data else None
            self._active_skills.insert(0, skill)
            if skill:
                self._gui_manager.insert_namespace(
                    namespace=skill,
                    position=position,
                )
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
            self._gui_manager.update_data(
                namespace=namespace,
                session_data=session_data,
            )

    def handle_session_list_update(self: GUIClient) -> None:
        # TODO: Implement me
        pass

    def handle_session_list_move(self: GUIClient) -> None:
        # TODO: Implement me
        pass

    def handle_session_list_remove(
        self: GUIClient,
        namespace: str,
        position: Optional[int],
        property: Optional[str],
        items_number: Optional[int],
    ) -> None:
        if position is None:
            position = 0
        if namespace == "mycroft.system.active_skills":
            try:
                skill: str = self._active_skills.pop(position)
                self._gui_manager.remove_namespace(namespace=skill)
            except IndexError:
                pass
        else:
            session_data = self._session.get(namespace, {})
            if property is not None and property in session_data:
                del session_data[property]

    # Send an event to OVOS-GUI
    def send_event(
        self: GUIClient,
        namespace: str,
        event_name: EventType,
        data: Dict[str, Any],
    ) -> None:
        if self._ws:
            message = Message(
                type=MessageType.EVENT_TRIGGERED,
                namespace=namespace,
                event_name=event_name,
                data=data,
            )
            self._ws.send(message.model_dump_json())

    # Send an event to OVOS-GUI
    def send_focus_event(
        self: GUIClient,
        namespace: str,
        index: int
    ) -> None:
        self.send_event(
            namespace=namespace,
            event_name=EventType.PAGE_GAINED_FOCUS,
            data={"number": index},
        )


global_client = GUIClient()
