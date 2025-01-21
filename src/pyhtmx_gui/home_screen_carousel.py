from __future__ import annotations
import os
from typing import Any, Optional, List, Dict
import random
from pyhtmx import Div, Input, Img, Script, Link, Ul, Li, H2
from pyhtmx_gui.page_manager import PageManager
from pyhtmx_gui.types import DOMEvent
from pyhtmx_gui.kit import SessionItem, Control, Widget, Page


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
            _id="weather-icon",  # unique element id
            src=self.weather_icon_src(),
            alt=self.weather_icon_alt(),
            width="auto",
            height="auto",
        )
        # NOTE: USE CASE #1: multiplicity of attributes
        # Description:
        # A single session parameter must update two or more attributes on an
        # HTML element.
        #
        # Design approach: it's been decided for now, at which point we do not
        # have enough elements as clear guidance or requirements, that it makes
        # sense to use the same SessionItem to update the HTML element for as
        # many attributes as necessary (including inner content).
        #
        # Consequence: the complexity of a SessionItem and its parsing must
        # increase to deal with updates for single or multiple attributes.
        self.add_interaction(
            "weather_code",  # session data key from OVOS
            SessionItem(
                parameter="weather-icon",  # message name for the SSE
                attribute=("src", "alt"),  # two attributes
                component=weather_icon,
                format_value={  # one formatter per attribute
                    "src": self.weather_icon_src,
                    "alt": self.weather_icon_alt,
                },
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
            _id="weather-temp",
            _class=[
                "text-[4vw]",
                "leading-[8vw]",
                "font-bold",
            ],
        )
        self.add_interaction(
            "weather_temp",
            SessionItem(
                parameter="weather-temp",
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

    def weather_icon_alt(self: WeatherWidget, value: Any = None) -> str:
        weather_code = self._session_data["weather_code"]
        if weather_code is not None and weather_code in WEATHER_ICONS:
            weather_alt, _ = os.path.splitext(
                os.path.basename(WEATHER_ICONS[weather_code])
            )
            return weather_alt.title().replace('_', ' ')
        return "No weather information"

    def weather_temperature(self: WeatherWidget, value: Any = None) -> str:
        weather_temp = self._session_data["weather_temp"]
        """Formats the temperature with °F."""
        if weather_temp is not None:
            return f"{weather_temp}°F"
        return '--.-°F'


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
        # NOTE: USE CASE #2: multiplicity of elements
        # Description:
        # A single session parameter must update two or more HTML elements.
        #
        # Design approach: it's been decided for now, at which point we do not
        # have enough elements as clear guidance or requirements, that it makes
        # sense to use one SessionItem per HTML element that must be updated,
        # but all SessionItem's must be mapped to the same session parameter
        # (from OVOS).
        #
        # Consequence: under the hood, the widget must keep track of a list of
        # SessionItem's per session parameter, and loop through them every time
        # the update method is called.
        for i, example in enumerate(skill_examples):
            self.add_interaction(
                "skill_examples",  # session data key from OVOS
                SessionItem(
                    parameter=f"example-{i}",  # message name for the SSE
                    attribute="inner_content",  # attribute
                    component=example,
                    format_value=self.skill_example,  # formatter
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

        # Bottom container
        tab_classes = [
            "tab",
            "tab-lifted",
            "text-white",
            "font-bold",
        ]
        text_input: Input = Input(
            _id="utterance-input",
            _type="text",
            value="",
            placeholder="Ask anything",
            onmouseout="this.blur()",  # Remove focus on mouse out
            _class=[
                "input",
                "input-bordered",
                "focus:border-sky-500",
                "focus:ring-sky-500",
                "focus:ring-1",
                "text-[20px]",
                "w-[30vw]",
                "h-[48px]",
                "ml-auto",
            ],
        )

        # Add interaction to send utterance back to OVOS
        def send_utterance_callback(page_manager: PageManager, dom_event: DOMEvent):
            # Send utterance to OVOS
            page_manager.send_utterance_to_ovos(dom_event.target.value)
            # Reset text input value
            page_manager.update_attributes(
                namespace="skill-ovos-homescreen.openvoiceos",
                page_id="home_screen",
                parameter="utterance-input",
                attribute={"value": ""},
            )
        self.add_interaction(
            "utterance_input",
            SessionItem(
                parameter="utterance-input",
                attribute="value",
                component=text_input,
            )
        )
        self.add_interaction(
            "send-utterance-key-up",
            Control(
                context="global",
                event="keyup[(event.code === 'Enter') && (this.value != '')] from:body",
                callback=send_utterance_callback,
                source=text_input,
            ),
        )

        # Bottom container
        bottom_container = Div(
            [
                text_input,
                Div(inner_content="1", _class=[*tab_classes, "ml-auto"]),
                Div(inner_content="2", _class=tab_classes),
                Div(inner_content="3", _class=tab_classes),
                Div(inner_content="4", _class=tab_classes),
            ],
            _class=[
                "tabs",
                "tabs-boxed",
                "tabs-lg",
                "tabs-hidden",
                "px-[1vw]",
                "pb-[1vw]",
                "mb-4",
                "flex",
                "justify-center",
            ],
            _id="bottom-container",
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

        # Combine carousel, utterance input and tabs
        main_view = Div(
            [carousel_container, bottom_container],
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

        # extra CSS for carousel
        style = Link(rel="stylesheet", href="assets/css/carousel.css")
        # script for carousel
        script = Script(src="assets/js/carousel.js")

        self._page: Div = Div(
            [main_view, style, script],
            _id="home",
            _class="flex flex-col",
            style={"width": "100vw", "height": "100vh"},
        )

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
                    H2(
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
                                    H2(
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
                                    H2(
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
                            H2(
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
                            H2(
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
                            H2(
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
                            H2(
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
                            H2(
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
                    H2(
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
