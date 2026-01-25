try:
    import win32gui
    import win32process
    import win32con
    import psutil

    WIN_LIBS_LOADED = True
except ImportError:
    WIN_LIBS_LOADED = False
    win32con = None

WM_NCRBUTTONDOWN = 0x00A4
WM_NCRBUTTONUP = 0x00A5
WM_SYSCOMMAND = 0x0112
SC_CLOSE = 0xF060
SC_MINIMIZE = 0xF020
HTCLOSE = 0x14

if WIN_LIBS_LOADED:
    WM_NCRBUTTONDOWN = getattr(win32con, "WM_NCRBUTTONDOWN", WM_NCRBUTTONDOWN)
    WM_NCRBUTTONUP = getattr(win32con, "WM_NCRBUTTONUP", WM_NCRBUTTONUP)
    WM_SYSCOMMAND = getattr(win32con, "WM_SYSCOMMAND", WM_SYSCOMMAND)
    SC_CLOSE = getattr(win32con, "SC_CLOSE", SC_CLOSE)
    SC_MINIMIZE = getattr(win32con, "SC_MINIMIZE", SC_MINIMIZE)
    HTCLOSE = getattr(win32con, "HTCLOSE", HTCLOSE)


def get_active_process_name():
    """Возвращает имя активного процесса в нижнем регистре (например, 'winword.exe')."""
    if not WIN_LIBS_LOADED:
        return None
    try:
        pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
        return psutil.Process(pid[-1]).name().lower()
    except Exception:
        return None


def get_active_window_title():
    """Возвращает заголовок активного окна."""
    if not WIN_LIBS_LOADED:
        return None
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            return win32gui.GetWindowText(hwnd)
        return None
    except Exception:
        return None


def get_active_window_class():
    """Возвращает имя класса активного окна."""
    if not WIN_LIBS_LOADED:
        return None
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            return win32gui.GetClassName(hwnd)
        return None
    except Exception:
        return None
