# PyHTMX GUI Dev Guide

## Setting up

Before start editing, testing and debugging the code, install the provided packages as editable.

First clone the repository:

```bash
git clone https://github.com/femelo/pyhtmx-gui-client.git &&
cd pyhtmx-gui-client
```

From the cloned repository directory, assuming the development Python virtual
environment is already activated, install the package as editable with:

```bash
python3 -m pip install -e .
```

For editing and testing the provided skill example, also install it.

```bash
cd skill-pyhtmx-hello-world &&
python3 -m pip install -e .
```

## Install the pyhtmx library
```bash
python3 -m pip install pyhtmx-lib
```

## Starting the application

For launching the GUI application, start it with the command line script as below. It will automatically start the pyhtxm-gui client on http://localhost:8000. If preferred, change the network adress in `config.toml` (/pyhtmx_gui/config/config.toml)

```bash
pyhtmx-gui
```
