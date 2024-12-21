from pyhtmx import (
    Html,
    Head,
    Meta,
    Link,
    Script,
    Title,
    Body,
    Div,
)
from config import config_data


ping_period: int = round(config_data["ping-period"])

MASTER_DOCUMENT: Html = Html(
    [
        Head(
            [
                Meta(charset="UTF-8"),
                Meta(
                    name="viewport",
                    content="width=device-width, initial-scale=1.0",
                ),
                Link(
                    href="./assets/icons/pyhtmx-favicon.svg",
                    rel="icon",
                    _type="image/x-icon",
                ),
                Link(
                    href="./assets/css/daisyui-full.min.css",
                    rel="stylesheet",
                    _type="text/css",
                ),
                Script(src="./assets/js/tailwind-play-cdn.js"),
                Script(src="./assets/js/htmx.min.js", defer="true"),
                Script(src="./assets/js/sse.js", defer="true"),
                Script(src="./assets/js/htmx-process.js", defer="true"),
                Title("PyHTMX GUI Client"),
            ]
        ),
        Body(
            Div(
                _id="session-id",
                style="display: none;",
                hx_post="/ping",
                hx_trigger=f"every {ping_period}s",
            ),  # hidden element to register session id
            hx_ext="sse",
            sse_connect="/updates",
            style="visibility: hidden;"
        ),
    ],
    lang="en",
)
