<p align="center">
  <img src="app/assets/app-icon.svg" width="112" height="112" alt="Text Expander">
</p>

<h1 align="center">Text Expander</h1>

<p align="center"><strong>Type a short abbreviation to insert a complete phrase in the right window.</strong></p>

<p align="center"><a href="README.md">Русский</a> · <a href="https://github.com/Frommer-droid/Text_expander/releases/latest">Download the latest release</a></p>

Text Expander for Windows replaces abbreviations with reusable replies, addresses and email templates. For example, `.mail` followed by a space becomes `user@example.com`.

## Highlights

- Organize snippets in categories and subcategories; enable individual entries or complete groups.
- Match keyboard scan codes independently of the active keyboard layout.
- Limit a snippet or category to a window title and class.
- Use the system tray, pause substitutions, start with Windows and launch minimized.
- Import and export snippets, settings or a complete backup as JSON.
- Use the OneDark Pro interface with automatic display scaling and a manual adjustment.

## Quick start

Windows 10 or 11 is required. The application interface is in Russian.

1. Download and run the installer from the [latest release page](https://github.com/Frommer-droid/Text_expander/releases/latest).
2. Accept the Windows administrator elevation prompt.
3. Click **Новая категория** (New category), then **Новый сниппет** (New snippet).
4. Enter `.mail` as the abbreviation and `user@example.com` as the text, then click **Сохранить** (Save).
5. Type `.mail` in Notepad and press Space to insert the address.

For the portable edition, run `Text_expander.exe` from its extracted folder together with `_internal` and the remaining files. It does not require Python.

## Using the application

Under **Фильтр по окну** (Window filter), specify a window title or class and choose exact or substring matching. Set category filters through the category context menu; snippets without their own filter inherit the category filter.

The tray menu provides pause, snippet reload, autostart and exit. Left-clicking the close button exits the application; right-clicking it hides the window to the tray. Scaling, startup and data exchange settings are on the **Система** (System) tab.

JSON import **replaces the current data** of the selected type. Create a backup with **Экспорт всего** (Export everything) first.

## Data and limitations

Snippets (`snippets.json`), settings (`expander_settings.json`) and the log (`Text_expander.log`) live next to the application, so its folder must be writable. These files are excluded from Git. A new public build starts with empty snippets and autostart disabled.

The application uses a global keyboard hook and runs with administrator privileges. Insertion uses the clipboard; its previous text is restored if it could be read. Other clipboard managers may interfere. Use a distinctive abbreviation prefix to avoid accidental replacements.

## Run from source

Install Python 3.12 and Git, then run:

```powershell
git clone https://github.com/Frommer-droid/Text_expander.git
cd Text_expander
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Start-Process .\.venv\Scripts\pythonw.exe -ArgumentList ".\Text_expander.pyw"
```

For development:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

The [developer guide](DEVELOPER.md) covers architecture and build preparation. The [changelog](RELEASE_NOTES.md) describes released versions.

## License

The project's own code is licensed under [MIT](LICENSE). Third-party components retain their own licenses: see [Third-Party Notices](THIRD_PARTY_NOTICES.md) and the [license texts](licenses/).
