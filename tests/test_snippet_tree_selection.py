from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTreeWidgetItem

from app.ui.snippet_tree_widget import SnippetTreeWidget


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication(sys.argv[:1])


def test_hover_does_not_commit_another_item_to_the_editor(app):
    tree = SnippetTreeWidget()
    tree.setColumnCount(1)
    first_item = QTreeWidgetItem(tree, ["Первый"])
    second_item = QTreeWidgetItem(tree, ["Второй"])
    committed_items = []
    tree.itemSelectionCommitted.connect(
        lambda current, previous: committed_items.append((current, previous))
    )

    try:
        tree.resize(260, 120)
        tree.show()
        app.processEvents()

        QTest.mouseClick(
            tree.viewport(),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            tree.visualItemRect(first_item).center(),
        )
        app.processEvents()
        assert committed_items == [(first_item, None)]

        QTest.mouseMove(tree.viewport(), tree.visualItemRect(second_item).center())
        app.processEvents()
        assert tree.currentItem() is first_item
        assert committed_items == [(first_item, None)]
    finally:
        tree.close()
