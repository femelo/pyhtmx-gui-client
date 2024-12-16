from pyhtmx import (
    Html,
    Head,
    Meta,
    Link,
    Script,
    Title,
    Body,
    Div,
    Dialog,
)

DUMMY_DOCUMENT: Html = Html(
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
                Title("PyHTMX GUI Dummy Display"),
            ]
        ),
        Body(
            [
                Div(
                    _id="root",
                    _class="flex flex-col",
                ),
                Dialog(
                    _id="dialog",
                    _class="modal",
                ),
            ],
        ),
    ],
    lang="en",
)
