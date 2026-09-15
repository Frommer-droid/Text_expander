from functools import partial

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.ui_scale_service import scale_px
from app.services.windows_api import get_active_window_class, get_active_window_title
from app.ui.action_icons import action_icon
from app.ui.snippet_tree_widget import SnippetTreeWidget
from app.ui.styles import ONEDARK_GREEN, ONEDARK_RED, build_app_stylesheet


class UiSetupMixin:
    def _set_action_icon(self, button, icon_name, tooltip):
        """Добавляет центрированную пиктограмму, сохраняя текст кнопки доступным."""
        button.setIcon(action_icon(icon_name))
        button.setIconSize(QSize(18, 18))
        button.setToolTip(tooltip)

    def _create_widgets(self):
        self.tabs = QTabWidget()
        self.main_tab = QWidget()
        self.system_tab = self._create_system_tab()
        self.tabs.addTab(
            self.main_tab,
            action_icon("list"),
            "Основная функция",
        )
        self.tabs.addTab(
            self.system_tab,
            action_icon("system"),
            "Система",
        )
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
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.snippet_tree_widget.setColumnWidth(1, 20)
        self.snippet_tree_widget.setIndentation(12)
        self.control_panel = QWidget()
        self.editor_group = QGroupBox("Редактор")
        self.category_label = QLabel("Категория:")
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.abbreviation_label = QLabel("Аббревиатура (например, .ab):")
        self.abbreviation_input = QLineEdit()
        self.text_label = QLabel("Текст для вставки:")
        self.text_input = QTextEdit()

        # Группа фильтра окна для сниппета (сворачиваемая кнопкой-заголовком)
        self.window_filter_group = QGroupBox()
        self.window_filter_group.setObjectName("window_filter_group")
        self.window_filter_toggle_button = QPushButton(
            "▾ Фильтр по окну (опционально)"
        )
        self.window_filter_toggle_button.setObjectName("filter_header_btn")
        self.window_filter_toggle_button.setToolTip(
            "Свернуть или развернуть настройки фильтра по окну"
        )
        self._window_filter_collapsed = False
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
        self._set_action_icon(
            self.capture_window_button,
            "capture",
            "Заполнит поля данными активного окна",
        )
        self._window_filter_content_widgets = [
            self.window_title_label,
            self.window_title_input,
            self.window_class_label,
            self.window_class_input,
            self.match_mode_label,
            self.match_mode_combo,
            self.capture_window_button,
        ]

        self.mgmt_group = QGroupBox("Управление списком")
        self.new_category_button = QPushButton("Новая категория")
        self.new_snippet_button = QPushButton("Новый сниппет")
        self.rename_button = QPushButton("Переименовать")
        self.delete_button = QPushButton("Удалить")
        self.delete_button.setObjectName("warning_btn")
        self.save_button = QPushButton("Сохранить")
        self.save_button.setObjectName("start_btn")
        self._set_action_icon(
            self.new_category_button,
            "folder",
            "Создать новую категорию",
        )
        self._set_action_icon(
            self.new_snippet_button,
            "document",
            "Создать новый сниппет",
        )
        self._set_action_icon(
            self.rename_button,
            "edit",
            "Переименовать выбранный элемент",
        )
        self._set_action_icon(
            self.delete_button,
            "trash",
            "Удалить выбранный элемент",
        )
        self._set_action_icon(
            self.save_button,
            "save",
            "Сохранить текущий сниппет",
        )
        # Правая панель должна сжиматься при уменьшении окна, а не сдвигать
        # ручку splitter. Ширина элементов остаётся адаптивной, а ручка
        # по-прежнему свободно перетаскивается пользователем.
        for widget in (
            self.control_panel,
            self.editor_group,
            self.category_label,
            self.category_combo,
            self.abbreviation_label,
            self.abbreviation_input,
            self.text_label,
            self.text_input,
            self.window_filter_group,
            self.window_filter_toggle_button,
            self.window_title_label,
            self.window_title_input,
            self.window_class_label,
            self.window_class_input,
            self.match_mode_label,
            self.match_mode_combo,
            self.capture_window_button,
            self.mgmt_group,
            self.new_category_button,
            self.new_snippet_button,
            self.rename_button,
            self.delete_button,
            self.save_button,
        ):
            size_policy = widget.sizePolicy()
            size_policy.setHorizontalPolicy(QSizePolicy.Policy.Ignored)
            widget.setSizePolicy(size_policy)

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

        # Layout для группы фильтра окна (сворачиваемая кнопкой-заголовком)
        window_filter_layout = QVBoxLayout(self.window_filter_group)
        window_filter_layout.setContentsMargins(0, 0, 0, 0)
        window_filter_layout.addWidget(self.window_filter_toggle_button)
        window_filter_layout.addWidget(self.window_title_label)
        window_filter_layout.addWidget(self.window_title_input)
        window_filter_layout.addWidget(self.window_class_label)
        window_filter_layout.addWidget(self.window_class_input)
        window_filter_layout.addWidget(self.match_mode_label)
        window_filter_layout.addWidget(self.match_mode_combo)
        window_filter_layout.addWidget(self.capture_window_button)

        mgmt_layout = QGridLayout(self.mgmt_group)
        for column in range(6):
            mgmt_layout.setColumnStretch(column, 1)
        mgmt_layout.addWidget(self.new_category_button, 0, 0, 1, 3)
        mgmt_layout.addWidget(self.new_snippet_button, 0, 3, 1, 3)
        mgmt_layout.addWidget(self.rename_button, 1, 0, 1, 2)
        mgmt_layout.addWidget(self.delete_button, 1, 2, 1, 2)
        mgmt_layout.addWidget(self.save_button, 1, 4, 1, 2)
        control_layout.addWidget(self.editor_group)
        control_layout.addWidget(self.window_filter_group)
        control_layout.addWidget(self.mgmt_group)
        control_layout.setStretchFactor(self.editor_group, 1)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.snippet_tree_widget)
        self.splitter.addWidget(self.control_panel)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        main_tab_layout = QHBoxLayout(self.main_tab)
        main_tab_layout.setContentsMargins(0, 0, 0, 0)
        main_tab_layout.setSpacing(0)
        main_tab_layout.addWidget(self.splitter)

    def _toggle_window_filter_collapsed(self):
        collapsed = not self._window_filter_collapsed
        self._set_window_filter_collapsed(collapsed)
        self._save_specific_setting("window_filter_collapsed", collapsed)

    def _set_window_filter_collapsed(self, collapsed):
        self._window_filter_collapsed = bool(collapsed)
        for widget in self._window_filter_content_widgets:
            widget.setVisible(not collapsed)
        arrow = "▾" if not collapsed else "▸"
        self.window_filter_toggle_button.setText(
            f"{arrow} Фильтр по окну (опционально)"
        )

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

        scale_group = QGroupBox("Масштаб интерфейса")
        scale_layout = QVBoxLayout(scale_group)
        scale_row_layout = QHBoxLayout()
        self.ui_scale_label = QLabel("Масштаб:")
        self.ui_scale_combo = QComboBox()
        for delta_percent in range(-50, 51, 10):
            self.ui_scale_combo.addItem(f"{100 + delta_percent}%", delta_percent)
        self.ui_scale_info_label = QLabel("Авто: 100% | Поправка: 100% | Итог: 100%")
        scale_row_layout.addWidget(self.ui_scale_label)
        scale_row_layout.addWidget(self.ui_scale_combo, 1)
        scale_layout.addLayout(scale_row_layout)
        scale_layout.addWidget(self.ui_scale_info_label)
        layout.addWidget(scale_group)

        exchange_group = QGroupBox("Импорт и экспорт данных")
        exchange_layout = QVBoxLayout(exchange_group)
        exchange_note = QLabel(
            "Экспорт и импорт выполняются через JSON-файлы. "
            "Можно работать отдельно со сниппетами и настройками или использовать общий backup-файл. "
            "Импорт заменяет текущие данные соответствующего типа."
        )
        exchange_note.setWordWrap(True)
        exchange_layout.addWidget(exchange_note)

        snippets_buttons_layout = QHBoxLayout()
        self.export_snippets_button = QPushButton("Экспорт сниппетов")
        self.import_snippets_button = QPushButton("Импорт сниппетов")
        self._set_action_icon(
            self.export_snippets_button,
            "download",
            "Экспортировать сниппеты в JSON-файл",
        )
        self._set_action_icon(
            self.import_snippets_button,
            "upload",
            "Импортировать сниппеты из JSON-файла",
        )
        snippets_buttons_layout.addWidget(self.export_snippets_button)
        snippets_buttons_layout.addWidget(self.import_snippets_button)
        exchange_layout.addLayout(snippets_buttons_layout)

        settings_buttons_layout = QHBoxLayout()
        self.export_settings_button = QPushButton("Экспорт настроек")
        self.import_settings_button = QPushButton("Импорт настроек")
        self._set_action_icon(
            self.export_settings_button,
            "download",
            "Экспортировать настройки в JSON-файл",
        )
        self._set_action_icon(
            self.import_settings_button,
            "upload",
            "Импортировать настройки из JSON-файла",
        )
        settings_buttons_layout.addWidget(self.export_settings_button)
        settings_buttons_layout.addWidget(self.import_settings_button)
        exchange_layout.addLayout(settings_buttons_layout)

        backup_buttons_layout = QHBoxLayout()
        self.export_all_data_button = QPushButton("Экспорт всего")
        self.import_all_data_button = QPushButton("Импорт всего")
        self._set_action_icon(
            self.export_all_data_button,
            "archive",
            "Экспортировать сниппеты и настройки в backup JSON-файл",
        )
        self._set_action_icon(
            self.import_all_data_button,
            "upload",
            "Импортировать сниппеты и настройки из backup JSON-файла",
        )
        backup_buttons_layout.addWidget(self.export_all_data_button)
        backup_buttons_layout.addWidget(self.import_all_data_button)
        exchange_layout.addLayout(backup_buttons_layout)

        layout.addWidget(exchange_group)

        layout.addStretch()
        return tab

    def _apply_styles(self, scale_factor=None):
        if scale_factor is None:
            if hasattr(self, "get_ui_scale_factor"):
                scale_factor = self.get_ui_scale_factor()
            else:
                scale_factor = 1.0
        style_sheet = build_app_stylesheet(scale_factor)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(style_sheet)
        else:
            self.setStyleSheet(style_sheet)
        if hasattr(self, "admin_status_label"):
            self._apply_admin_status_style()

    def _setup_status_bar(self, is_admin):
        self.admin_status_label = QLabel()
        self.admin_status_label.setObjectName("admin_status_label")
        self._admin_status_is_admin = bool(is_admin)
        if is_admin:
            self.admin_status_label.setText("Права администратора")
        else:
            self.admin_status_label.setText("Обычные права (могут быть проблемы)")
        self._apply_admin_status_style()
        self.tabs.setCornerWidget(self.admin_status_label, Qt.Corner.TopRightCorner)

    def _apply_admin_status_style(self):
        if not hasattr(self, "admin_status_label"):
            return
        scale_factor = (
            self.get_ui_scale_factor() if hasattr(self, "get_ui_scale_factor") else 1.0
        )
        padding = scale_px(10, scale_factor, 1)
        color = ONEDARK_GREEN if getattr(self, "_admin_status_is_admin", False) else ONEDARK_RED
        self.admin_status_label.setStyleSheet(f"color: {color}; padding: 0 {padding}px;")

    def _connect_signals(self):
        self.snippet_tree_widget.itemSelectionCommitted.connect(
            self._display_item_details
        )
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
        self.window_filter_toggle_button.clicked.connect(
            self._toggle_window_filter_collapsed
        )
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.autostart_check.stateChanged.connect(self.on_autostart_changed)
        self.start_minimized_check.stateChanged.connect(self.on_start_minimized_changed)
        self.ui_scale_combo.currentIndexChanged.connect(self.on_ui_scale_delta_changed)
        self.export_snippets_button.clicked.connect(self.export_snippets_to_json)
        self.import_snippets_button.clicked.connect(self.import_snippets_from_json)
        self.export_settings_button.clicked.connect(self.export_settings_to_json)
        self.import_settings_button.clicked.connect(self.import_settings_from_json)
        self.export_all_data_button.clicked.connect(self.export_all_data_to_json)
        self.import_all_data_button.clicked.connect(self.import_all_data_from_json)

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
