import ctypes
import os
import subprocess
import sys

USER_APPDATA_FLAG = "--user-appdata"
STARTUP_RELATIVE_PATH = os.path.join(
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
)
ORIGINAL_APPDATA = os.environ.get("APPDATA", "")
_EFFECTIVE_APPDATA = None


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


def get_startup_locations():
    locations = []
    effective_appdata = get_effective_appdata()
    user_startup_dir = _startup_path_from_root(effective_appdata)
    common_startup_dir = _startup_path_from_root(os.environ.get("PROGRAMDATA", ""))
    for path in (user_startup_dir, common_startup_dir):
        if path and path not in locations:
            locations.append(path)
    return locations


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
            params.append(sys.argv[0])

        effective_appdata = get_effective_appdata()
        if effective_appdata:
            params.append(f'{USER_APPDATA_FLAG}="{effective_appdata}"')

        if len(sys.argv) > 1:
            params.extend(sys.argv[1:])

        param_line = subprocess.list2cmdline(params) if params else ""
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, param_line, None, 1
        )
        return False
    return True
