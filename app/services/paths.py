import sys
from pathlib import Path


def get_project_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def get_application_path():
    return str(get_project_root())


def resource_path(relative_path):
    return str(get_project_root() / relative_path)
