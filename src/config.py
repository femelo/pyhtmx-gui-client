import os
import tomllib

APP_DIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(APP_DIR, "config.toml"), "rb") as f:
    config_data = tomllib.load(f)
