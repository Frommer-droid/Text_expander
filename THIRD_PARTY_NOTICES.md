# Third-Party Notices

Text_expander source code is distributed under the MIT License. The Windows
release also bundles third-party runtime components listed below.

This notice is not a legal opinion. It documents the dependency/license state
used by this repository and release tooling.

## Runtime Components

| Component | Used for | License | Bundled in release |
| --- | --- | --- | --- |
| Python 3.12 | Python runtime and standard library | Python Software Foundation License | Yes |
| PySide6, PySide6_Essentials, PySide6_Addons, shiboken6 | Qt bindings and Qt runtime for the GUI | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only; this project uses the LGPL-3.0 option | Yes |
| pynput | Keyboard listener and keyboard/mouse backend selection | LGPLv3 | Yes |
| six | Runtime dependency of pynput | MIT | Yes |
| pywin32 | Windows APIs used by window filtering, shortcuts and clipboard integration | Python Software Foundation License / bundled BSD-style notices | Yes |
| psutil | Process metadata for active-window filtering | BSD-3-Clause | Yes |
| pyperclip | Clipboard text operations | BSD License | Yes |
| PyInstaller bootloader | Starts the frozen executable | GPL-2.0-or-later WITH Bootloader-exception | Yes, as part of the generated executable |
| Inno Setup runtime | Generated Windows installer/uninstaller | Inno Setup License | Yes, in the setup executable |

Build and test tools such as `pytest`, `ruff`, `pyinstaller-hooks-contrib`,
`pefile`, `altgraph` and `packaging` are development dependencies and are not
intended to be shipped as application runtime modules. Verify the applicable Inno Setup license before distributing an installer.

## Qt Module Audit

Source imports found in the application:

- `PySide6.QtCore`
- `PySide6.QtGui`
- `PySide6.QtWidgets`

The application does not use Qt Virtual Keyboard, Qt QML, Qt Quick, Qt
PDF, Qt SVG, Qt WebEngine, Qt Charts, Qt Multimedia, Qt Quick 3D, Qt HTTP
Server, Qt MQTT, Qt Network Authorization, Qt Graphs or Qt Wayland Compositor
APIs.

`Qt6Pdf.dll` and `Qt6Svg.dll` can still appear in the release because
PyInstaller collects Qt image/icon plugins such as `qpdf.dll`, `qsvg.dll` and
`qsvgicon.dll` through `QtGui`. They are not GPL-only modules in the Qt 6.11
licensing list checked for this release.

The release tooling explicitly excludes the Qt Virtual Keyboard runtime pulled
by PyInstaller's generic Qt plugin collection:

- `PySide6/Qt6VirtualKeyboard.dll`
- `PySide6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll`
- `PySide6/plugins/virtualkeyboard/`
- `PySide6/qml/QtQuick/VirtualKeyboard/`

The same post-build cleanup also removes the QML/Quick DLL stack that is pulled
only through Qt Virtual Keyboard in this application:

- `PySide6/Qt6Qml.dll`
- `PySide6/Qt6QmlMeta.dll`
- `PySide6/Qt6QmlModels.dll`
- `PySide6/Qt6QmlWorkerScript.dll`
- `PySide6/Qt6Quick.dll`

If a future feature starts using QML, Quick or Virtual Keyboard, this audit and
the PyInstaller cleanup rules must be revisited before publishing a release.

## LGPL Compliance Notes

The Windows release is built as an onedir bundle with Qt/PySide6 libraries kept
as separate files under `_internal/PySide6`. Recipients must not be restricted
from replacing or debugging LGPL-covered library components for their own use.

The release includes this file, the project `LICENSE`, and the `licenses/`
directory with license texts/notices for LGPL/GPL and bundled Python packages.

Relevant source links:

- Qt licensing: https://doc.qt.io/qt-6/licensing.html
- Qt LGPL/GPL obligations: https://www.qt.io/development/open-source-lgpl-obligations
- PySide6 package metadata: https://pypi.org/project/PySide6/
- PyInstaller license: https://pyinstaller.org/en/stable/license.html
- GNU LGPLv3: https://www.gnu.org/licenses/lgpl-3.0.html
