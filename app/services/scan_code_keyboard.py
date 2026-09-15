import ctypes
import logging
from ctypes import wintypes

_USER32 = ctypes.WinDLL("user32", use_last_error=True)

try:
    ULONG_PTR = wintypes.ULONG_PTR
except AttributeError:
    ULONG_PTR = ctypes.c_size_t

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

MAPVK_VK_TO_VSC = 0

SC_BACKSPACE = 0x0E
SC_SPACE = 0x39
SC_DOT = 0x34
SC_SLASH = 0x35
SC_LEFT = 0x4B
SC_DELETE = 0x53
SC_INSERT = 0x52
SC_CTRL = 0x1D
SC_SHIFT = 0x2A
SC_V = 0x2F

EXTENDED_SCANCODES = {SC_LEFT, SC_DELETE, SC_INSERT}

_EN_BASE = {
    "`": 0x29,
    "1": 0x02,
    "2": 0x03,
    "3": 0x04,
    "4": 0x05,
    "5": 0x06,
    "6": 0x07,
    "7": 0x08,
    "8": 0x09,
    "9": 0x0A,
    "0": 0x0B,
    "-": 0x0C,
    "=": 0x0D,
    "q": 0x10,
    "w": 0x11,
    "e": 0x12,
    "r": 0x13,
    "t": 0x14,
    "y": 0x15,
    "u": 0x16,
    "i": 0x17,
    "o": 0x18,
    "p": 0x19,
    "[": 0x1A,
    "]": 0x1B,
    "\\": 0x2B,
    "a": 0x1E,
    "s": 0x1F,
    "d": 0x20,
    "f": 0x21,
    "g": 0x22,
    "h": 0x23,
    "j": 0x24,
    "k": 0x25,
    "l": 0x26,
    ";": 0x27,
    "'": 0x28,
    "z": 0x2C,
    "x": 0x2D,
    "c": 0x2E,
    "v": 0x2F,
    "b": 0x30,
    "n": 0x31,
    "m": 0x32,
    ",": 0x33,
    ".": 0x34,
    "/": 0x35,
}

_EN_SHIFTED = {
    "~": "`",
    "!": "1",
    "@": "2",
    "#": "3",
    "$": "4",
    "%": "5",
    "^": "6",
    "&": "7",
    "*": "8",
    "(": "9",
    ")": "0",
    "_": "-",
    "+": "=",
    "{": "[",
    "}": "]",
    "|": "\\",
    ":": ";",
    "\"": "'",
    "<": ",",
    ">": ".",
    "?": "/",
}

_EN_MAP = dict(_EN_BASE)
_EN_MAP.update({symbol: _EN_BASE[base] for symbol, base in _EN_SHIFTED.items()})

_RU_EXTRA = {
    "ё": 0x29,
    "й": 0x10,
    "ц": 0x11,
    "у": 0x12,
    "к": 0x13,
    "е": 0x14,
    "н": 0x15,
    "г": 0x16,
    "ш": 0x17,
    "щ": 0x18,
    "з": 0x19,
    "х": 0x1A,
    "ъ": 0x1B,
    "ф": 0x1E,
    "ы": 0x1F,
    "в": 0x20,
    "а": 0x21,
    "п": 0x22,
    "р": 0x23,
    "о": 0x24,
    "л": 0x25,
    "д": 0x26,
    "ж": 0x27,
    "э": 0x28,
    "я": 0x2C,
    "ч": 0x2D,
    "с": 0x2E,
    "м": 0x2F,
    "и": 0x30,
    "т": 0x31,
    "ь": 0x32,
    "б": 0x33,
    "ю": 0x34,
    "№": 0x04,
}

_RU_MAP = dict(_EN_MAP)
_RU_MAP.update(_RU_EXTRA)
_RU_MAP["."] = SC_SLASH
_RU_MAP[","] = SC_SLASH


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", _KEYBDINPUT),
        ("mi", _MOUSEINPUT),
        ("hi", _HARDWAREINPUT),
    ]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]


_USER32.SendInput.argtypes = (
    wintypes.UINT,
    ctypes.POINTER(_INPUT),
    ctypes.c_int,
)
_USER32.SendInput.restype = wintypes.UINT

_USER32.MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
_USER32.MapVirtualKeyW.restype = wintypes.UINT


def _is_cyrillic_char(ch):
    code = ord(ch)
    return 0x0400 <= code <= 0x04FF or 0x0500 <= code <= 0x052F


def _has_latin(text):
    for ch in text:
        lower = ch.lower()
        if "a" <= lower <= "z":
            return True
    return False


def _select_layouts(abbr):
    if any(_is_cyrillic_char(ch) for ch in abbr):
        return ("ru",)
    if _has_latin(abbr):
        return ("en",)
    return ("en", "ru")


def build_scan_sequences(abbr):
    if not abbr:
        return [], set()
    layouts = _select_layouts(abbr)
    sequences = []
    seen = set()
    missing = set()
    for layout in layouts:
        mapping = _RU_MAP if layout == "ru" else _EN_MAP
        sequence = []
        ok = True
        for ch in abbr:
            key = ch.lower()
            scan_code = mapping.get(key)
            if scan_code is None:
                ok = False
                missing.add(ch)
                break
            sequence.append(scan_code)
        if ok:
            seq_key = tuple(sequence)
            if seq_key not in seen:
                seen.add(seq_key)
                sequences.append(sequence)
    return sequences, missing


def build_snippet_index(snippets):
    snippets_by_abbr = {}
    snippets_by_scan = {}
    for abbr, payload in snippets.items():
        sequences, missing = build_scan_sequences(abbr)
        if not sequences:
            details = ""
            if missing:
                details = f" (неподдерживаемые символы: {''.join(sorted(missing))})"
            logging.warning(
                "[SNIPPET] Пропуск '%s': не удалось построить скан-коды%s",
                abbr,
                details,
            )
            continue
        entry = dict(payload)
        entry["abbr"] = abbr
        entry["scan_sequences"] = [tuple(seq) for seq in sequences]
        snippets_by_abbr[abbr] = entry
        for seq_key in entry["scan_sequences"]:
            bucket = snippets_by_scan.setdefault(seq_key, [])
            if bucket:
                logging.warning(
                    "[SNIPPET] Коллизия скан-кодов: '%s' и '%s'",
                    bucket[0].get("abbr"),
                    abbr,
                )
            bucket.append(entry)
    return snippets_by_abbr, snippets_by_scan


def scan_code_from_key(key):
    scan_code = getattr(key, "scan_code", None)
    if scan_code:
        return int(scan_code)
    vk = getattr(key, "vk", None)
    if vk is None:
        key_value = getattr(key, "value", None)
        vk = getattr(key_value, "vk", None) if key_value else None
    if vk is None:
        return None
    mapped = _USER32.MapVirtualKeyW(int(vk), MAPVK_VK_TO_VSC)
    return int(mapped) if mapped else None


def is_dot_prefix(scan_codes):
    return bool(scan_codes) and scan_codes[0] in {SC_DOT, SC_SLASH}


def format_scancodes(scan_codes):
    return "-".join(f"{code:02X}" for code in scan_codes)


def _make_input(scan_code, key_up=False, extended=False):
    flags = KEYEVENTF_SCANCODE
    if key_up:
        flags |= KEYEVENTF_KEYUP
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    return _INPUT(
        type=INPUT_KEYBOARD,
        u=_INPUT_UNION(
            ki=_KEYBDINPUT(
                wVk=0,
                wScan=scan_code,
                dwFlags=flags,
                time=0,
                dwExtraInfo=0,
            )
        ),
    )


def _send_inputs(inputs):
    if not inputs:
        return
    data = (_INPUT * len(inputs))(*inputs)
    sent = _USER32.SendInput(len(data), data, ctypes.sizeof(_INPUT))
    if sent != len(data):
        error_code = ctypes.get_last_error()
        logging.warning(
            "[INPUT] SendInput отправил %d из %d (ошибка %d)",
            sent,
            len(data),
            error_code,
        )


def press_key(scan_code, extended=False):
    _send_inputs([_make_input(scan_code, key_up=False, extended=extended)])


def release_key(scan_code, extended=False):
    _send_inputs([_make_input(scan_code, key_up=True, extended=extended)])


def tap_key(scan_code, extended=False):
    _send_inputs(
        [
            _make_input(scan_code, key_up=False, extended=extended),
            _make_input(scan_code, key_up=True, extended=extended),
        ]
    )
