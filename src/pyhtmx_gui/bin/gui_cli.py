#!/usr/bin/env python3
import typer
from typing import Optional


def run_app(
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> None:
    from pyhtmx_gui import app
    app.run(host=host, port=port)


def main() -> None:
    typer.run(run_app)


if __name__ == "__main__":
    main()
