from __future__ import annotations
import os
import typer
import json
from typing import Optional, Any
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
import uvicorn
from pyhtmx import HTMLTag
from .dummy_document import DUMMY_DOCUMENT
from ..utils import build_page


BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
app = FastAPI()


app.mount(
    "/assets",
    StaticFiles(
        directory=os.path.join(BASE_DIR, "src", "assets"),
    ),
    name="assets",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

page: Optional[Any] = None


@app.get("/")
async def root() -> HTMLResponse:
    global page
    document: HTMLTag = DUMMY_DOCUMENT
    root_div = document.find_element_by_id(_id="root")
    root_div.add_child(page)  # type: ignore
    return HTMLResponse(document.to_string())


def main(file_path: str, session_data: Optional[str] = None) -> None:
    global page
    if not os.path.exists(file_path):
        IOError(f"'{file_path}' not found.")

    page_object = build_page(
        file_path,
        session_data=json.loads(session_data) if session_data else {},
    )
    page = page_object.page  # type: ignore
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        use_colors=True,
    )


if __name__ == "__main__":
    typer.run(main)
