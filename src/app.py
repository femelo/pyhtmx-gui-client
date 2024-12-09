from __future__ import annotations
from typing import AsyncIterator
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
import json, uvicorn
from event_sender import global_sender
from ovos_gui_client import global_client


app = FastAPI("PyHTMX GUI Client")


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
    return FileResponse('index.html')
