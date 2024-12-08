from __future__ import annotations
import flet as ft
from ovos_gui_client import global_client

# Main Flet app setup
def main(page: ft.Page):
    page.title = "OVOS Flet GUI Client"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 0
    # Set deregistering upon disconnecting
    page.on_disconnect = lambda _: global_client.deregister(page)
    # Register page
    global_client.register(page)

# Start the Flet app
ft.app(target=main, view=ft.AppView.WEB_BROWSER, web_renderer=ft.WebRenderer.HTML)

