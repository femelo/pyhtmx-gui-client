from __future__ import annotations
import shutil
import os
from typing import Any, Optional, List, Dict, Tuple, Callable
from pyhtmx.html_tag import HTMLTag
from pyhtmx import Div, Img, Script, Link


# Version text
VERSION_TEXT = """
OpenVoiceOS - PyHTMX GUI Version: 1.0.0
"""


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
        target_level: Optional[str] = "innerHTML",
    ):
        self.parameter = parameter
        self.attribute = attribute
        self.component = component
        self.format_value = format_value
        self.target_level = target_level


class Widget:
    _parameters: Tuple[str] = ()

    def __init__(
        self: Widget,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        self._session_data: Dict[str, Any] = {
            parameter: '' for parameter in self._parameters
        }
        self._session_objects: Dict[str, Optional[SessionData]] = {
            parameter: None for parameter in self._parameters
        }
        self._widget: Optional[HTMLTag] = None
        self.init_session_data(session_data)

    @property
    def widget(self: Widget) -> Optional[HTMLTag]:
        return self._widget

    @property
    def session_objects(self: Widget) -> Dict[str, Optional[SessionData]]:
        return self._session_objects

    def has(self: Widget, parameter: str) -> bool:
        return parameter in self._parameters

    def init_session_data(self: Widget, session_data: Optional[Dict[str, Any]]) -> None:
        if session_data:
            self._session_data.update(
                {
                    k: v for k, v in session_data.items()
                    if k in self._session_data
                }
            )


class DateTimeWidget(Widget):
    _parameters = (
        "time_string",
        "weekday_string",
        "month_string",
        "day_string",
        "year_string",
    )

    def __init__(
        self: DateTimeWidget,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(session_data=session_data)

        # Time text
        time_text: Div = Div(
            inner_content=session_data.get("time_string"),
            _id="time",
            _class="text-[10vw] text-white font-bold",
        )
        self._session_objects["time_string"] = SessionData(
            parameter="time",
            attribute="inner_content",
            component=time_text,
        )
        # Full date text
        date_text: Div = Div(
            inner_content=self.format_date(),
            _id="date",
            _class="text-[6vw] text-white font-bold",
        )
        date_session_object = SessionData(
            parameter="date",
            attribute="inner_content",
            component=date_text,
            format_value=self.format_date,
        )
        # Same object for all date parameters:
        # whenever one of them changes, the object state changes
        for parameter in ["weekday_string", "month_string", "day_string", "year_string"]:
            self._session_objects[parameter] = date_session_object

        # Time and date container
        self._widget: Div = Div(
            [
                time_text,
                date_text,
            ],
            _class=[
                "p-[1vw]",
                "flex",
                "flex-col",
                "justify-start",
                "items-start",
            ],
        )

    def format_date(self: DateTimeWidget, *args: Any, **kwargs: Any) -> str:
        weekday = self._session_data.get("weekday_string", '')[:3]
        month = self._session_data.get("month_string", '')
        day = self._session_data.get("day_string", '')
        year = self._session_data.get("year_string", '')
        return f"{weekday} {month} {day}, {year}"



class WeatherWidget(Widget):
    _parameters = ("weather_code", "weather_temp")

    def __init__(
        self: WeatherWidget,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(session_data=session_data)

        # Weather icon
        weather_icon: Img = Img(
            _id="weather_code",
            src=self.weather_icon_src(),
            width="auto",
            height="auto",
        )
        # Wrap img in a div to control size dynamically
        weather_icon_container: Div = Div(
            weather_icon,
            _class="w-[8vw] h-[8vw]",
        )
        self._session_objects["weather_code"] = SessionData(
            parameter="weather_code",
            attribute="src",
            component=weather_icon,
            format_value=self.weather_icon_src,
            target_level="outerHTML",
        )
        # Weather temperature text
        weather_temp_text: Div = Div(
            inner_content=self.weather_temperature(),
            _id="weather_temp",
            _class="text-[4vw] leading-[8vw] text-white font-bold",
        )
        self._session_objects["weather_temp"] = SessionData(
            parameter="weather_temp",
            attribute="inner_content",
            component=weather_temp_text,
            format_value=self.weather_temperature,
        )
        # Weather container
        self._widget: Div = Div(
            Div(
                [
                    weather_icon_container,
                    weather_temp_text,
                ],
                _class=[
                    "p-[1vw]",
                    "flex",
                    "gap-[2vw]",
                ],
            ),
            _class="flex grow justify-end items-start",
        )

    def weather_icon_src(self: WeatherWidget, *args: Any, **kwargs: Any) -> str:
        """Returns the local file path for the weather icon."""
        weather_code = self._session_data["weather_code"]
        if weather_code is not None and weather_code in WEATHER_ICONS:
            return WEATHER_ICONS[weather_code]
        return os.path.join("assets", "icons", "no-internet.svg")

    def weather_temperature(self: WeatherWidget, *args: Any, **kwargs: Any) -> str:
        weather_temp = self._session_data["weather_temp"]
        """Formats the temperature with °C."""
        if weather_temp is not None:
            return f"{weather_temp}°C"
        return ''


class SkillExamplesWidget(Widget):
    _parameters = ("examples",)

    def __init__(self: SkillExamplesWidget, session_data: Optional[Dict[str, Any]] = None):
        super().__init__(session_data=session_data)

        # List of example commands
        examples_text = "\n".join(session_data.get("skill_examples", {}).get("examples", []))
        
        examples_div = Div(
            inner_content=examples_text,
            _id="skill_examples",
            _class="text-[4vw] text-white font-bold",
        )
        
        self._session_objects["examples"] = SessionData(
            parameter="examples",
            attribute="inner_content",
            component=examples_div,
        )

        # Widget container
        self._widget: Div = Div(
            examples_div,
            _class="p-[1vw] flex flex-col justify-start items-start",
        )


class HomeScreen:
    _is_page = True

    def __init__(self, session_data: Optional[Dict[str, Any]]):
        self._route: str = "/home"
        
        self.date_time_widget = DateTimeWidget(session_data)
        self.weather_widget = WeatherWidget(session_data)
        self.skill_examples_widget = SkillExamplesWidget(session_data)  # Add SkillExamplesWidget
        
        self._session_data = {
            "time_string": self.date_time_widget._session_data.get("time_string", ""),
            "weather_code": self.weather_widget._session_data.get("weather_code", 0),
            "weather_temp": self.weather_widget._session_data.get("weather_temp", 0),
            "full_date": self.date_time_widget.format_date(),
        }

        # Carousel Div with items
        carousel_items = self.generate_carousel(self._session_data)

        # Carousel-container
        carousel_container = Div(
            carousel_items,
            _class="carousel w-full h-full relative snap-x snap-mandatory overflow-x-auto flex",
            _id="carousel",
        )

        # Tabs-container
        tabs_container = Div(
            [
                Div(inner_content="1", _class="tab tab-lifted"),
                Div(inner_content="2", _class="tab tab-lifted"),
                Div(inner_content="3", _class="tab tab-lifted"),
                Div(inner_content="4", _class="tab tab-lifted"),
            ],
            _class="tabs tabs-boxed mb-4 w-full max-w-[15%] flex justify-center",
            _id="tabs-container", 
        )

        # Combine carousel and tabs 
        main_view = Div(
            [carousel_container, tabs_container],
            _class="h-full w-full flex flex-col items-center justify-center",
            _id="carousel-bg",
            style="background: linear-gradient(to right, rgb(59, 130, 246), rgb(255, 182, 193)); transition: background 0.5s ease;",
        )

        self._page: Div = Div(
            main_view,
            _id="home",
            _class="flex flex-col",
            style={"width": "100vw", "height": "100vh"},
        )
        
        script_tag = Script(src="assets/js/carousel.js")
        self._page.add_child(script_tag)
        
        # extra CSS for carousel
        style_tag = Link(rel="stylesheet", href="assets/css/styles.css") 
        self._page.add_child(style_tag)

    def generate_carousel(self: HomeScreen, session_data: Optional[Dict[str, Any]]) -> List[Div]:
        """Genereert carousel-items op basis van de HTML-structuur."""
        return [
            # Carousel Item 1
            Div(
                Div(
                    [
                        Div(
                            [
                                # Datum boven tijd
                                self.date_time_widget._session_objects["weekday_string"].component,  # Fetch date
                                self.date_time_widget._session_objects["time_string"].component,     # Fetch time
                            ],
                            _class="flex flex-col items-center space-y-2",
                        ),
                        Div(
                            [
                                self.weather_widget.widget,  # Re-use the existing WeatherWidget
                            ],
                        ),
                    ],
                    _id="full-screen-image", 
                    _class="full-screen-image flex flex-col items-center justify-center",
                ),
                _class="carousel-item w-full h-full flex justify-center items-center snap-center",
            ),
            # Carousel Item 2
            Div(
                Div(
                    [
                        Div(
                            [
                                Div(inner_content="Current Time", _class="modern-title"),
                                Div(inner_content=session_data.get("time_string", "12:00"), _class="digital-clock"),
                            ],
                            _class="bg-white bg-opacity-60 rounded-lg p-8 text-center shadow-lg w-full",
                        ),
                        Div(
                            [
                                Div(
                                    [
                                        Div(inner_content="Weather", _class="modern-title"),
                                        Div(
                                            [
                                                self.weather_widget.widget,  
                                            ],
                                            _class="weather-widget-small", 
                                        ),
                                    ],
                                    _class="bg-white bg-opacity-60 rounded-lg p-8 text-center shadow-lg w-1/2",
                                ),
                                Div(
                                    [
                                        Div(inner_content="Alarm clock", _class="modern-title"),
                                        Div(inner_content="Set an alarm to wake up on time", _class="modern-text text-lg mt-4"),
                                    ],
                                    _class="bg-white bg-opacity-60 rounded-lg p-8 text-center shadow-lg w-1/2",
                                ),
                            ],
                            _class="flex w-full justify-between space-x-4",
                        ),
                    ],
                    _class="flex flex-col items-center space-y-4 w-full max-w-4xl px-4",
                ),
                _class="carousel-item w-full h-full flex justify-center items-center snap-center",
            ),
            # Carousel Item 3 (updated)
            Div(
                Div(
                    [
                        Div(
                            [
                                Div(inner_content="What is the latest news?", _class="modern-title"),
                                Div(inner_content="Stay updated with the latest events happening around the world.", _class="modern-text text-lg mt-4"),
                            ],
                            _class="bg-white bg-opacity-40 rounded-lg p-8 text-center shadow-lg",
                        ),
                        Div(
                            [
                                Div(inner_content="Play music on Spotify", _class="modern-title"),
                                Div(inner_content="Listen to your favorite playlists and artists on Spotify.", _class="modern-text text-lg mt-4"),
                            ],
                            _class="bg-white bg-opacity-40 rounded-lg p-8 text-center shadow-lg",
                        ),
                        Div(
                            [
                                Div(inner_content="Tell me a joke", _class="modern-title"),
                                Div(inner_content="Enjoy a lighthearted joke to brighten your day.", _class="modern-text text-lg mt-4"),
                            ],
                            _class="bg-white bg-opacity-40 rounded-lg p-8 text-center shadow-lg",
                        ),
                        Div(
                            [
                                Div(inner_content="Play underwater adventure game", _class="modern-title"),
                                Div(inner_content="Dive into an exciting underwater adventure game.", _class="modern-text text-lg mt-4"),
                            ],
                            _class="bg-white bg-opacity-40 rounded-lg p-8 text-center shadow-lg",
                        ),
                        # Skill examples title and widget
                        Div(
                            [
                                Div(inner_content="Skill examples", _class="modern-title"),  # Add title "Skill examples"
                                self.skill_examples_widget.widget,  # Add SkillExamplesWidget
                            ],
                            _class="bg-white bg-opacity-40 rounded-lg p-8 text-center shadow-lg",
                        ),
                    ],
                    _class="grid grid-cols-2 gap-4 w-full max-w-4xl px-4",
                ),
                _class="carousel-item w-full h-full flex justify-center items-center snap-center", 
            ),
            # Carousel Item 4
            Div(
                Div(
                    [
                        Div(
                            inner_content="Another widget", _class="modern-title"
                        ),
                        Div(
                            inner_content="Room for other skills content.", _class="modern-text text-lg mt-4"
                        ),
                    ],
                    _class="bg-white bg-opacity-60 rounded-lg p-8 text-center shadow-lg",
                ),
                _class="carousel-item w-full h-full flex justify-center items-center snap-center", 
            ),
        ]

    @property
    def page(self):
        return self._page

    @property
    def session_data(self):
        return self._session_data

    def update_session_data(self, session_data: Dict[str, Any], renderer: Any) -> None:
        for parameter, value in session_data.items():
            # session_data is updated in the widgets
            if parameter in self._session_data:
                self._session_data[parameter] = value

            # Renderer is updated
            for widget in [self.date_time_widget, self.weather_widget]:
                if widget.has(parameter):
                    widget._session_data[parameter] = value
                    session_object = widget.session_objects[parameter]
                    attr_name = session_object.attribute
                    attr_value = (
                        session_object.format_value(value)
                        if session_object.format_value else value
                    )
                    renderer.update_attributes(
                        route=self._route,
                        parameter=session_object.parameter,
                        attribute={attr_name: attr_value},
                    )

    def set_up(self, renderer: Any) -> None:
        # Register session parameters in the renderer
        registered = []
        for widget in [self.date_time_widget, self.weather_widget]:
            for _, session_object in widget.session_objects.items():
                if id(session_object) not in registered:
                    renderer.register_session_parameter(
                        route=self._route,
                        parameter=session_object.parameter,
                        target=session_object.component,
                        target_level=session_object.target_level,
                    )
                    registered.append(id(session_object))

  