from __future__ import annotations
import shutil
import os
from typing import Any, Optional, Dict
from functools import partial
from flet import (
    BottomAppBar,
    colors,
    Text,
    TextField,
    FontWeight,
    Container,
    IconButton,
    Icon,
    icons,
    Image,
    ImageFit,
    Row,
    Column,
    CrossAxisAlignment,
    MainAxisAlignment,
    alignment,
    Stack,
    View,
    padding,
    NavigationDrawer,
    RoundedRectangleBorder,
    ControlEvent,
    BottomSheet,
)

# Background image
WALLPAPER = "https://cdn.pixabay.com/photo/2016/06/02/02/33/triangles-1430105_1280.png"
# Version text
VERSION_TEXT = """
OpenVoiceOS - Flet GUI Version: 1.0.0
"""
# License text
LICENSE_URL = "https://www.apache.org/licenses/LICENSE-2.0"
LICENSE_TEXT = (
    "\nLicensed under the Apache License, Version 2.0 (the 'License'); "
    "you may not use this file except in compliance with the License.\n"
    f"You may obtain a copy of the License at {LICENSE_URL}.\n\n"
    "Unless required by applicable law or agreed to in writing, software distributed under "
    "the License is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF "
    "ANY KIND, either express or implied.\n\n"
    "See the License for the specific language governing permissions and limitations under "
    "the License.\n\n"
)

# Weather icon mapping
WEATHER_ICONS = {
    0: "icons/sun.svg",
    1: "icons/partial_clouds.svg",
    2: "icons/clouds.svg",
    3: "icons/rain.svg",
    4: "icons/rain.svg",
    5: "icons/storm.svg",
    6: "icons/snow.svg",
    7: "icons/fog.svg",
}


class HomeScreen:
    _is_page: bool = True  # required class attribute for correct loading

    def __init__(
        self: HomeScreen,
        session_data: Optional[Dict[str, Any]],
    ):
        self._session_data: Dict[str, Any] = {
            "notification": {},
            "notification_model": [],
            "system_connectivity": "offline",
            "persistent_menu_hint": False,
            "applications_model": [],
            "apps_enabled": True,
            "time_string": "",
            "date_string": "",
            "weekday_string": "",
            "day_string": "",
            "month_string": "",
            "year_string": "",
            "skill_info_enabled": False,
            "skill_info_prefix": False,
            "rtl_mode": 0,
            "dateFormat": "MDY",
            "wallpaper_path": "",
            "selected_wallpaper": "default.jpg",
            "weather_code": None,
            "weather_temp": None,
        }
        if session_data:
            self._session_data.update(session_data)
        self._element_keys = {
            "time_string": "time_string",
            "weekday_string": "full_date_string",
            "day_string": "full_date_string",
            "month_string": "full_date_string",
            "year_string": "full_date_string",
            "selected_wallpaper": "selected_wallpaper",
            "weather_code": "weather_icon",
            "weather_temp": "weather_temp",
        }
        self._time_text: Text = Text(
            key="time_string",
            size=200,
            color="white",
            weight=FontWeight.BOLD
        )
        self._full_date_text: Text = Text(
            key="full_date_string",
            size=100,
            color="white",
            weight=FontWeight.BOLD
        )
        # Weather icon and text
        self._weather_icon: Image = Image(
            src=self.weather_icon_src,
            key="weather_icon",
            width=100,
            height=100,
            fit=ImageFit.CONTAIN,
        )
        self._weather_temp_text: Text = Text(
            self.weather_temperature,
            key="weather_temp",
            size=50,
            color="white",
            weight=FontWeight.BOLD,
        )
        # Background settings
        self._background_container = Container(
            key="selected_wallpaper",
            expand=True,
            image_src=self._session_data["selected_wallpaper"],
            image_fit=ImageFit.COVER,
        )
        self._weather_container = Container(
            content=Row(
                [
                    self._weather_icon,
                    self._weather_temp_text,
                ],
                alignment="end",
                vertical_alignment="center",
                spacing=10,
            ),
            padding=20,
            alignment=alignment.top_right,
        )
        self._overlay = Container(
            content=Column(
                [
                    self._time_text,
                    self._full_date_text,
                ],
                alignment=MainAxisAlignment.END,
                horizontal_alignment=CrossAxisAlignment.START,
                spacing=10,
            ),
            padding=20,
        )
        # Bottom bar
        self._menu_button = IconButton(
            icons.MENU,
            tooltip="Menu",
            icon_color=colors.WHITE,
            on_click=None,
        )
        self._bar = BottomAppBar(
            content=Row(
                controls=[
                    self._menu_button,
                    IconButton(
                        icons.ARROW_BACK,
                        tooltip="Back",
                        icon_color=colors.WHITE
                    ),
                    TextField(
                        label="Ask anything",
                        color=colors.WHITE,
                        bgcolor=colors.BLACK87,
                        expand=True,
                    ),
                ],
            ),
            height=60,
            bgcolor=colors.BLACK87,
            padding=padding.symmetric(vertical=0, horizontal=10),
        )
        # Drawer menu options
        self._collapse_button = IconButton(
            icons.CLOSE,
            tooltip="Close",
            icon_color=colors.WHITE,
            on_click=None,
        )
        self._option_style = {
            "settings": {
                "normal": {
                    "icon": {
                        "name": icons.SETTINGS_OUTLINED,
                        "color": colors.WHITE,
                    },
                    "text": {
                        "color": colors.WHITE,
                        "weight": FontWeight.NORMAL,
                    },
                    "container": {
                        "bgcolor": colors.TRANSPARENT,
                    },
                },
                "on_hover": {
                    "icon": {
                        "name": icons.SETTINGS_ROUNDED,
                        "color": colors.BLACK87,
                    },
                    "text": {
                        "color": colors.BLACK87,
                        "weight": FontWeight.BOLD,
                    },
                    "container": {
                        "bgcolor": colors.WHITE,
                    },
                },
            },
            "about": {
                "normal": {
                    "icon": {
                        "name": icons.INFO_OUTLINED,
                        "color": colors.WHITE,
                    },
                    "text": {
                        "color": colors.WHITE,
                        "weight": FontWeight.NORMAL,
                    },
                    "container": {
                        "bgcolor": colors.TRANSPARENT,
                    },
                },
                "on_hover": {
                    "icon": {
                        "name": icons.INFO_ROUNDED,
                        "color": colors.BLACK87,
                    },
                    "text": {
                        "color": colors.BLACK87,
                        "weight": FontWeight.BOLD,
                    },
                    "container": {
                        "bgcolor": colors.WHITE,
                    },
                },
            },
        }
        self._settings_option = Container(
            content=Row(
                controls=[
                    Icon(
                        key="settings-icon",
                        **self._option_style["settings"]["normal"]["icon"],
                    ),
                    Text(
                        "Settings",
                        key="settings-text",
                        size=20,
                        **self._option_style["settings"]["normal"]["text"],
                    ),
                ],
                expand=True,
                spacing=20,
            ),
            key="settings-container",
            padding=padding.symmetric(vertical=10, horizontal=30),
            on_hover=None,
            **self._option_style["settings"]["normal"]["container"],
        )
        self._about_option = Container(
            content=Row(
                controls=[
                    Icon(
                        key="about-icon",
                        **self._option_style["about"]["normal"]["icon"],
                    ),
                    Text(
                        "About",
                        key="about-text",
                        size=20,
                        **self._option_style["about"]["normal"]["text"],
                    ),
                ],
                expand=True,
                spacing=20,
            ),
            key="about-container",
            padding=padding.symmetric(vertical=10, horizontal=30),
            on_hover=None,
            **self._option_style["about"]["normal"]["container"],
        )
        # Drawer object
        self._drawer = NavigationDrawer(
            on_dismiss=None,
            on_change=None,
            controls=[
                Row(
                    controls=[self._collapse_button],
                    height=40,
                    expand=True,
                    alignment=MainAxisAlignment.END,
                ),
                self._settings_option,
                self._about_option,
            ],
            bgcolor=colors.BLACK87,
            indicator_color=colors.WHITE,
            indicator_shape=RoundedRectangleBorder(radius=0),
        )
        # About banner
        self._about_close_button = IconButton(
            icons.CLOSE,
            tooltip="Close",
            icon_color=colors.WHITE,
            on_click=None,
        )
        self._about_banner = BottomSheet(
            content=Container(
                content=Column(
                    controls=[
                        Row(
                            controls=[self._about_close_button],
                            alignment=MainAxisAlignment.END,
                        ),
                        Text("Client Information", size=24, color=colors.WHITE, weight=FontWeight.BOLD),
                        Text(VERSION_TEXT, color=colors.WHITE),
                        Text("License", size=24, color=colors.WHITE, weight=FontWeight.BOLD),
                        Text(LICENSE_TEXT, color=colors.WHITE),
                    ],
                    expand=True,
                ),
                height=1000,
                width=800,
                expand=True,
                bgcolor=colors.TRANSPARENT,
                padding=padding.only(left=50, top=10, right=20, bottom=10),
            ),
            bgcolor=colors.BLACK87,
        )
        # Page (view)
        self._view = View(
            "/home",
            controls=[
                Stack(
                    [
                        self._background_container,
                        self._weather_container,
                        self._overlay,
                    ],
                    expand=True,
                ),
            ],
            appbar=self._bar,
            drawer=self._drawer,
            padding=0,
        )

    @property
    def page(self: HomeScreen) -> View:
        return self._view

    @property
    def full_date(self: HomeScreen) -> str:
        weekday = self._session_data["weekday_string"][:3].title()
        month = self._session_data["month_string"].title()
        day = self._session_data["day_string"]
        year = self._session_data["year_string"]
        return f"{weekday} {month} {day}, {year}"

    @property
    def wallpaper_uri(self: HomeScreen) -> str:
        wallpaper_path = self._session_data["wallpaper_path"]
        selected_wallpaper = self._session_data["selected_wallpaper"]
        if wallpaper_path:
            # Hack to workaround the way Flet serves figures
            shutil.copy(
                os.path.join(wallpaper_path, selected_wallpaper),
                "assets/",
            )
        return selected_wallpaper

    @property
    def weather_icon_src(self) -> str:
        """Returns the local file path for the weather icon."""
        weather_code = self._session_data.get("weather_code")
        if weather_code is not None and weather_code in WEATHER_ICONS:
            return WEATHER_ICONS[weather_code]
        return "icons/default.svg"  # Fallback icon if weather_code is missing or invalid

    @property
    def weather_temperature(self) -> str:
        """Formats the temperature with °C."""
        weather_temp = self._session_data.get("weather_temp")
        if weather_temp is not None:
            return f"{weather_temp} °C"
        return ""

    def update_session_data(
        self: HomeScreen,
        session_data: Dict[str, Any],
        renderer: Any
    ) -> None:
        self._session_data.update(session_data)
        for key, value in session_data.items():
            if key not in self._element_keys:
                continue
            element_key = self._element_keys[key]
            if element_key == "full_date_string":  # full date
                attr_name = "value"
                attr_value = self.full_date
                self._full_date_text.value = attr_value
            elif element_key == "selected_wallpaper":  # wallpaper
                attr_name = "image_src"
                attr_value = self.wallpaper_uri
                self._background_container.image_src = attr_value
            elif element_key == "weather_icon":  # weather icon
                attr_name = "src"
                attr_value = self.weather_icon_src
                self._weather_icon.src = attr_value
            elif element_key == "weather_temp":  # weather temperature
                attr_name = "value"
                attr_value = self.weather_temperature
                self._weather_temp_text.value = attr_value
            else:
                attr_name = "value"
                attr_value = value
                self._time_text.value = attr_value
            print(f"Updating {element_key} with {attr_name}={attr_value} in /home.")
            renderer.update_attributes(
                route="/home",
                key=element_key,
                attributes={attr_name: attr_value},
            )

    def set(self: HomeScreen, renderer: Any) -> None:
        # Set callbacks
        self._menu_button.on_click = lambda _: renderer.open_component(
            route="/home",
            component="drawer",
        )

        def on_hover(event: ControlEvent, option: str) -> None:
            entered: bool = (event.data == "true")
            style_key = "on_hover" if entered else "normal"
            renderer.update_attributes(
                route="/home",
                key=f"{option}-container",
                attributes=self._option_style[option][style_key]["container"],
            )
            renderer.update_attributes(
                route="/home",
                key=f"{option}-icon",
                attributes=self._option_style[option][style_key]["icon"],
            )
            renderer.update_attributes(
                route="/home",
                key=f"{option}-text",
                attributes=self._option_style[option][style_key]["text"],
            )

        def on_dismiss(event: ControlEvent) -> None:
            renderer.close_component(
                route="/home",
                component="drawer",
            )

        self._collapse_button.on_click = on_dismiss
        self._drawer.on_dismiss = on_dismiss

        self._settings_option.on_hover = partial(on_hover, option="settings")
        self._about_option.on_hover = partial(on_hover, option="about")

        def about_on_click(event: ControlEvent) -> None:
            on_dismiss(event)
            renderer.open_component(
                route="/home",
                component=self._about_banner,
            )

        self._about_option.on_click = about_on_click

        self._about_close_button.on_click = lambda _ : renderer.close_component(
            route="/home",
            component=self._about_banner,
        )
