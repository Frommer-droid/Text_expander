from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QTreeWidget

from app.ui.constants import CATEGORY_ITEM_KIND, ITEM_KIND_ROLE, ITEM_PATH_ROLE, SNIPPET_ITEM_KIND


class SnippetTreeWidget(QTreeWidget):
    """
    Дерево со сниппетами, которое умеет перетаскивать дочерние элементы между категориями.
    """

    snippetMoved = Signal(object, str, object)  # source_path, abbreviation, target_path
    categoryMoved = Signal(object, object)  # source_path, target_category_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._dragged_item = None

    def startDrag(self, supportedActions):
        current_item = self.currentItem()
        if not current_item:
            self._dragged_item = None
            return

        kind = current_item.data(0, ITEM_KIND_ROLE)
        if kind not in (SNIPPET_ITEM_KIND, CATEGORY_ITEM_KIND):
            self._dragged_item = None
            return

        self._dragged_item = current_item
        super().startDrag(supportedActions)

    def dragMoveEvent(self, event):
        if not self._dragged_item:
            event.ignore()
            return

        item_kind = self._dragged_item.data(0, ITEM_KIND_ROLE)
        if item_kind == SNIPPET_ITEM_KIND:
            if self._target_category_item(event):
                event.acceptProposedAction()
                super().dragMoveEvent(event)
            else:
                event.ignore()
            return

        if item_kind == CATEGORY_ITEM_KIND:
            target_path = self._target_category_path(event)
            source_path = tuple(self._dragged_item.data(0, ITEM_PATH_ROLE) or ())
            if (
                target_path
                and source_path
                and target_path != source_path[:-1]
                and not self._path_is_prefix(source_path, target_path)
            ):
                event.acceptProposedAction()
                super().dragMoveEvent(event)
            else:
                event.ignore()
            return

        event.ignore()

    def dropEvent(self, event):
        dragged_item = self._dragged_item
        self._dragged_item = None
        if not dragged_item:
            event.ignore()
            return

        target_path = self._target_category_path(event)
        source_path = tuple(dragged_item.data(0, ITEM_PATH_ROLE) or ())
        item_kind = dragged_item.data(0, ITEM_KIND_ROLE)

        if item_kind == SNIPPET_ITEM_KIND:
            if target_path and source_path and source_path != target_path:
                event.acceptProposedAction()
                abbreviation = dragged_item.text(0)
                self.snippetMoved.emit(source_path, abbreviation, target_path)
            else:
                event.ignore()
            return

        if item_kind == CATEGORY_ITEM_KIND:
            if (
                target_path
                and source_path
                and target_path != source_path[:-1]
                and not self._path_is_prefix(source_path, target_path)
            ):
                event.acceptProposedAction()
                self.categoryMoved.emit(source_path, target_path)
            else:
                event.ignore()
            return

        event.ignore()

    def _target_category_item(self, event):
        item = self._item_from_event(event)
        while item and item.data(0, ITEM_KIND_ROLE) != CATEGORY_ITEM_KIND:
            item = item.parent()
        return item

    def _target_category_path(self, event):
        category_item = self._target_category_item(event)
        if not category_item:
            return None
        path_data = category_item.data(0, ITEM_PATH_ROLE)
        if isinstance(path_data, (list, tuple)):
            return tuple(path_data)
        if path_data:
            return (path_data,)
        return None

    def _item_from_event(self, event):
        try:
            pos = event.position().toPoint()
        except AttributeError:
            pos = event.pos()
        return self.itemAt(pos)

    @staticmethod
    def _path_is_prefix(prefix, candidate):
        if not prefix:
            return False
        prefix = tuple(prefix or ())
        candidate = tuple(candidate or ())
        if len(candidate) < len(prefix):
            return False
        return candidate[: len(prefix)] == prefix
