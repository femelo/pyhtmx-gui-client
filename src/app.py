from __future__ import annotations
from typing import Iterator, Dict, Any
from fastapi import Body, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response, HTMLResponse, StreamingResponse
from copy import deepcopy
from time import time, sleep
from threading import Lock, Thread
from secrets import token_hex
from renderer import global_renderer
from event_sender import global_sender
from ovos_gui_client import global_client


app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: move this ping check somewhere else
sessions: Dict[str, int] = {}
session_lock = Lock()


def check_disconnected() -> None:
    while True:
        now = time()
        disconnected = []
        for session_id, last_update in sessions.items():
            if now - last_update > 3:
                global_client.deregister(session_id)
                disconnected.append(session_id)
                print(f"Session closed: {session_id}")
        if disconnected:
            with session_lock:
                for session_id in disconnected:
                    del sessions[session_id]
        sleep(0.5)


Thread(target=check_disconnected, daemon=True).start()


@app.get("/updates")
async def updates() -> StreamingResponse:
    # Define message streaming generator
    def stream() -> Iterator[str]:
        messages = global_sender.listen()  # returns a queue.Queue
        while True:
            msg = messages.get()  # blocks until a new message arrives
            # print(f"Sending message:\n{msg}")
            yield msg
    return StreamingResponse(
        stream(),
        media_type="text/event-stream"
    )


@app.post("/ping")
async def ping(payload: Any = Body(None)) -> Response:
    _, session_id = payload.decode().split("=")
    # print(f"Received a ping from: {session_id}")
    now = time()
    with session_lock:
        sessions[session_id] = now
    return Response()


@app.get("/")
async def root():
    session_id = token_hex(4)
    document = deepcopy(global_renderer.document)
    session_element = document.find_element_by_id("session-id")
    if session_element:
        session_element.update_attributes(
            text_content=session_id,
            attributes={
                "hx-vals": f"{{\"session-id\": \"{session_id}\"}}"
            },
        )
    global_client.register(session_id)
    print(f"Session opened: {session_id}")
    return HTMLResponse(document.to_string())
