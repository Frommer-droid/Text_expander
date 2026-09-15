import json
import os
from functools import partial

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QCheckBox, QMessageBox, QStyle, QTreeWidgetItem

from app.ui.constants import (
    CATEGORY_ITEM_KIND,
    ITEM_KIND_ROLE,
    ITEM_PATH_ROLE,
    SNIPPET_ITEM_KIND,
)


class SnippetDataMixin:
    def _save_tree_expanded_state(self):
        """Сохраняет состояние развернутых категорий в список."""
        expanded_categories = []

        def _collect_expanded(item):
            if not self._is_category_tree_item(item):
                return
            path = item.data(0, ITEM_PATH_ROLE)
            if path and item.isExpanded():
                expanded_categories.append(list(path))
            for idx in range(item.childCount()):
                _collect_expanded(item.child(idx))

        for i in range(self.snippet_tree_widget.topLevelItemCount()):
            _collect_expanded(self.snippet_tree_widget.topLevelItem(i))
        return expanded_categories

    def _restore_tree_expanded_state(self, expanded_categories):
        """Восстанавливает состояние развернутых категорий из списка."""
        normalized = set()
        for entry in expanded_categories or []:
            if isinstance(entry, str) and entry:
                normalized.add((entry,))
            elif isinstance(entry, (list, tuple)):
                tuple_entry = tuple(str(part) for part in entry if part)
                if tuple_entry:
                    normalized.add(tuple_entry)

        def _apply_state(item):
            if not self._is_category_tree_item(item):
                return
            path = tuple(item.data(0, ITEM_PATH_ROLE) or [])
            item.setExpanded(bool(normalized and path in normalized))
            for idx in range(item.childCount()):
                _apply_state(item.child(idx))

        for i in range(self.snippet_tree_widget.topLevelItemCount()):
            _apply_state(self.snippet_tree_widget.topLevelItem(i))

    def _on_item_expanded(self, item):
        """Обработчик события разворачивания категории."""
        if not item.parent():  # Только для категорий верхнего уровня
            self._save_expanded_state_to_settings()

    def _on_item_collapsed(self, item):
        """Обработчик события сворачивания категории."""
        if not item.parent():  # Только для категорий верхнего уровня
            self._save_expanded_state_to_settings()

    def _save_expanded_state_to_settings(self):
        """Сохраняет текущее состояние развернутых категорий в настройки."""
        expanded = self._save_tree_expanded_state()
        try:
            settings = {}
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            settings["expanded_categories"] = expanded
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except (IOError, json.JSONDecodeError):
            pass

    def _format_category_path(self, path):
        return self.CATEGORY_PATH_SEPARATOR.join(path) if path else ""

    def _parse_category_path(self, text):
        if not text:
            return ()
        raw_parts = text.split("/")
        parts = tuple(part.strip() for part in raw_parts if part.strip())
        return parts

    def _set_item_metadata(self, item, kind, path):
        item.setData(0, ITEM_KIND_ROLE, kind)
        item.setData(0, ITEM_PATH_ROLE, tuple(path))

    def _item_path(self, item):
        data = item.data(0, ITEM_PATH_ROLE) if item else None
        if isinstance(data, (tuple, list)):
            return tuple(data)
        if data:
            return (str(data),)
        return ()

    def _is_category_tree_item(self, item):
        return bool(item) and item.data(0, ITEM_KIND_ROLE) == CATEGORY_ITEM_KIND

    def _iter_category_paths(self, categories=None, prefix=()):
        categories = categories if categories is not None else self.snippets_data
        for name in sorted(categories.keys()):
            payload = categories[name]
            path = prefix + (name,)
            yield path
            subcats = payload.get("categories", {})
            if subcats:
                yield from self._iter_category_paths(subcats, path)

    def _get_category_payload(self, path, *, create=False):
        if not path:
            return None
        current = None
        container = self.snippets_data
        for name in path:
            payload = container.get(name)
            if payload is None:
                if not create:
                    return None
                payload = self._new_category_payload()
                container[name] = payload
            current = payload
            container = payload.setdefault("categories", {})
        return current

    def _get_category_children(self, path, *, create=False):
        if not path:
            return self.snippets_data
        payload = self._get_category_payload(path, create=create)
        if payload is None:
            return None
        return (
            payload.setdefault("categories", {}) if create else payload.get("categories", {})
        )

    def _category_is_empty(self, payload):
        return not payload.get("snippets") and not payload.get("categories")

    def _sync_parent_payload_flags(self, path):
        current_path = tuple(path or ())
        while current_path:
            payload = self._get_category_payload(current_path)
            if payload:
                payload["enabled"] = self._are_all_snippets_enabled(payload)
            current_path = current_path[:-1]

    def _find_category_item(self, path):
        target_path = tuple(path or ())
        if not target_path:
            return None

        def _search(item):
            if not item:
                return None
            if self._is_category_tree_item(item):
                item_path = self._item_path(item)
                if item_path == target_path:
                    return item
            for idx in range(item.childCount()):
                found = _search(item.child(idx))
                if found:
                    return found
            return None

        for i in range(self.snippet_tree_widget.topLevelItemCount()):
            found_item = _search(self.snippet_tree_widget.topLevelItem(i))
            if found_item:
                return found_item
        return None

    def _new_category_payload(self, enabled=True):
        return {"enabled": bool(enabled), "snippets": {}, "categories": {}}

    def _are_all_snippets_enabled(self, payload):
        if not isinstance(payload, dict):
            return True
        snippets = payload.get("snippets", {})
        subcategories = payload.get("categories", {})
        if not snippets and not subcategories:
            return bool(payload.get("enabled", True))
        for entry in snippets.values():
            if not entry.get("enabled", True):
                return False
        for child_payload in subcategories.values():
            if not self._are_all_snippets_enabled(child_payload):
                return False
        return True

    def _any_snippet_enabled(self, payload):
        snippets = payload.get("snippets", {})
        return any(entry.get("enabled", True) for entry in snippets.values())

    def _category_checkbox_state(self, payload):
        if not isinstance(payload, dict):
            return Qt.CheckState.Unchecked
        child_states = []
        for entry in payload.get("snippets", {}).values():
            child_states.append(
                Qt.CheckState.Checked
                if entry.get("enabled", True)
                else Qt.CheckState.Unchecked
            )
        for sub_payload in payload.get("categories", {}).values():
            child_states.append(self._category_checkbox_state(sub_payload))

        if not child_states:
            return (
                Qt.CheckState.Checked
                if payload.get("enabled", True)
                else Qt.CheckState.Unchecked
            )
        if all(state == Qt.CheckState.Checked for state in child_states):
            return Qt.CheckState.Checked
        if all(state == Qt.CheckState.Unchecked for state in child_states):
            return Qt.CheckState.Unchecked
        return Qt.CheckState.PartiallyChecked

    def _set_item_checkbox_state(self, item, state):
        checkbox = self.snippet_tree_widget.itemWidget(item, 1)
        if not checkbox:
            return
        checkbox.blockSignals(True)
        checkbox.setCheckState(state)
        checkbox.blockSignals(False)

    def _update_category_checkbox_state(self, category_item):
        payload = self._get_category_payload(self._item_path(category_item))
        if not payload:
            return
        state = self._category_checkbox_state(payload)
        self._set_item_checkbox_state(category_item, state)

    def _update_parent_checkbox_state(self, starting_item):
        parent = starting_item.parent()
        while parent:
            if self._is_category_tree_item(parent):
                self._update_category_checkbox_state(parent)
            parent = parent.parent()

    def _apply_category_state_to_children(self, category_item, enabled):
        state = Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked
        for i in range(category_item.childCount()):
            child_item = category_item.child(i)
            if self._is_category_tree_item(child_item):
                child_path = self._item_path(child_item)
                child_payload = self._get_category_payload(child_path)
                if child_payload:
                    child_payload["enabled"] = enabled
                    for entry in child_payload.get("snippets", {}).values():
                        entry["enabled"] = enabled
                self._set_item_checkbox_state(child_item, state)
                self._apply_category_state_to_children(child_item, enabled)
            else:
                self._set_item_checkbox_state(child_item, state)
                parent_path = self._item_path(child_item)
                payload = self._get_category_payload(parent_path)
                if payload:
                    snippet_entry = payload.get("snippets", {}).get(child_item.text(0))
                    if snippet_entry:
                        snippet_entry["enabled"] = enabled

    def _normalize_category_payload(self, payload):
        needs_resave = False
        if not isinstance(payload, dict):
            return self._new_category_payload(), True

        normalized_payload = self._new_category_payload(
            enabled=payload.get("enabled", True)
        )

        # Сохраняем window_filter категории, если он есть
        if "window_filter" in payload and payload.get("window_filter"):
            normalized_payload["window_filter"] = payload["window_filter"]

        snippets_block = {}
        if "snippets" in payload and isinstance(payload.get("snippets"), dict):
            snippets_block = payload.get("snippets") or {}
        elif isinstance(payload, dict):
            snippets_block = {
                key: value
                for key, value in payload.items()
                if key not in {"enabled", "categories", "window_filter"}
            }
            if snippets_block:
                needs_resave = True

        normalized_snippets = {}
        for abbr, snippet_payload in snippets_block.items():
            snippet_enabled = True
            snippet_text = ""
            snippet_window_filter = None
            if isinstance(snippet_payload, dict):
                snippet_text = str(snippet_payload.get("text", ""))
                snippet_enabled = bool(snippet_payload.get("enabled", True))
                # Сохраняем window_filter сниппета
                snippet_window_filter = snippet_payload.get("window_filter")
                if "text" not in snippet_payload or "enabled" not in snippet_payload:
                    needs_resave = True
            else:
                snippet_text = str(snippet_payload) if snippet_payload else ""
                snippet_enabled = True
                needs_resave = True

            snippet_data = {
                "text": snippet_text,
                "enabled": snippet_enabled,
            }
            # Добавляем window_filter только если он есть
            if snippet_window_filter:
                snippet_data["window_filter"] = snippet_window_filter

            normalized_snippets[abbr] = snippet_data

        raw_subcategories = payload.get("categories", {})
        normalized_subcategories = {}
        if isinstance(raw_subcategories, dict):
            for sub_name, sub_payload in raw_subcategories.items():
                normalized_child, child_resave = self._normalize_category_payload(
                    sub_payload
                )
                normalized_subcategories[sub_name] = normalized_child
                needs_resave = needs_resave or child_resave
        elif raw_subcategories:
            needs_resave = True

        normalized_payload["snippets"] = normalized_snippets
        normalized_payload["categories"] = normalized_subcategories
        return normalized_payload, needs_resave

    def _normalize_snippet_store(self, data):
        normalized = {}
        needs_resave = False
        if not isinstance(data, dict):
            return normalized, True

        if data and all(isinstance(v, str) for v in data.values()):
            normalized["Без категории"] = {
                "enabled": True,
                "snippets": {
                    abbr: {"text": str(text), "enabled": True}
                    for abbr, text in data.items()
                },
                "categories": {},
            }
            return normalized, True

        for category_name, payload in data.items():
            normalized_payload, payload_resave = self._normalize_category_payload(
                payload
            )
            normalized[category_name] = normalized_payload
            needs_resave = needs_resave or payload_resave

        return normalized, needs_resave

    def _attach_checkbox_widget(self, item, *, is_category, state):
        checkbox = QCheckBox()
        checkbox.setTristate(is_category)
        checkbox.blockSignals(True)
        if isinstance(state, Qt.CheckState):
            check_state = state
        else:
            check_state = Qt.CheckState.Checked if state else Qt.CheckState.Unchecked
        checkbox.setCheckState(check_state)
        checkbox.blockSignals(False)
        tooltip = (
            "Включить/выключить все сниппеты категории"
            if is_category
            else "Включить/выключить этот сниппет"
        )
        checkbox.setToolTip(tooltip)
        checkbox.stateChanged.connect(
            partial(self._on_tree_checkbox_toggled, item, is_category)
        )
        self.snippet_tree_widget.setItemWidget(item, 1, checkbox)

    def _on_tree_checkbox_toggled(self, item, is_category, state):
        check_state = Qt.CheckState(state)
        if is_category:
            if check_state == Qt.CheckState.PartiallyChecked:
                return
            self._set_category_enabled(item, check_state == Qt.CheckState.Checked)
        else:
            parent_item = item.parent()
            if not parent_item:
                return
            category_path = self._item_path(parent_item)
            if not category_path:
                return
            abbr = item.text(0)
            self._set_snippet_enabled(
                category_path,
                abbr,
                check_state == Qt.CheckState.Checked,
                parent_item=parent_item,
            )

    def _set_category_enabled(self, category_item, enabled):
        category_path = self._item_path(category_item)
        payload = self._get_category_payload(category_path)
        if not payload:
            return
        enabled = bool(enabled)
        changed = payload.get("enabled", True) != enabled
        payload["enabled"] = enabled
        child_changed = False
        for entry in payload.get("snippets", {}).values():
            if entry.get("enabled", True) != enabled:
                entry["enabled"] = enabled
                child_changed = True
        payload["enabled"] = self._are_all_snippets_enabled(payload)
        self._apply_category_state_to_children(category_item, enabled)
        self._update_category_checkbox_state(category_item)
        self._update_parent_checkbox_state(category_item)
        self._sync_parent_payload_flags(category_path[:-1])
        if changed or child_changed:
            self.reload_listener_snippets()

    def _set_snippet_enabled(self, category_path, abbr, enabled, parent_item=None):
        payload = self._get_category_payload(category_path)
        if not payload:
            return
        snippet_entry = payload.get("snippets", {}).get(abbr)
        if not snippet_entry:
            return
        enabled = bool(enabled)
        if snippet_entry.get("enabled", True) == enabled:
            return
        snippet_entry["enabled"] = enabled
        payload["enabled"] = self._are_all_snippets_enabled(payload)
        if parent_item:
            self._update_category_checkbox_state(parent_item)
            self._update_parent_checkbox_state(parent_item)
        self._sync_parent_payload_flags(category_path[:-1])
        self.reload_listener_snippets()

    def _load_snippets(self):
        try:
            if not os.path.exists(self.snippets_file):
                self.snippets_data = {
                    "Общее": {
                        "enabled": True,
                        "snippets": {
                            ".example": {
                                "text": "Это пример сниппета.",
                                "enabled": True,
                            }
                        },
                        "categories": {},
                    }
                }
                self._save_snippets_to_file()
            else:
                with open(self.snippets_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                normalized, needs_resave = self._normalize_snippet_store(raw_data)
                self.snippets_data = normalized
                if needs_resave:
                    self._save_snippets_to_file()

            if not self.snippets_data:
                self.snippets_data["Общее"] = {
                    "enabled": True,
                    "snippets": {},
                    "categories": {},
                }

            expanded_categories = self._save_tree_expanded_state()

            self.snippet_tree_widget.clear()
            self.category_combo.clear()
            self.category_combo_paths = {}

            folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)

            def _build_category_items(parent_widget, path, payload):
                category_item = QTreeWidgetItem(parent_widget)
                category_item.setText(0, path[-1])
                category_item.setIcon(0, folder_icon)
                self._set_item_metadata(category_item, CATEGORY_ITEM_KIND, path)
                category_state = self._category_checkbox_state(payload)
                self._attach_checkbox_widget(
                    category_item, is_category=True, state=category_state
                )

                sorted_snippets = sorted(payload.get("snippets", {}).keys())
                for abbr in sorted_snippets:
                    snippet_entry = payload["snippets"].get(abbr, {})
                    snippet_text = snippet_entry.get("text", "")
                    snippet_item = QTreeWidgetItem(category_item)
                    snippet_item.setText(0, abbr)
                    snippet_item.setData(0, Qt.ItemDataRole.UserRole, snippet_text)
                    self._set_item_metadata(snippet_item, SNIPPET_ITEM_KIND, path)
                    snippet_state = (
                        Qt.CheckState.Checked
                        if snippet_entry.get("enabled", True)
                        else Qt.CheckState.Unchecked
                    )
                    self._attach_checkbox_widget(
                        snippet_item, is_category=False, state=snippet_state
                    )

                for sub_name, sub_payload in sorted(payload.get("categories", {}).items()):
                    _build_category_items(
                        category_item,
                        path + (sub_name,),
                        sub_payload or self._new_category_payload(),
                    )

            for category_name in sorted(self.snippets_data.keys()):
                category_payload = self.snippets_data.get(
                    category_name, self._new_category_payload()
                )
                _build_category_items(
                    self.snippet_tree_widget, (category_name,), category_payload
                )

            for path in self._iter_category_paths():
                display = self._format_category_path(path)
                self.category_combo.addItem(display)
                index = self.category_combo.count() - 1
                self.category_combo.setItemData(index, path, Qt.ItemDataRole.UserRole)
                self.category_combo_paths[display] = path

            self._restore_tree_expanded_state(expanded_categories)

        except (json.JSONDecodeError, IOError) as e:
            QMessageBox.warning(
                self, "Ошибка", f"Не удалось загрузить файл сниппетов: {e}"
            )
            self.snippets_data = {}

    def _schedule_tree_refresh(
        self,
        *,
        focus_category_path=None,
        focus_snippet=None,
        expand_category_path=None,
    ):
        focus_path = tuple(focus_category_path or ())
        expand_path = tuple(expand_category_path or ())
        QTimer.singleShot(
            0,
            partial(
                self._refresh_tree_after_model_change,
                focus_path,
                focus_snippet,
                expand_path,
            ),
        )

    def _refresh_tree_after_model_change(
        self, focus_category_path, focus_snippet, expand_category_path
    ):
        self._load_snippets()
        if expand_category_path:
            self._expand_category_branch(expand_category_path)
        if focus_snippet and focus_category_path:
            if not self._select_snippet_in_tree(focus_category_path, focus_snippet):
                self._select_category_in_tree(focus_category_path)
        elif focus_category_path:
            self._select_category_in_tree(focus_category_path)

    def _save_snippets_to_file(self):
        try:
            with open(self.snippets_file, "w", encoding="utf-8") as f:
                json.dump(self.snippets_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось сохранить файл сниппетов: {e}"
            )
