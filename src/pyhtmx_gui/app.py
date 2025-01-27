from __future__ import annotations
import os
from typing import Iterator, Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response, HTMLResponse, StreamingResponse
from copy import deepcopy
from time import time
from threading import Lock, Thread
from secrets import token_hex
from signal import signal, SIGINT, SIGTERM
import uvicorn
from urllib.parse import unquote
import json
from pyhtmx.html_tag import HTMLTag
from .config import config_data
from .types import DOMEvent, CallbackContext
from .renderer import global_renderer
from .logger import logger
from .event_sender import global_sender
from .gui_client import global_client, termination_event


APP_DIR = os.path.abspath(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(APP_DIR, "assets")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # After start
    logger.info("PyHTMX GUI started...")
    yield
    # Before finishing
    logger.info("PyHTMX GUI shutting down...")


# Instantiate application
app = FastAPI(lifespan=lifespan)

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Termination handler
def termination_handler(*args: Any) -> None:
    if not termination_event.is_set():
        logger.info("Terminating gently...")
        termination_event.set()
        global_client.close()
    else:
        os.kill(os.getpid(), SIGTERM)


# Set signal
signal(SIGINT, termination_handler)


# TODO: move this ping check somewhere else
sessions: Dict[str, int] = {}
session_lock = Lock()


def check_disconnected() -> None:
    wait_time: float = config_data["connection-check-wait"]
    ping_period: float = config_data["ping-period"]
    while not termination_event.wait(timeout=wait_time):
        now = time()
        disconnected = []
        for session_id, last_update in sessions.items():
            if now - last_update > ping_period + 3 * wait_time:
                global_client.deregister(session_id)
                disconnected.append(session_id)
                logger.info(f"Session closed: {session_id}")
        if disconnected:
            with session_lock:
                for session_id in disconnected:
                    del sessions[session_id]


Thread(target=check_disconnected, daemon=True).start()


@app.get("/updates")
async def updates() -> StreamingResponse:
    # Define message streaming generator
    def stream() -> Iterator[str]:
        messages = global_sender.listen()  # returns a queue.Queue
        while True:
            msg = messages.get()  # blocks until a new message arrives
            # logger.debug(f"Sending message:\n{msg}")
            yield msg
    return StreamingResponse(
        stream(),
        media_type="text/event-stream"
    )


@app.get("/local-event/{event_id}")
async def local_event(event_id: str, payload: str = Body(...)) -> HTMLResponse:
    # Parse event
    event: DOMEvent = DOMEvent(
        event_id=event_id,
        event_json=unquote(payload).replace('event=', '').replace('\n', ''),
    )
    logger.debug(f"Local event triggered: {event_id}")
    # Run callback
    component: HTMLTag = global_client._gui_manager.trigger_callback(
        context=CallbackContext.LOCAL,
        event_id=event_id,
        event=event,
    )
    return HTMLResponse(component.to_string())


@app.post("/global-event/{event_id}")
async def global_event(event_id: str, payload: str = Body(...)) -> Response:
    # Parse event
    event: DOMEvent = DOMEvent(
        event_id=event_id,
        event_json=unquote(payload).replace('event=', '').replace('\n', ''),
    )
    logger.debug(f"Global event triggered: {event_id}")
    # Run callback
    global_client._gui_manager.trigger_callback(
        context=CallbackContext.GLOBAL,
        event_id=event_id,
        event=event,
    )
    return Response(status_code=204)


@app.post("/ping/{session_id}")
async def ping(session_id: str) -> Response:
    # logger.debug(f"Received a ping from: {session_id}")
    now = time()
    with session_lock:
        sessions[session_id] = now
    return Response(status_code=204)


@app.get("/")
async def root() -> HTMLResponse:
    session_id = token_hex(4)
    document = deepcopy(global_renderer.document)
    session_element = document.find_element_by_id("session-id")
    if session_element:
        session_element.update_attributes(
            text_content=session_id,
            attributes={
                "hx-post": f"/ping/{session_id}"
            },
        )
    global_client.register(session_id)
    logger.info(f"Session opened: {session_id}. Displaying page.")
    return HTMLResponse(document.to_string())


def run(
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> None:
    # Launch app
    uvicorn.run(
        app,
        host=host or config_data["server-host"],
        port=port or config_data["server-port"],
        log_level="warning",  # set log level to warning
    )


if __name__ == "__main__":
    run()
