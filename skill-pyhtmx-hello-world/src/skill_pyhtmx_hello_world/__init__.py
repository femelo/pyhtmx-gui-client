from __future__ import annotations
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler


class HelloWorldSkill(OVOSSkill):
    def __init__(
        self: HelloWorldSkill,
        skill_id: str = "skill-pyhtmx-hello-world",
    ):
        super().__init__(skill_id=skill_id)

    @intent_handler("pyhtmx.intent")
    def handle_hello_world(self: HelloWorldSkill):
        text = "Hello world, this is a new GUI"

        self.gui["title"] = "PyHTMX-based Hello World"
        self.gui["text"] = text
        self.gui.show_pages(
            [
                "hello_world_page1",
                "hello_world_page2",
                "hello_world_page3",
            ],
            override_idle=60,
        )

        self.speak(text)
