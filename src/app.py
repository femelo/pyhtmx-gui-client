from __future__ import annotations
from typing import AsyncIterator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
import json, uvicorn
from renderer import global_renderer
from event_sender import global_sender
from ovos_gui_client import global_client


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/event-source')
async def event_source() -> StreamingResponse:
    # Define message streaming generator
    async def stream() -> AsyncIterator[str]:
        messages = global_sender.listen()  # returns a queue.Queue
        while True:
            msg = messages.get()  # blocks until a new message arrives
            yield msg
    return StreamingResponse(
        stream(),
        media_type="text/event-stream"
    )


@app.get("/")
async def root():
    global_client.register("1")
    return HTMLResponse(global_renderer.document)
