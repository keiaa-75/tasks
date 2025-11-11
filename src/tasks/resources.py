import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    else:
        # Development mode
        return Path(__file__).parent / relative_path


def get_icon_path() -> Path:
    return get_resource_path("resources/tasks.png")
