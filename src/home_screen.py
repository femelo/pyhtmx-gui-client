from __future__ import annotations
import shutil
import os
from secrets import token_hex
from typing import Any, Optional, List, Dict, Tuple, Callable
from enum import Enum
from functools import partial
from pyhtmx.html_tag import HTMLTag
from pyhtmx import Div, Img, Input, Label, Ul, Li, A, Br, H1, P, Button


# Background image
WALLPAPER = (
    "https://cdn.pixabay.com/photo/2016/06/02/02/33/"
    "triangles-1430105_1280.png"
)
# Version text
VERSION_TEXT = "OpenVoiceOS - PyHTMX GUI Version: 1.0.0"
# License text
LICENSE_URL = "https://www.apache.org/licenses/LICENSE-2.0"
LICENSE_P1 = (
    "Licensed under the Apache License, Version 2.0 (the 'License'); "
    "you may not use this file except in compliance with the License."
)
LICENSE_P2 = (
    "You may obtain a copy of the License at "
)
LICENSE_P3 = (
    "Unless required by applicable law or agreed to in writing, "
    "software distributed under the License is distributed on an "
    "'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, "
    "either express or implied."
)
LICENSE_P4 = (
    "See the License for the specific language governing permissions "
    "and limitations under the License."
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
        target_level: Optional[str] = "innerHTML",
    ):
        self.parameter = parameter
        self.attribute = attribute
        self.component = component
        self.format_value = format_value
        self.target_level = target_level


class Control:
    def __init__(
        self: Control,
        context: str,
        event: str,
        callback: Callable,
        source: HTMLTag,
        target: Optional[HTMLTag] = None,
        target_level: str = "innerHTML",
    ):
        self.context = context
        self.event = event
        self.callback = callback
        self.source = source
        self.target = target
        self.target_level = target_level


class WidgetType(str, Enum):
    COMPONENT = "component"
    DIALOG = "dialog"


class Widget:
    _parameters: Tuple[str] = ()

    def __init__(
        self: Widget,
        type: WidgetType = WidgetType.COMPONENT,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        self._id: str = token_hex(8)
        self._type: WidgetType = type
        self._session_data: Dict[str, Any] = {
            parameter: '' for parameter in self._parameters
        }
        self._session_objects: Dict[str, Optional[SessionData]] = {
            parameter: None for parameter in self._parameters
        }
        self._controls: Dict[str, Optional[Control]] = {}
        self._widget: Optional[HTMLTag] = None
        self.init_session_data(session_data)

    @property
    def id(self: Widget) -> str:
        return self._id

    @property
    def type(self: Widget) -> WidgetType:
        return self._type

    @property
    def widget(self: Widget) -> Optional[HTMLTag]:
        return self._widget

    @property
    def session_objects(self: Widget) -> Dict[str, Optional[SessionData]]:
        return self._session_objects

    @property
    def controls(self: Widget) -> Dict[str, Optional[Control]]:
        return self._controls

    def has(self: Widget, parameter: str) -> bool:
        return parameter in self._parameters

    def init_session_data(
        self: Widget,
        session_data: Optional[Dict[str, Any]],
    ) -> None:
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
            style={"text-shadow": "#272727 0.5vw 0.5vh 1vw"},
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
            style={"text-shadow": "#272727 0.5vw 0.5vh 1vw"},
        )
        date_session_object = SessionData(
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
            "year_string"
        ]:
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
            style={"filter": "drop-shadow(0.5vw 0.5vh 1vw #272727)"},
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
            style={"text-shadow": "#272727 0.5vw 0.5vh 1vw"},
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

    def weather_icon_src(
        self: WeatherWidget,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Returns the local file path for the weather icon."""
        weather_code = self._session_data["weather_code"]
        if weather_code is not None and weather_code in WEATHER_ICONS:
            return WEATHER_ICONS[weather_code]
        return os.path.join("assets", "icons", "no-internet.svg")

    def weather_temperature(
        self: WeatherWidget,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        weather_temp = self._session_data["weather_temp"]
        """Formats the temperature with °C."""
        if weather_temp is not None:
            return f"{weather_temp}°C"
        return '--,-'


class BottomBar(Widget):
    def __init__(
        self: BottomBar,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(session_data=session_data)

        self.button: Label = Label(
            Img(
                src="assets/icons/bars-solid.svg",
                width="25",
                height="25",
                _class="p-0",
                style="filter: invert(100%);"
            ),
            _for="drawer-input",
            _class=[
                "btn",
                "btn-neutral",
                "text-start",
                "animation-none",
                "drawer-button",
                "bg-[#272727]",
                "hover:bg-[#575757]",
                "py-[5px]",
                "px-[10px]",
                "w-[50px]",
            ],
        )

        self.text_input: Input = Input(
            _type="text",
            placeholder="Ask anything",
            _class=[
                "input",
                "input-bordered",
                "focus:border-sky-500",
                "focus:ring-sky-500",
                "focus:ring-1",
                "w-full",
                "h-[40px]",
                "grow",
            ],
        )

        self._widget: Div = Div(
            [
                self.button,
                self.text_input,
            ],
            _class=[
                "flex",
                "p-[5px]",
                "gap-[10px]",
                "justify-start",
                "items-center",
                "bg-[#272727]",
            ],
        )


class Drawer(Widget):
    def __init__(
        self: Drawer,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(session_data=session_data)

        self._settings_item: Li = Li(
            [
                Img(
                    src="./assets/icons/gear-solid.svg",
                    width=25,
                    height=25,
                    style="filter: invert(100%);",
                    _class="bg-transparent hover:bg-transparent p-0",
                ),
                Div(
                    "Settings",
                    _class="bg-transparent hover:bg-transparent select-none",
                ),
            ],
            _class=[
                "flex",
                "flex-row",
                "gap-[24px]",
                "items-stretch",
                "text-[20px]",
                "font-bold",
                "bg-transparent",
                "hover:bg-[#777777]",
                "px-[24px]",
                "py-[16px]",
                "rounded",
                "cursor-pointer",
                "active:bg-[#575757]",
                "hover:transition-all",
                "duration-700",
            ],
        )
        self._about_item: Li = Li(
            [
                Img(
                    src="./assets/icons/circle-info-solid.svg",
                    width=25,
                    height=25,
                    style="filter: invert(100%);",
                    _class="bg-transparent hover:bg-transparent p-0",
                ),
                Div(
                    "About",
                    _class="bg-transparent hover:bg-transparent select-none",
                ),
            ],
            _class=[
                "flex",
                "flex-row",
                "gap-[24px]",
                "items-stretch",
                "text-[20px]",
                "font-bold",
                "bg-transparent",
                "hover:bg-[#777777]",
                "px-[24px]",
                "py-[16px]",
                "rounded",
                "cursor-pointer",
                "active:bg-[#575757]",
                "hover:transition-all",
                "duration-700",
            ],
        )
        self._controls["menu-item-about-click"] = Control(
            context="global",
            event="click",
            # will open the dialog about
            callback=lambda renderer: renderer.open_dialog("about-dialog"),
            source=self._about_item,
            target=None,  # to target the dialog (to open it)
        )

        self.container: Div = Div(
            _class=[
                "drawer-content",
                "flex",
                "flex-col",
                "grow",
            ],
        )

        self._widget: Div = Div(
            [
                Input(
                    id="drawer-input",
                    _type="checkbox",
                    _class="drawer-toggle",
                ),
                self.container,
                Div(
                    [
                        Label(
                            _for="drawer-input",
                            aria_label="close sidebar",
                            _class="drawer-overlay",
                        ),
                        Ul(
                            [
                                self._settings_item,
                                self._about_item,
                            ],
                            _class=[
                                "flex",
                                "flex-col",
                                "leading-10",
                                "text-base-content",
                                "min-h-full",
                                "w-[400px]",
                                "py-[2px]",
                                "px-[2px]",
                                "text-white",
                                "bg-[#171717]",
                                "bg-opacity-80",
                            ],
                        ),
                    ],
                    _class="drawer-side",
                ),
            ],
            _class=[
                "drawer",
                "flex",
                "flex-col",
                "grow",
            ],
        )


class AboutDialog(Widget):

    def __init__(
        self: AboutDialog,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(type=WidgetType.DIALOG, session_data=session_data)

        self._id: str = "about-dialog"
        self._button: Button = Button(
            "Close",
            _class="btn btn-info",
        )
        self._controls["about-close-btn-click"] = Control(
            context="global",
            event="click",
            # will close the about dialog
            callback=lambda renderer: renderer.close_dialog("about-dialog"),
            source=self._button,
            target=None,  # to target the dialog (to close it)
        )
        self._widget: Div = Div(
            [
                H1("Version", _class="text-[20px] font-bold text-info"),
                P(VERSION_TEXT),
                Br(),
                Br(),
                H1("License", _class="text-[20px] font-bold text-info"),
                P(LICENSE_P1),
                P(
                    [
                        LICENSE_P2,
                        A(
                            f"{LICENSE_URL}.",
                            href=LICENSE_URL,
                            target="_blank",
                            rel="noopener noreferrer",
                            _class="text-orange-300",
                        ),
                    ],
                ),
                P(LICENSE_P3),
                P(LICENSE_P4),
                Br(),
                Br(),
                Div(
                    self._button,
                    _class="flex justify-end w-full b-transparent",
                ),
            ],
            _class=[
                "modal-box",
                "min-w-[50vw]",
                "px-[24px]",
                "py-[24px]",
                "text-white",
                "bg-[#171717]",
                "bg-opacity-80",
            ],
        )


class BackgroundContainer(Widget):
    _parameters = (
        "wallpaper_path",
        "selected_wallpaper",
    )

    def __init__(
        self: BackgroundContainer,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(session_data=session_data)

        # Background container
        background_container: Div = Div(
            _id="selected_wallpaper",
            _class=[
                "p-[1vw]",
                "flex",
                "grow",
                "flex-col",
                "justify-start",
                "items-stretch",
                "bg-cover",
                "bg-no-repeat",
            ],
            style=self.wallpaper_url(),
        )
        wallpaper_session_object = SessionData(
            parameter="wallpaper",
            attribute="style",
            component=background_container,
            format_value=self.wallpaper_url,
        )
        # Same object for both wallpaper parameters:
        # whenever one of them changes, the object state changes
        self._session_objects["wallpaper_path"] = wallpaper_session_object
        self._session_objects["selected_wallpaper"] = wallpaper_session_object

        # Time and date container
        self._widget: Div = background_container

    def wallpaper_url(
        self: BackgroundContainer,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        wallpaper_path = self._session_data.get("wallpaper_path", '')
        selected_wallpaper = self._session_data.get("selected_wallpaper", '')
        if wallpaper_path and selected_wallpaper:
            # Hack to workaround the way figures are served
            shutil.copy(
                os.path.join(wallpaper_path, selected_wallpaper),
                "assets/images/",
            )
        wallpaper_url = os.path.join("assets", "images", selected_wallpaper)
        return f"background-image: url({wallpaper_url});"


class HomeScreen:
    _is_page: bool = True  # required class attribute for correct loading

    def __init__(
        self: HomeScreen,
        session_data: Optional[Dict[str, Any]],
    ):
        self._route: str = "/home"

        date_and_time = DateTimeWidget(session_data=session_data)
        weather = WeatherWidget(session_data=session_data)
        background = BackgroundContainer(session_data=session_data)
        background.widget.add_child(weather.widget)
        background.widget.add_child(date_and_time.widget)
        drawer = Drawer(session_data=session_data)
        bar = BottomBar(session_data=session_data)
        about_dialog = AboutDialog(session_data=session_data)
        drawer.container.add_child(background.widget)
        drawer.container.add_child(bar.widget)

        self._widgets: List[Widget] = [
            date_and_time,
            weather,
            background,
            drawer,
            bar,
            about_dialog,
        ]

        self._session_data: Dict[str, Any] = {
            k: v for widget in self._widgets
            for k, v in widget._session_data.items()
        }

        # Main view
        self._page: Div = Div(
            drawer.widget,
            _id="home",
            _class="flex flex-col",
            style={"width": "100vw", "height": "100vh"},
        )

    @property
    def page(self: HomeScreen) -> HTMLTag:
        return self._page

    def update_session_data(
        self: HomeScreen,
        session_data: Dict[str, Any],
        renderer: Any
    ) -> None:
        for parameter, value in session_data.items():
            for widget in self._widgets:
                # Check whether the session parameter pertains to the widget
                if widget.has(parameter):
                    # If so, update the session data
                    widget._session_data[parameter] = value
                    # And update the corresponding attribute
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

    def set_up(self: HomeScreen, renderer: Any) -> None:
        for widget in self._widgets:
            # Register session parameters
            registered = []
            for parameter, session_object in widget.session_objects.items():
                # Prevent objects from being registered twice
                if id(session_object) in registered:
                    continue
                renderer.register_session_parameter(
                    route=self._route,
                    parameter=session_object.parameter,
                    target=session_object.component,
                    target_level=session_object.target_level,
                )
                registered.append(id(session_object))
            # Register callbacks
            registered = []
            for _, control in widget.controls.items():
                # Prevent objects from being registered twice
                if id(control) in registered:
                    continue
                renderer.register_callback(
                    context=control.context,
                    event=control.event,
                    fn=partial(control.callback, renderer),
                    source=control.source,
                    target=control.target,
                    target_level=control.target_level,
                )
                registered.append(id(control))
            # Register dialogs
            if widget.type == WidgetType.DIALOG:
                renderer.register_dialog(
                    dialog_id=widget.id,
                    dialog_content=widget.widget,
                )
                registered.append(id(session_object))
