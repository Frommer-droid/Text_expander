from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QCheckBox, QHeaderView, QMainWindow, QTreeWidgetItem

from app.ui.snippet_tree_widget import SnippetTreeWidget
from app.ui.theme import THEME_COLORS, build_global_stylesheet
from app.ui.ui_setup_mixin import UiSetupMixin
from app.ui.ui_scale_mixin import UiScaleMixin


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication(sys.argv[:1])


def test_application_icon_is_multi_size_and_uses_the_full_canvas(app):
    icon_path = PROJECT_ROOT / "logo.ico"
    icon = QIcon(str(icon_path))
    sizes = {size.width() for size in icon.availableSizes()}
    image = icon.pixmap(QSize(256, 256)).toImage()

    assert {16, 32, 48, 64, 128, 256}.issubset(sizes)
    assert image.width() == 256
    assert image.height() == 256
    assert all(
        image.pixelColor(x, y).alpha() == 255
        for x, y in ((0, 0), (255, 0), (0, 255), (255, 255))
    )


def test_primary_actions_and_remaining_tabs_have_icons(app):
    class TestWindow(QMainWindow, UiSetupMixin, UiScaleMixin):
        def __init__(self):
            super().__init__()
            self.settings_file = "stub_unused.json"
            self._init_ui_scale_runtime()
            self._create_widgets()
            self._create_layout()

    window = TestWindow()
    try:
        window._apply_styles(1.0)
        window._setup_status_bar(True)
        buttons = (
            window.capture_window_button,
            window.new_category_button,
            window.new_snippet_button,
            window.rename_button,
            window.delete_button,
            window.save_button,
            window.export_snippets_button,
            window.import_snippets_button,
            window.export_settings_button,
            window.import_settings_button,
            window.export_all_data_button,
            window.import_all_data_button,
        )
        assert all(not button.icon().isNull() for button in buttons)
        assert all(
            not window.tabs.tabIcon(index).isNull()
            for index in range(window.tabs.count())
        )
        assert window.tabs.count() == 2
        assert [window.tabs.tabText(index) for index in range(window.tabs.count())] == [
            "Основная функция",
            "Система",
        ]

        management_layout = window.mgmt_group.layout()

        def grid_position(button):
            return management_layout.getItemPosition(management_layout.indexOf(button))

        assert grid_position(window.new_category_button) == (0, 0, 1, 3)
        assert grid_position(window.new_snippet_button) == (0, 3, 1, 3)
        assert grid_position(window.rename_button) == (1, 0, 1, 2)
        assert grid_position(window.delete_button) == (1, 2, 1, 2)
        assert grid_position(window.save_button) == (1, 4, 1, 2)
        assert window.save_button.text() == "Сохранить"
        assert window.save_button.minimumSizeHint().height() == (
            window.delete_button.minimumSizeHint().height()
        )
        assert window.tabs.cornerWidget(Qt.Corner.TopRightCorner) is (
            window.admin_status_label
        )
        assert window.main_tab.layout().contentsMargins().left() == 0
        assert window.snippet_tree_widget.columnWidth(1) == 20
        assert window.snippet_tree_widget.allColumnsShowFocus()
        assert (
            window.snippet_tree_widget.selectionBehavior()
            == window.snippet_tree_widget.SelectionBehavior.SelectRows
        )
        assert window.snippet_tree_widget.indentation() == 12

        image = window.save_button.icon().pixmap(QSize(24, 24)).toImage()
        opaque_pixels = [
            (x, y)
            for y in range(image.height())
            for x in range(image.width())
            if image.pixelColor(x, y).alpha() > 0
        ]
        top = min(y for _, y in opaque_pixels)
        bottom = max(y for _, y in opaque_pixels)
        vertical_center = (top + bottom + 1) / 2
        # «Сохранить» — эталон для кнопок с текстом: пиктограмма должна быть
        # оптически немного ниже центра, на одной линии с буквами.
        assert 0.5 <= vertical_center - image.height() / 2 <= 2
    finally:
        window.close()


def test_tree_selection_has_a_continuous_background_behind_checkbox(app):
    tree = SnippetTreeWidget()
    tree.setColumnCount(2)
    header = tree.header()
    header.setStretchLastSection(False)
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
    tree.setColumnWidth(1, 20)
    tree.setStyleSheet(build_global_stylesheet(THEME_COLORS))

    item = QTreeWidgetItem(tree)
    item.setText(0, "Общее")
    checkbox = QCheckBox()
    tree.setItemWidget(item, 1, checkbox)

    try:
        tree.resize(320, 100)
        tree.show()
        tree.setCurrentItem(item)
        app.processEvents()

        image = tree.viewport().grab().toImage()
        item_y = tree.visualItemRect(item).center().y()
        text_column_color = image.pixelColor(10, item_y)
        checkbox_column_color = image.pixelColor(
            header.sectionPosition(1) + 1, item_y
        )

        assert tree.allColumnsShowFocus()
        assert text_column_color == checkbox_column_color
    finally:
        tree.close()
