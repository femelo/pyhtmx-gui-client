from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, Dict
from threading import Thread, Condition
from datetime import datetime
import time
from pyhtmx.html_tag import HTMLTag
from pyhtmx import Div, Span


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


# TODO: move this to 'types.py'
@dataclass
class SessionData:
    parameter: str
    attribute: str
    component: HTMLTag
    value_format: Optional[str] = None


class HomeScreen:
    _clock: Clock = global_clock

    def __init__(
        self: HomeScreen,
        session_data: Optional[Dict[str, Any]],
    ):
        self._route = "/home"
        self._session_objects: Dict[str, Optional[SessionData]] = {
            "clock-time": None,
            "wallpaper": None,
        }
        # Clock text
        clock_text: Div = Div(
            Span(
                content=session_data.get("clock-time"),
                _id="clock-time",
                _class="text-9xl text-white font-bold",
            ),
        )
        # Overlay container
        wallpaper = session_data.get("wallpaper") 
        overlay: Div = Div(
            clock_text,
            _id="wallpaper",
            _class=' '.join(
                [
                    "p-[20px]",
                    "flex",
                    "grow",
                    "flex-col",
                    "justify-start",
                    "content-end",
                    f"bg-[url({wallpaper})]" if wallpaper else "",
                ]
            )
        )

        self._session_objects["clock-time"] = SessionData(
            parameter="clock-time",
            attribute="content",
            component=clock_text,
        )
        self._session_objects["wallpaper"] = SessionData(
            parameter="wallpaper",
            attribute="_class",
            component=overlay,
            value_format="bg-[url({})]",
        )

        # Main view
        self._page: Div = Div(
            overlay,
            _id="home",
            _class="flex grow",
        )

    @property
    def page(self: HomeScreen) -> HTMLTag:
        return self._page

    def update_session_data(
        self: HomeScreen,
        parameter: str,
        attribute: Dict[str, Any],
        renderer: Any
    ) -> None:
        renderer.update_attributes(
            route="/home",
            parameter=parameter,
            attribute=attribute,
        )

    def set_up(self: HomeScreen, renderer: Any) -> None:
        # Register session parameters
        for parameter, session_object in self._session_objects.keys():
            renderer.register_session_parameter(
                route=self._route,
                parameter=parameter,
                target=session_object.component
            )
        # Update time
        def update_time():
            while HomeScreen._clock.wait():
                renderer.update_attributes(
                    route="/home",
                    parameter="clock-time",
                    attribute={"content": HomeScreen._clock.time},
                )
        # Start thread
        Thread(target=update_time, daemon=True).start()
