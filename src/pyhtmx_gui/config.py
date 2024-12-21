import os
import sys
if sys.version_info.minor < 11:
    import tomli as tomllib
else:
    import tomllib

APP_DIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(APP_DIR, "config", "config.toml"), "rb") as f:
    config_data = tomllib.load(f)
