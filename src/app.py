from __future__ import annotations
from typing import Iterator
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, StreamingResponse
# import json, uvicorn
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


@app.get('/updates')
async def updates() -> StreamingResponse:
    # Define message streaming generator
    def stream() -> Iterator[str]:
        messages = global_sender.listen()  # returns a queue.Queue
        while True:
            msg = messages.get()  # blocks until a new message arrives
            print(f"Sending message:\n{msg}")
            yield msg
    return StreamingResponse(
        stream(),
        media_type="text/event-stream"
    )


@app.get("/")
async def root():
    global_client.register("1")
    return HTMLResponse(global_renderer.document)
