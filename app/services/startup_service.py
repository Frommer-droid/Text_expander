import ctypes
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import uuid

USER_APPDATA_FLAG = "--user-appdata"
STARTUP_RELATIVE_PATH = os.path.join(
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
)
ORIGINAL_APPDATA = os.environ.get("APPDATA", "")
_EFFECTIVE_APPDATA = None
FOLDERID_STARTUP = "B97D20BB-F46A-4C97-BA10-5E3608430854"
FOLDERID_COMMON_STARTUP = "82A5EA35-D9CD-47C5-9629-E15D2F714E6E"


@dataclass(frozen=True)
class ShortcutLaunchSpec:
    target_path: str
    arguments: str = ""
    working_directory: str = ""
    icon_location: str = ""


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def _clean_arg(value):
    if value and value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def apply_user_appdata_override():
    """
    Извлекает путь APPDATA из аргументов и очищает sys.argv от служебных флагов.
    """
    global _EFFECTIVE_APPDATA
    if _EFFECTIVE_APPDATA is not None:
        return _EFFECTIVE_APPDATA

    user_appdata = None
    cleaned_args = [sys.argv[0]] if sys.argv else []
    skip_next = False

    for arg in sys.argv[1:]:
        if skip_next:
            user_appdata = _clean_arg(arg)
            skip_next = False
            continue

        if arg == USER_APPDATA_FLAG:
            skip_next = True
            continue

        if arg.startswith(f"{USER_APPDATA_FLAG}="):
            user_appdata = _clean_arg(arg.split("=", 1)[1])
            continue

        cleaned_args.append(arg)

    if cleaned_args:
        sys.argv[:] = cleaned_args

    _EFFECTIVE_APPDATA = user_appdata or ORIGINAL_APPDATA
    return _EFFECTIVE_APPDATA


def get_effective_appdata():
    return apply_user_appdata_override()


def _startup_path_from_root(root_path):
    if not root_path:
        return None
    return os.path.normpath(os.path.join(root_path, STARTUP_RELATIVE_PATH))


def _guid_from_string(value):
    parsed = uuid.UUID(value)
    tail = parsed.bytes[8:]
    return GUID(
        parsed.time_low,
        parsed.time_mid,
        parsed.time_hi_version,
        (ctypes.c_ubyte * 8).from_buffer_copy(tail),
    )


def get_known_folder_path(folder_id):
    """
    Возвращает путь Windows Known Folder через SHGetKnownFolderPath.
    """
    try:
        guid = _guid_from_string(folder_id)
        path_ptr = ctypes.c_void_p()
        result = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(guid),
            0,
            None,
            ctypes.byref(path_ptr),
        )
        if result != 0 or not path_ptr.value:
            return None
        try:
            return ctypes.wstring_at(path_ptr.value)
        finally:
            ctypes.windll.ole32.CoTaskMemFree(path_ptr)
    except Exception:
        return None


def get_startup_locations():
    locations = []
    effective_appdata = get_effective_appdata()
    fallback_user_startup_dir = _startup_path_from_root(effective_appdata)
    fallback_common_startup_dir = _startup_path_from_root(os.environ.get("PROGRAMDATA", ""))
    for path in (
        get_known_folder_path(FOLDERID_STARTUP),
        get_known_folder_path(FOLDERID_COMMON_STARTUP),
        fallback_user_startup_dir,
        fallback_common_startup_dir,
    ):
        if path and path not in locations:
            locations.append(path)
    return locations


def get_launch_executable(prefer_windowed=False, script_path=None):
    """
    Возвращает подходящий интерпретатор для запуска текущего скрипта.

    Для `.pyw` в dev-режиме предпочитает `pythonw.exe`, чтобы не открывать
    отдельное консольное окно.
    """
    if (
        not prefer_windowed
        or getattr(sys, "frozen", False)
        or not (script_path or sys.argv)
        or Path(script_path or sys.argv[0]).suffix.lower() != ".pyw"
    ):
        return sys.executable

    executable_path = Path(sys.executable)
    if executable_path.name.lower() == "pythonw.exe":
        return str(executable_path)

    if executable_path.name.lower() != "python.exe":
        return sys.executable

    windowed_path = executable_path.with_name("pythonw.exe")
    if windowed_path.exists():
        return str(windowed_path)

    return sys.executable


def get_autostart_launch_spec(entry_path):
    """
    Возвращает параметры ярлыка для автозагрузки.
    """
    if getattr(sys, "frozen", False):
        executable_path = str(Path(sys.executable).resolve())
        executable_dir = str(Path(executable_path).parent)
        return ShortcutLaunchSpec(
            target_path=executable_path,
            working_directory=executable_dir,
            icon_location=executable_path,
        )

    resolved_entry_path = str(Path(entry_path).resolve())
    launch_executable = get_launch_executable(
        prefer_windowed=True,
        script_path=resolved_entry_path,
    )
    working_directory = str(Path(resolved_entry_path).parent)
    icon_path = str(Path(working_directory) / "logo.ico")
    if not os.path.exists(icon_path):
        icon_path = launch_executable

    return ShortcutLaunchSpec(
        target_path=launch_executable,
        arguments=subprocess.list2cmdline([resolved_entry_path]),
        working_directory=working_directory,
        icon_location=icon_path,
    )


def relaunch_in_windowed_mode():
    """
    Перезапускает `.pyw` через `pythonw.exe`, если текущий запуск идёт через
    `python.exe`.
    """
    if getattr(sys, "frozen", False) or not sys.argv:
        return False

    launch_executable = get_launch_executable(
        prefer_windowed=True,
        script_path=sys.argv[0],
    )
    if not launch_executable or os.path.normcase(launch_executable) == os.path.normcase(
        sys.executable
    ):
        return False

    script_path = str(Path(sys.argv[0]).resolve())
    subprocess.Popen([launch_executable, script_path, *sys.argv[1:]], cwd=os.getcwd())
    return True


def run_as_admin():
    """
    Перезапускает скрипт с правами администратора, если он еще не запущен с ними.
    Возвращает True, если скрипт запущен с правами администратора, иначе False.
    """
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

    if not is_admin:
        params = []
        if not getattr(sys, "frozen", False) and sys.argv:
            params.append(str(Path(sys.argv[0]).resolve()))

        effective_appdata = get_effective_appdata()
        if effective_appdata:
            params.append(f'{USER_APPDATA_FLAG}="{effective_appdata}"')

        if len(sys.argv) > 1:
            params.extend(sys.argv[1:])

        param_line = subprocess.list2cmdline(params) if params else ""
        launch_executable = get_launch_executable(
            prefer_windowed=True,
            script_path=sys.argv[0] if sys.argv else None,
        )
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", launch_executable, param_line, None, 1
        )
        return False
    return True
