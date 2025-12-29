from functools import partial

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.windows_api import get_active_window_class, get_active_window_title
from app.ui.snippet_tree_widget import SnippetTreeWidget
from app.version import __version__


class UiSetupMixin:
    def _create_widgets(self):
        self.tabs = QTabWidget()
        self.main_tab = QWidget()
        self.about_tab = QWidget()
        self.system_tab = self._create_system_tab()
        self.tabs.addTab(self.main_tab, "Основная функция")
        self.tabs.addTab(self.system_tab, "Система")
        self.tabs.addTab(self.about_tab, "О программе")
        self.setCentralWidget(self.tabs)
        self.snippet_tree_widget = SnippetTreeWidget()
        self.snippet_tree_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.snippet_tree_widget.setHeaderHidden(True)
        self.snippet_tree_widget.setColumnCount(2)
        header = self.snippet_tree_widget.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.snippet_tree_widget.setColumnWidth(1, 32)
        self.control_panel = QWidget()
        self.editor_group = QGroupBox("Редактор")
        self.category_label = QLabel("Категория:")
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.abbreviation_label = QLabel("Аббревиатура (например, .ab):")
        self.abbreviation_input = QLineEdit()
        self.text_label = QLabel("Текст для вставки:")
        self.text_input = QTextEdit()

        # Группа фильтра окна для сниппета
        self.window_filter_group = QGroupBox("Фильтр по окну (опционально)")
        self.window_title_label = QLabel("Заголовок окна:")
        self.window_title_input = QLineEdit()
        self.window_title_input.setPlaceholderText("Например: Notepad, Word")
        self.window_class_label = QLabel("Класс окна:")
        self.window_class_input = QLineEdit()
        self.window_class_input.setPlaceholderText("Например: Notepad, XLMAIN")
        self.match_mode_label = QLabel("Режим сопоставления:")
        self.match_mode_combo = QComboBox()
        self.match_mode_combo.addItems(
            ["Содержит (contains)", "Точное совпадение (exact)"]
        )
        self.capture_window_button = QPushButton("Захватить текущее окно")
        self.capture_window_button.setToolTip("Заполнит поля данными активного окна")

        self.mgmt_group = QGroupBox("Управление списком")
        self.new_category_button = QPushButton("Новая категория")
        self.new_snippet_button = QPushButton("Новый сниппет")
        self.rename_button = QPushButton("Переименовать")
        self.delete_button = QPushButton("Удалить")
        self.delete_button.setObjectName("warning_btn")
        self.save_button = QPushButton("Сохранить сниппет")
        self.save_button.setObjectName("start_btn")
        self.about_text = QTextEdit()
        self.about_text.setReadOnly(True)
        self.about_text.setText(
            f"""
            <h1>Text expander v{__version__} (упрощенный интерфейс)</h1>
            <p>Это приложение позволяет создавать и управлять текстовыми сниппетами в удобной древовидной структуре.</p>
            <h3>Как это работает:</h3>
            <ol>
                <li><b>Запустите приложение:</b> При первом запуске Windows запросит разрешение на запуск от имени администратора. Это необходимо для стабильной работы со всеми программами.</li>
                <br>
                <li><b>Создайте сниппет:</b> Добавьте категории и сниппеты через интерфейс.</li>
                <br>
                <li><b>Сохраните сниппет:</b> После нажатия кнопки <b>"Сохранить сниппет"</b> изменения автоматически сохраняются в файл и применяются мгновенно.</li>
                <br>
                <li><b>Используйте:</b> Вводите аббревиатуру и нажимайте пробел - текст будет автоматически заменён.</li>
            </ol>
            <h3>Управление окном:</h3>
            <ul>
                <li><b>Левый клик по кнопке минимизации</b> - сворачивание на панель задач</li>
                <li><b>Левый клик по крестику</b> - полное закрытие приложения</li>
                <li><b>Правый клик по крестику</b> - сворачивание в системный трей (работа в фоне)</li>
            </ul>
            <p><b>Новое в v5.14:</b></p>
            <ul>
                <li>Сниппеты сопоставляются по скан-кодам, независимо от раскладки.</li>
                <li>Код приложения разделён на модули для удобства сопровождения.</li>
            </ul>
            """
        )
        self.about_text.setStyleSheet("font-size: 14pt;")

    def _create_layout(self):
        control_layout = QVBoxLayout(self.control_panel)
        editor_layout = QVBoxLayout(self.editor_group)
        editor_layout.addWidget(self.category_label)
        editor_layout.addWidget(self.category_combo)
        editor_layout.addWidget(self.abbreviation_label)
        editor_layout.addWidget(self.abbreviation_input)
        editor_layout.addWidget(self.text_label)
        editor_layout.addWidget(self.text_input)
        editor_layout.setStretchFactor(self.text_input, 1)

        # Layout для группы фильтра окна
        window_filter_layout = QVBoxLayout(self.window_filter_group)
        window_filter_layout.addWidget(self.window_title_label)
        window_filter_layout.addWidget(self.window_title_input)
        window_filter_layout.addWidget(self.window_class_label)
        window_filter_layout.addWidget(self.window_class_input)
        window_filter_layout.addWidget(self.match_mode_label)
        window_filter_layout.addWidget(self.match_mode_combo)
        window_filter_layout.addWidget(self.capture_window_button)

        mgmt_layout = QHBoxLayout(self.mgmt_group)
        mgmt_layout.addWidget(self.new_category_button)
        mgmt_layout.addWidget(self.new_snippet_button)
        mgmt_layout.addWidget(self.rename_button)
        mgmt_layout.addWidget(self.delete_button)
        control_layout.addWidget(self.editor_group)
        control_layout.addWidget(self.window_filter_group)
        control_layout.addWidget(self.mgmt_group)
        control_layout.addWidget(self.save_button)
        control_layout.setStretchFactor(self.editor_group, 1)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.snippet_tree_widget)
        self.splitter.addWidget(self.control_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)
        main_tab_layout = QHBoxLayout(self.main_tab)
        main_tab_layout.addWidget(self.splitter)
        about_layout = QVBoxLayout(self.about_tab)
        about_layout.addWidget(self.about_text)

    def _create_system_tab(self):
        """Создает вкладку с системными настройками."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Группа автозапуска
        autostart_group = QGroupBox("Автозапуск")
        autostart_layout = QVBoxLayout(autostart_group)

        # Чекбокс автозапуска
        self.autostart_check = QCheckBox("Автозапуск при входе в Windows")

        # Чекбокс запуска свернутым
        self.start_minimized_check = QCheckBox("Запускать свернутым в трей")

        autostart_layout.addWidget(self.autostart_check)
        autostart_layout.addWidget(self.start_minimized_check)
        layout.addWidget(autostart_group)

        layout.addStretch()
        return tab

    def _apply_styles(self):
        style_sheet = """
        QMainWindow, QWidget { background-color: #17212B; color: #FFFFFF; font-family: Aptos, sans-serif; font-size: 15pt; }
        QStatusBar { background-color: #17212B; color: #3AE2CE; font-size: 12pt; }
        QStatusBar::item { border: 0px; }
        QTabWidget::pane { border: 1px solid white; border-radius: 5px; background-color: #17212B; }
        QTabBar::tab { background: #0E1621; color: white; border: 1px solid #3AE2CE; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 5px; margin-right: 2px; }
        QTabBar::tab:selected { background: #17212B; border-bottom: 1px solid #17212B; }
        QTabBar::tab:hover { background: #4B82E5; }
        QLabel { color: #3AE2CE; padding: 2px; }
        QGroupBox { border: 1px solid white; border-radius: 5px; margin-top: 1em; padding: 5px 5px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; font-weight: bold; color: white; }
        QLineEdit, QTextEdit, QComboBox { background-color: #0E1621; border: 1px solid #3AE2CE; border-radius: 4px; padding: 5px; color: white; }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView { background-color: #0E1621; color: white; border: 1px solid #3AE2CE; selection-background-color: #4B82E5; selection-color: white; }
        QComboBox QAbstractItemView::item:hover { background-color: #3AE2CE; color: black; }
        QTreeWidget { background-color: #0E1621; border: 1px solid white; }
        QTreeWidget::item:selected { background-color: #3AE2CE; color: black; }
        QTreeWidget::item { padding: 5px; }
        QSplitter::handle { background-color: #3AE2CE; }
        QSplitter::handle:horizontal { width: 5px; }
        QPushButton { background-color: #4B82E5; color: white; border: none; border-radius: 4px; height: 40px; padding: 5px; }
        QPushButton:hover { background-color: #78A3F2; }
        QPushButton:pressed { background-color: #194595; }
        QPushButton#warning_btn { background-color: #BF8255; color: white; }
        QPushButton#warning_btn:hover { background-color: #FFCD71; color: black; }
        QPushButton#warning_btn:pressed { background-color: #A67315; }
        QPushButton#start_btn { background-color: #6AF1E2; color: black; font-weight: bold; height: 48px; }
        QPushButton#start_btn:hover { background-color: #8EF1E6; }
        QPushButton#start_btn:pressed { background-color: #139385; }
        QMenu { background-color: #0E1621; border: 1px solid #3AE2CE; color: white; }
        QMenu::item:selected { background-color: #4B82E5; color: white; }
        QMessageBox { background-color: #17212B; }
        QMessageBox QLabel { color: white; }
        QMessageBox QPushButton { background-color: #4B82E5; color: white; border-radius: 4px; height: 35px; min-width: 100px; padding: 5px 15px; }
        QMessageBox QPushButton:hover { background-color: #78A3F2; }
        QMessageBox QPushButton:pressed { background-color: #194595; }
        """
        self.setStyleSheet(style_sheet)

    def _setup_status_bar(self, is_admin):
        self.admin_status_label = QLabel()
        if is_admin:
            self.admin_status_label.setText("Права администратора")
            self.admin_status_label.setStyleSheet(
                "color: #3AE2CE; padding-right: 10px;"
            )
        else:
            self.admin_status_label.setText("Обычные права (могут быть проблемы)")
            self.admin_status_label.setStyleSheet(
                "color: #BF8255; padding-right: 10px;"
            )
        self.statusBar().addPermanentWidget(self.admin_status_label)

    def _connect_signals(self):
        self.snippet_tree_widget.currentItemChanged.connect(self._display_item_details)
        self.snippet_tree_widget.snippetMoved.connect(
            self._move_snippet_between_categories
        )
        self.snippet_tree_widget.categoryMoved.connect(
            self._move_category_between_categories
        )
        self.snippet_tree_widget.customContextMenuRequested.connect(
            self._show_tree_context_menu
        )
        self.snippet_tree_widget.itemExpanded.connect(self._on_item_expanded)
        self.snippet_tree_widget.itemCollapsed.connect(self._on_item_collapsed)
        self.new_category_button.clicked.connect(self._add_new_category)
        self.new_snippet_button.clicked.connect(self._clear_fields_for_new_snippet)
        self.rename_button.clicked.connect(self._rename_item)
        self.delete_button.clicked.connect(self._delete_item)
        self.save_button.clicked.connect(self._save_snippet)
        self.capture_window_button.clicked.connect(self._capture_current_window)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.autostart_check.stateChanged.connect(self.on_autostart_changed)
        self.start_minimized_check.stateChanged.connect(self.on_start_minimized_changed)

    def _show_tree_context_menu(self, position):
        item = self.snippet_tree_widget.itemAt(position)
        if not item or not self._is_category_tree_item(item):
            return

        category_path = tuple(self._item_path(item) or ())
        if not category_path:
            return

        menu = QMenu(self)

        # Пункт настройки фильтра окна
        filter_action = menu.addAction("Настроить фильтр окна...")
        filter_action.triggered.connect(
            partial(self._show_category_filter_dialog, category_path)
        )

        # Пункт вытаскивания в корень (только для вложенных категорий)
        if item.parent() is not None and len(category_path) > 1:
            menu.addSeparator()
            pull_action = menu.addAction("Вытащить в корень")
            pull_action.triggered.connect(
                partial(self._pull_category_to_root, category_path)
            )

        self.snippet_tree_widget.setCurrentItem(item)
        global_pos = self.snippet_tree_widget.viewport().mapToGlobal(position)
        menu.exec(global_pos)

    def _show_category_filter_dialog(self, category_path):
        """Показывает диалог настройки window_filter для категории."""
        category_payload = self._get_category_payload(category_path)
        if not category_payload:
            return

        current_filter = category_payload.get("window_filter", {})
        current_title = current_filter.get("title", "") if current_filter else ""
        current_class = current_filter.get("class", "") if current_filter else ""
        current_mode = (
            current_filter.get("match_mode", "contains") if current_filter else "contains"
        )

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Фильтр окна для категории: {' / '.join(category_path)}")
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)

        title_input = QLineEdit(current_title)
        title_input.setPlaceholderText("Часть заголовка окна")
        layout.addRow("Заголовок окна:", title_input)

        class_input = QLineEdit(current_class)
        class_input.setPlaceholderText("Класс окна (например, Notepad)")
        layout.addRow("Класс окна:", class_input)

        mode_combo = QComboBox()
        mode_combo.addItems(["Содержит (contains)", "Точное совпадение (exact)"])
        mode_combo.setCurrentIndex(1 if current_mode == "exact" else 0)
        layout.addRow("Режим:", mode_combo)

        # Кнопка захвата окна
        capture_btn = QPushButton("Захватить текущее окно (3 сек)")

        def do_capture():
            capture_btn.setEnabled(False)
            capture_btn.setText("Переключитесь на нужное окно...")
            QTimer.singleShot(3000, lambda: finish_capture())

        def finish_capture():
            title = get_active_window_title()
            wclass = get_active_window_class()
            if title:
                title_input.setText(title)
            if wclass:
                class_input.setText(wclass)
            capture_btn.setText("Захватить текущее окно (3 сек)")
            capture_btn.setEnabled(True)
            dialog.activateWindow()

        capture_btn.clicked.connect(do_capture)
        layout.addRow("", capture_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        # Кнопка очистки
        clear_btn = buttons.addButton(
            "Очистить фильтр", QDialogButtonBox.ButtonRole.ResetRole
        )

        def clear_filter():
            title_input.clear()
            class_input.clear()
            mode_combo.setCurrentIndex(0)

        clear_btn.clicked.connect(clear_filter)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_title = title_input.text().strip()
            new_class = class_input.text().strip()
            new_mode = "exact" if mode_combo.currentIndex() == 1 else "contains"

            if new_title or new_class:
                category_payload["window_filter"] = {
                    "title": new_title,
                    "class": new_class,
                    "match_mode": new_mode,
                }
            else:
                # Удаляем фильтр если оба поля пустые
                category_payload.pop("window_filter", None)

            self._save_snippets_to_file()
            self.reload_listener_snippets()
            self.statusBar().showMessage(
                f"Фильтр категории '{' / '.join(category_path)}' обновлён", 3000
            )

    def _pull_category_to_root(self, category_path):
        path = tuple(category_path or ())
        if len(path) <= 1:
            return
        self._move_category_between_categories(path, ())
