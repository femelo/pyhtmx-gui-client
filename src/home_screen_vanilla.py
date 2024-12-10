from __future__ import annotations
import shutil
import os
from typing import Any, Optional, Dict, Callable
from pyhtmx.html_tag import HTMLTag
from pyhtmx import Div, Span, Img

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
    0: "assets/icons/sun.svg",
    1: "assets/icons/partial_clouds.svg",
    2: "assets/icons/clouds.svg",
    3: "assets/icons/rain.svg",
    4: "assets/icons/rain.svg",
    5: "assets/icons/storm.svg",
    6: "assets/icons/snow.svg",
    7: "assets/icons/fog.svg",
}


# TODO: move this to 'types.py'
class SessionData:
    def __init__(
        self: SessionData,
        parameter: str,
        attribute: str,
        component: HTMLTag,
        format_value: Optional[Callable] = None,
    ):
        self.parameter = parameter
        self.attribute = attribute
        self.component = component
        self.format_value = format_value


class HomeScreen:
    _is_page: bool = True  # required class attribute for correct loading

    def __init__(
        self: HomeScreen,
        session_data: Optional[Dict[str, Any]],
    ):
        self._route: str = "/home"
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
            "weather_code": "",
            "weather_temp": "",
        }
        if session_data:
            self._session_data.update(session_data)

        self._session_objects: Dict[str, Optional[SessionData]] = {
            "time_string": None,
            "weekday_string": None,
            "day_string": None,
            "month_string": None,
            "year_string": None,
            "selected_wallpaper": None,
            "weather_code": None,
            "weather_temp": None,
        }

        # Time text
        time_text: Div = Div(
            inner_content=session_data.get("time_string"),
            _id="time_string",
            _class="text-[200px] text-white font-bold",
        )
        self._session_objects["time_string"] = SessionData(
            parameter="time_string",
            attribute="inner_content",
            component=time_text,
        )
        # Weekday, month, day and year
        for parameter in [
            "weekday_string",
            "month_string",
            "day_string",
            "year_string",
        ]:
            component: Span = Span(
                inner_content=session_data.get(parameter),
                _id=parameter,
                _class="text-[60px] text-white font-bold",
            )
            self._session_objects[parameter] = SessionData(
                parameter=parameter,
                attribute="inner_content",
                component=component,
            )
        
        # Date container
        date_container: Div = Div(
            [
                self._session_objects["weekday_string"].component,
                " ",
                self._session_objects["month_string"].component,
                " ",
                self._session_objects["day_string"].component,
                ", ",
                self._session_objects["year_string"].component,
            ],
        )
        # Time and date container
        time_and_date: Div = Div(
            [
                time_text,
                date_container,
            ],
            _class=[
                "p-[20px]",
                "flex",
                "flex-col",
                "justify-start",
                "items-start",
            ],
        )

        # Weather icon
        formatted_weather_icon_src = self.weather_icon_src(
            self._session_data.get("weather_code")
        )
        weather_icon: Img = Img(
            _id="weather_code",
            src=formatted_weather_icon_src,
            width="100",
            height="100",
        )
        self._session_objects["weather_code"] = SessionData(
            parameter="weather_code",
            attribute="src",
            component=weather_icon,
            format_value=self.weather_icon_src,
        )
        # Weather temperature text
        formatted_temperature_value = self.weather_temperature(
            self._session_data.get("weather_temp")
        )
        weather_temp_text: Div = Div(
            formatted_temperature_value,
            key="weather_temp",
            _class="text-[50px] text-white font-bold",
        )
        self._session_objects["weather_temp"] = SessionData(
            parameter="weather_temp",
            attribute="inner_content",
            component=weather_temp_text,
            format_value=self.weather_temperature,
        )
        # Weather container
        weather_container: Div = Div(
            Div(
                [
                    weather_icon,
                    weather_temp_text,
                ],
                _class=[
                    "p-[20px]",
                    "flex",
                    "gap-[10px]",
                    "justify-end",
                    "items-center",
                ],
            ),
            _class="flex grow",
        )

        # Background container
        formatted_wallpaper_uri = self.wallpaper_uri(
            self._session_data.get("selected_wallpaper")
        )
        background_container: Div = Div(
            [
                weather_container,
                time_and_date,
            ],
            _id="selected_wallpaper",
            _class=[
                "p-[20px]",
                "flex",
                "grow",
                "flex-col",
                "justify-start",
                "items-stretch",
                "bg-cover",
                formatted_wallpaper_uri,
            ],
        )
        self._session_objects["selected_wallpaper"] = SessionData(
            parameter="selected_wallpaper",
            attribute="class",
            component=background_container,
            format_value=self.wallpaper_uri,
        )

        # Main view
        self._page: Div = Div(
            background_container,
            _id="home",
            _class="flex flex-col h-screen",
        )

    @property
    def page(self: HomeScreen) -> HTMLTag:
        return self._page

    def wallpaper_uri(self: HomeScreen, selected_wallpaper: str) -> str:
        wallpaper_path = self._session_data["wallpaper_path"]
        if wallpaper_path:
            # Hack to workaround the way Flet serves figures
            shutil.copy(
                os.path.join(wallpaper_path, selected_wallpaper),
                "assets/images/",
            )
        wallpaper_uri = os.path.join("assets", "images", selected_wallpaper)
        return f"bg-[url({wallpaper_uri})]"

    def weather_icon_src(self: HomeScreen, weather_code: Optional[str]) -> str:
        """Returns the local file path for the weather icon."""
        if weather_code is not None and weather_code in WEATHER_ICONS:
            return WEATHER_ICONS[weather_code]
        return os.path.join("assets", "icons", "default.svg")

    def weather_temperature(self: HomeScreen, weather_temp: Optional[str]) -> str:
        """Formats the temperature with °C."""
        if weather_temp is not None:
            return f"{weather_temp} °C"
        return ""

    def update_session_data(
        self: HomeScreen,
        session_data: Dict[str, Any],
        renderer: Any
    ) -> None:
        for parameter, value in session_data.items():
            if parameter in self._session_objects:
                session_object = self._session_objects[parameter]
                attr_name = session_object.attribute
                attr_value = (
                    session_object.format_value(value)
                    if session_object.format_value else value
                )
                renderer.update_attributes(
                    route=self._route,
                    parameter=parameter,
                    attribute={attr_name: attr_value},
                )

    def set_up(self: HomeScreen, renderer: Any) -> None:
        # Register session parameters
        for parameter, session_object in self._session_objects.items():
            renderer.register_session_parameter(
                route=self._route,
                parameter=parameter,
                target=session_object.component,
            )
