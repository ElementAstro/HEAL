# coding: utf-8
import sys
from pathlib import Path
from PySide6.QtCore import QStandardPaths

# change DEBUG to False if you want to compile the code to exe
DEBUG = "__compiled__" not in globals()

YEAR = 2025
AUTHOR = "Max Qian"
VERSION = "1.0.0"
APP_NAME = "HEAL"
HELP_URL = "https://fluent-m3u8.org"
REPO_URL = "https://github.com/ElementAstro/HEAL"
FEEDBACK_URL = "https://github.com/ElementAstro/HEAL/issues"
RELEASE_URL = "https://github.com/ElementAstro/HEAL/releases"

CONFIG_FOLDER = Path('AppData').absolute()

if sys.platform == "win32" and not DEBUG:
    CONFIG_FOLDER = Path(QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation)) / APP_NAME

CONFIG_FILE = CONFIG_FOLDER / "config.json"

LOG_FOLDER = CONFIG_FOLDER / "Log"
LOG_FOLDER.mkdir(exist_ok=True, parents=True)

if sys.platform == "win32":
    EXE_SUFFIX = ".exe"
else:
    EXE_SUFFIX = ""
