# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

block_cipher = None

# ========================================================
# 🔧 CONFIGURATION SECTION
# ========================================================
APP_NAME = 'Text_expander'
MAIN_SCRIPT = 'Text_expander.pyw'  # e.g., '../main.py'
ICON_FILE = 'logo.ico'      # e.g., '../logo.ico' or None

# List of hidden imports (modules that PyInstaller cannot detect)
HIDDEN_IMPORTS = [
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
    'win32gui',
    'win32con',
    'win32api',
    'ctypes',
    'psutil',
    'pyperclip',
]

# List of extra data files to include INSIDE the exe (src, dst)
# Note: For external config files, use post_build.py instead.
ADDED_FILES = [
    # ('../README.md', '.'),
]
# ========================================================

spec_path = os.path.abspath(sys.argv[0])
spec_dir = os.path.dirname(spec_path)
project_root = os.path.abspath(os.path.join(spec_dir, '..'))
sys.path.insert(0, spec_dir)

from release_packaging import (  # noqa: E402
    filter_pyinstaller_toc,
    validate_pyinstaller_binary_origins,
)

# Resolve paths
script_path = os.path.join(project_root, MAIN_SCRIPT)
icon_path = os.path.join(project_root, ICON_FILE) if ICON_FILE else None
pyside_runtime_dir = Path(sys.prefix) / "Lib" / "site-packages" / "PySide6"
pyside_msvc_runtime = [
    (str(path), ".")
    for path in pyside_runtime_dir.glob("*.dll")
    if path.name.lower().startswith(("concrt140", "msvcp140", "vcruntime140"))
]
if not pyside_msvc_runtime:
    raise RuntimeError(f"Не найден MSVC runtime PySide6: {pyside_runtime_dir}")

a = Analysis(
    [script_path],
    pathex=[project_root],
    binaries=pyside_msvc_runtime,
    datas=ADDED_FILES,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.binaries, removed_qt_binaries = filter_pyinstaller_toc(a.binaries)
a.datas, removed_qt_datas = filter_pyinstaller_toc(a.datas)
trusted_binary_roots = validate_pyinstaller_binary_origins(a.binaries, project_root)
print(
    "[SECURITY] Проверены источники native-библиотек. "
    f"Доверенных корней: {len(trusted_binary_roots)}"
)
if removed_qt_binaries or removed_qt_datas:
    print(
        "[INFO] Excluded unused Qt Virtual Keyboard/QML runtime files: "
        f"{len(removed_qt_binaries) + len(removed_qt_datas)}"
    )

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True if you want a terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
