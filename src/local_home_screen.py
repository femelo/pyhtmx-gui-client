from __future__ import annotations
from typing import Any, Optional, Dict
from threading import Thread, Condition
from datetime import datetime
import time
from flet import (
    Text,
    FontWeight,
    Container,
    ImageFit,
    Column,
    CrossAxisAlignment,
    alignment,
    Stack,
    View,
)


# Background image
WALLPAPER = "https://cdn.pixabay.com/photo/2016/06/02/02/33/triangles-1430105_1280.png?text=Achtergrond+1"


class Clock:
    def __init__(self: Clock):
        self._time: Optional[str] = None
        self._condition: Condition = Condition()
        self._quit: bool = False
        self._thread: Thread = Thread(target=self.tick, daemon=True).start()

    def __del__(self: Clock) -> None:
        self._quit = True
        time.sleep(1)
        self._thread.join()

    @property
    def time(self: Clock) -> Optional[str]:
        return self._time

    @time.setter
    def time(self: Clock, value: Optional[str]) -> None:
        self._time = time

    @property
    def condition(self: Clock) -> Condition:
        return self._condition

    def wait(self: Clock, timeout: Optional[float] = None) -> bool:
        self._condition.acquire()
        return self._condition.wait(timeout=timeout)

    def tick(self: Clock) -> None:
        while not self._quit:
            self._time = datetime.now().strftime("%H:%M:%S")
            self.condition.acquire()
            self._condition.notify_all()
            self._condition.release()
            time.sleep(1)


# Global clock
global_clock = Clock()


class HomeScreen:
    _is_page: bool = True  # required class attribute for correct loading
    _clock: Clock = global_clock

    def __init__(
        self: HomeScreen,
        session_data: Optional[Dict[str, Any]],
    ):
        self._session_data: Dict[str, Any] = {
            "wallpaper": WALLPAPER,
        }
        if session_data:
            self._session_data.update(session_data)
        self._clock_text: Text = Text(
            key="clock-time",
            size=150,
            color="white",
            weight=FontWeight.BOLD
        )
        # Background settings
        self._background_container = Container(
            key="wallpaper",
            expand=True,
            image_src=self._session_data["wallpaper"],
            image_fit=ImageFit.COVER,
        )
        self._overlay = Container(
            content=Column(
                [
                    self._clock_text,
                ],
                horizontal_alignment=CrossAxisAlignment.END,
                spacing=10,
            ),
            padding=20,
            alignment=alignment.Alignment(1, -1),
        )
        self._view = View(
            "/home",
            controls=[
                Stack([self._background_container, self._overlay], expand=True),
            ],
        )

    @property
    def page(self: HomeScreen) -> View:
        return self._view

    def update_session_data(
        self: HomeScreen,
        session_data: Dict[str, Any],
        renderer: Any
    ) -> None:
        self._session_data.update(session_data)
        image_src = self._session_data["wallpaper"]
        renderer.update_attributes(
            route="/home",
            key="wallpaper",
            attributes={"image_src": image_src},
        )

    def set(self: HomeScreen, renderer: Any) -> None:
        # Update time
        def update_time():
            while HomeScreen._clock.wait():
                renderer.update_attributes(
                    route="/home",
                    key="clock-time",
                    attributes={"value": HomeScreen._clock.time},
                )

        Thread(target=update_time, daemon=True).start()
