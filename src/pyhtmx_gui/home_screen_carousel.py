from __future__ import annotations
import os
from typing import Any, Optional, List, Dict
import random
from pyhtmx import Div, Img, Script, Link, Ul, Li
from pyhtmx_gui.kit import SessionItem, Widget, Page


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


class ClockTimeWidget(Widget):
    _parameters = ("time_string", )

    def __init__(
        self: ClockTimeWidget,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(session_data=session_data)
        # Time text
        time_text: Div = Div(
            inner_content=session_data.get("time_string"),
            _id="clock",
            _class="digital-clock",
        )
        self.add_interaction(
            "time_string",
            SessionItem(
                parameter="clock",
                attribute="inner_content",
                component=time_text,
            ),
        )
        self._widget: Div = Div(
            [
                Div(
                    inner_content="Current Time",
                    _class="modern-title"
                ),
                time_text,
            ],
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
        self.add_interaction(
            "time_string",
            SessionItem(
                parameter="time",
                attribute="inner_content",
                component=time_text,
            )
        )

        # Full date text
        date_text: Div = Div(
            inner_content=self.format_date(),
            _id="date",
            _class="text-[4vw] text-white font-bold",
        )
        session_item = SessionItem(
            parameter="date",
            attribute="inner_content",
            component=date_text,
            format_value=self.format_date,
        )
        # Same object for all date parameters:
        # whenever one of them changes, the object state changes
        for parameter in [
            "weekday_string",
            "month_string",
            "day_string",
            "year_string",
        ]:
            self.add_interaction(parameter, session_item)

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

    def format_date(self: DateTimeWidget, value: Any = None) -> str:
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
        self.add_interaction(
            "weather_code",
            SessionItem(
                parameter="weather_code",
                attribute="src",
                component=weather_icon,
                format_value=self.weather_icon_src,
                target_level="outerHTML",
            ),
        )
        # Wrap img in a div to control size dynamically
        weather_icon_container: Div = Div(
            weather_icon,
            _class="w-[8vw] h-[8vw]",
        )

        # Weather temperature text
        weather_temp_text: Div = Div(
            inner_content=self.weather_temperature(),
            _id="weather_temp",
            _class=[
                "text-[4vw]",
                "leading-[8vw]",
                # "text-white",
                "font-bold",
            ],
        )
        self.add_interaction(
            "weather_temp",
            SessionItem(
                parameter="weather_temp",
                attribute="inner_content",
                component=weather_temp_text,
                format_value=self.weather_temperature,
            ),
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
            _class=[
                "flex",
                "grow",
                "justify-end",
                "items-start",
            ],
        )

    def weather_icon_src(self: WeatherWidget, value: Any = None) -> str:
        """Returns the local file path for the weather icon."""
        weather_code = self._session_data["weather_code"]
        if weather_code is not None and weather_code in WEATHER_ICONS:
            return WEATHER_ICONS[weather_code]
        return os.path.join("assets", "icons", "no-internet.svg")

    def weather_temperature(self: WeatherWidget, value: Any = None) -> str:
        weather_temp = self._session_data["weather_temp"]
        """Formats the temperature with °C."""
        if weather_temp is not None:
            return f"{weather_temp}°C"
        return '--.-°C'


class SkillExamplesWidget(Widget):
    _parameters = ("skill_examples", )

    def __init__(
        self: SkillExamplesWidget,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(session_data=session_data)

        # List of example commands
        skill_examples: List[Li] = [
            Li(
                inner_content=self.skill_example(),
                _id=f"skill-example-{i}",
                _class="font-bold",
            ) for i in range(5)
        ]
        for i, example in enumerate(skill_examples):
            self.add_interaction(
                "skill_examples",
                SessionItem(
                    parameter=f"example-{i}",
                    attribute="inner_content",
                    component=example,
                    format_value=self.skill_example,
                ),
            )

        # Widget container
        self._widget: Div = Div(
            Ul(
                skill_examples,
                style={"list-style-type": "disc"},
            ),
            _class=[
                "p-[1vw]",
                "text-left",
                "flex",
                "flex-col",
                "justify-start",
                "items-start",
            ],
        )

    def skill_example(
        self: SkillExamplesWidget,
        value: Any = None,
    ) -> str:
        data = self._session_data.get("skill_examples", {})
        examples = data.get("examples", []) if data else []
        examples = list(map(lambda s: s[0].upper() + s[1:], examples))
        return random.choice(examples) if examples else ''


class HomeScreen(Page):
    def __init__(self, session_data: Optional[Dict[str, Any]]):
        super().__init__(name="home", session_data=session_data)

        self.clock_time = ClockTimeWidget(session_data)
        self.date_time = DateTimeWidget(session_data)
        self.weather1 = WeatherWidget(session_data)
        self.weather2 = WeatherWidget(session_data)
        # Add SkillExamplesWidget
        self.skill_examples = SkillExamplesWidget(session_data)
        self.add_component(
            [
                self.clock_time,
                self.date_time,
                self.weather1,
                self.weather2,
                self.skill_examples,
            ],
        )

        # Carousel Div with items
        carousel_items = self.generate_carousel()

        # Carousel-container
        carousel_container = Div(
            carousel_items,
            _class=[
                "carousel",
                "w-full",
                "h-full",
                "relative",
                "snap-x",
                "snap-mandatory",
                "overflow-x-auto",
                "flex",
            ],
            _id="carousel",
        )

        # Tabs-container
        tab_classes = [
            "tab",
            "tab-lifted",
            "text-white",
            "font-bold",
        ]
        tabs_container = Div(
            [
                Div(inner_content="1", _class=tab_classes),
                Div(inner_content="2", _class=tab_classes),
                Div(inner_content="3", _class=tab_classes),
                Div(inner_content="4", _class=tab_classes),
            ],
            _class=[
                "tabs",
                "tabs-boxed",
                "tabs-lg",
                "tabs-hidden",
                "mb-4",
                "flex",
                "justify-center",
            ],
            _id="tabs-container",
            style={
                "height": "10%",
                "width": "100%",
                "position": "fixed",
                "z-index": 1,
                "top": "90vh",
                "left": "0",
                "background-color": "rgba(0, 0, 0, 0)",
                "overflow-y": "hidden",
                "transition": "0.5s",
            },
        )

        # Combine carousel and tabs
        main_view = Div(
            [carousel_container, tabs_container],
            _class=[
                "h-full",
                "w-full",
                "flex",
                "flex-col",
                "items-center",
                "justify-center",
            ],
            _id="carousel-bg",
            style={
                "background": (
                    "linear-gradient(to right, "
                    "rgb(59, 130, 246), rgb(255, 182, 193))"
                ),
                "transition": "background 0.5s ease",
            },
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

    def generate_carousel(self: HomeScreen) -> List[Div]:
        """Genereert carousel-items op basis van de HTML-structuur."""
        # General carousel item and subitem classes
        item_classes = [
            "carousel-item",
            "w-full",
            "h-full",
            "flex",
            "justify-center",
            "items-center",
            "snap-center",
        ]
        subitem_classes = [
            "bg-white",
            "rounded-lg",
            "p-8",
            "text-center",
            "shadow-lg",
        ]
        text_classes = ["modern-text", "text-lg", "mt-4"]
        # Carousel Item 1
        item1: Div = Div(
            Div(
                [
                    Div(
                        self.date_time.widget,
                        _class=[
                            "flex",
                            "flex-col",
                            "items-center",
                            "space-y-2"
                        ],
                    ),
                    Div(
                        self.weather1.widget,
                    ),
                ],
                _id="full-screen-image",
                _class=[
                    "full-screen-image",
                    "flex",
                    "flex-col",
                    "items-center",
                    "justify-center",
                ],
            ),
            _class=item_classes,
        )
        # Carousel Item 2
        item2: Div = Div(
            Div(
                [
                    Div(
                        self.clock_time.widget,
                        _class=[
                            *subitem_classes,
                            "bg-opacity-60",
                            "w-full",
                        ],
                    ),
                    Div(
                        [
                            Div(
                                [
                                    Div(
                                        inner_content="Weather",
                                        _class="modern-title"
                                    ),
                                    Div(
                                        self.weather2.widget,
                                        _class="weather-widget-small",
                                    ),
                                ],
                                _class=[
                                    *subitem_classes,
                                    "bg-opacity-60",
                                    "w-1/2",
                                ],
                            ),
                            Div(
                                [
                                    Div(
                                        inner_content="Alarm clock",
                                        _class="modern-title"
                                    ),
                                    Div(
                                        inner_content=(
                                            "Set an alarm to wake "
                                            "up on time"
                                        ),
                                        _class=text_classes,
                                    ),
                                ],
                                _class=[
                                    *subitem_classes,
                                    "bg-opacity-60",
                                    "w-1/2",
                                ],
                            ),
                        ],
                        _class=[
                            "flex",
                            "w-full",
                            "justify-between",
                            "space-x-4",
                        ],
                    ),
                ],
                _class=[
                    "flex",
                    "flex-col",
                    "items-center",
                    "space-y-4",
                    "w-full",
                    "max-w-4xl",
                    "px-4",
                ],
            ),
            _class=item_classes,
        )
        # Carousel Item 3 (updated)
        item3: Div = Div(
            Div(
                [
                    Div(
                        [
                            Div(
                                inner_content="What is the latest news?",
                                _class="modern-title",
                            ),
                            Div(
                                inner_content=(
                                    "Stay updated with the latest events "
                                    "happening around the world."
                                ),
                                _class=text_classes,
                            ),
                        ],
                        _class=[*subitem_classes, "bg-opacity-40"],
                    ),
                    Div(
                        [
                            Div(
                                inner_content="Play music on Spotify",
                                _class="modern-title",
                            ),
                            Div(
                                inner_content=(
                                    "Listen to your favorite playlists "
                                    "and artists on Spotify."
                                ),
                                _class=text_classes,
                            ),
                        ],
                        _class=[*subitem_classes, "bg-opacity-40"],
                    ),
                    Div(
                        [
                            Div(
                                inner_content="Tell me a joke",
                                _class="modern-title",
                            ),
                            Div(
                                inner_content=(
                                    "Enjoy a lighthearted joke "
                                    "to brighten your day."
                                ),
                                _class=text_classes,
                            ),
                        ],
                        _class=[*subitem_classes, "bg-opacity-40"],
                    ),
                    Div(
                        [
                            Div(
                                inner_content="Play underwater adventure game",
                                _class="modern-title",
                            ),
                            Div(
                                inner_content=(
                                    "Dive into an exciting underwater "
                                    "adventure game."
                                ),
                                _class=text_classes,
                            ),
                        ],
                        _class=[*subitem_classes, "bg-opacity-40"],
                    ),
                    # Skill examples title and widget
                    Div(
                        [
                            Div(
                                inner_content="Skill examples",
                                _class="modern-title"
                            ),  # Add title "Skill examples"
                            # Add SkillExamplesWidget
                            self.skill_examples.widget,
                        ],
                        _class=[*subitem_classes, "bg-opacity-40"],
                    ),
                ],
                _class=[
                    "grid",
                    "grid-cols-2",
                    "gap-4",
                    "w-full",
                    "max-w-4xl",
                    "px-4",
                ],
            ),
            _class=item_classes,
        )
        # Carousel Item 4
        item4: Div = Div(
            Div(
                [
                    Div(
                        inner_content="Another widget",
                        _class="modern-title",
                    ),
                    Div(
                        inner_content="Room for other skills content.",
                        _class="modern-text text-lg mt-4",
                    ),
                ],
                _class=subitem_classes,
            ),
            _class=item_classes,
        )
        return [item1, item2, item3, item4]
