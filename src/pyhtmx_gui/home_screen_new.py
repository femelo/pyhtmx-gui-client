from __future__ import annotations
import os
import shutil
from typing import Any, Optional, Dict
from threading import Thread, Condition
from datetime import datetime
import time
from pyhtmx import Div
from pyhtmx_gui.kit import Page, SessionItem


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Background image
WALLPAPER = (
    "https://cdn.pixabay.com/photo/2016/06/02/02/33/"
    "triangles-1430105_1280.png"
)


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


class HomeScreen(Page):
    _parameters = ("clock-time", "wallpaper")
    _clock: Clock = global_clock

    def __init__(
        self: HomeScreen,
        session_data: Optional[Dict[str, Any]],
    ):
        super().__init__(name="home", session_data=session_data)

        # Clock text
        clock_text: Div = Div(
            _id="clock-time",
            _class="text-9xl text-white font-bold",
        )
        # Overlay container
        overlay: Div = Div(
            clock_text,
            _id="wallpaper",
            _class=[
                "p-[20px]",
                "flex",
                "grow",
                "flex-col",
                "justify-start",
                "items-end",
                "bg-cover",
            ],
            style=self.wallpaper_url(),
        )

        self.add_interaction(
            "clock-time",
            SessionItem(
                parameter="clock-time",
                attribute="inner_content",
                component=clock_text,
            ),
        )
        self.add_interaction(
            "wallpaper",
            SessionItem(
                parameter="wallpaper",
                attribute="_class",
                component=overlay,
                format_value=self.wallpaper_url,
            ),
        )

        # Main view
        self._page: Div = Div(
            overlay,
            _id="home",
            _class="flex flex-col h-screen",
        )

    def wallpaper_url(
        self: HomeScreen,
        value: Any = None,
    ) -> str:
        wallpaper_path = self._session_data.get("wallpaper_path", '')
        selected_wallpaper = self._session_data.get("selected_wallpaper", '')
        if wallpaper_path and selected_wallpaper:
            # Hack to workaround the way figures are served
            shutil.copy(
                os.path.join(wallpaper_path, selected_wallpaper),
                os.path.join(BASE_DIR, "assets", "images"),
            )
        if not wallpaper_path or not selected_wallpaper:
            wallpaper_url = WALLPAPER
        else:
            wallpaper_url = os.path.join(
                "assets",
                "images",
                selected_wallpaper
            )
        return f"background-image: url({wallpaper_url});"

    def set_up(self: HomeScreen, page_manager: Any) -> None:
        super().set_up(page_manager)

        # Update time
        def update_time():
            while HomeScreen._clock.wait():
                page_manager.update_attributes(
                    namespace=self.namespace,
                    page_id=self.page_id,
                    parameter="clock-time",
                    attribute={"inner_content": HomeScreen._clock.time},
                )
        # Start thread
        Thread(target=update_time, daemon=True).start()
