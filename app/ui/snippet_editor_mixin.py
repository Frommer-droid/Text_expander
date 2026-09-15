from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QInputDialog, QMessageBox

from app.services.windows_api import get_active_window_class, get_active_window_title
from app.ui.constants import ITEM_KIND_ROLE, SNIPPET_ITEM_KIND


class SnippetEditorMixin:
    def _display_item_details(self, item, previous):
        if not item:
            self._clear_fields_for_new_snippet()
            return

        is_snippet = item.data(0, ITEM_KIND_ROLE) == SNIPPET_ITEM_KIND
        self.abbreviation_input.setEnabled(True)
        self.text_input.setEnabled(True)

        if is_snippet:
            category_path = self._item_path(item)
            abbr = item.text(0)
            text = item.data(0, Qt.ItemDataRole.UserRole)

            self.category_combo.setCurrentText(self._format_category_path(category_path))
            self.abbreviation_input.setText(abbr)
            self.text_input.setText(text)
            self.original_abbr = abbr
            self.original_category_path = category_path

            # Загружаем window_filter сниппета
            category_payload = self._get_category_payload(category_path)
            snippet_data = None
            if category_payload:
                snippets = category_payload.get("snippets", {})
                snippet_data = snippets.get(abbr)

            if snippet_data and isinstance(snippet_data, dict):
                window_filter = snippet_data.get("window_filter", {})
                if window_filter:
                    self.window_title_input.setText(window_filter.get("title", ""))
                    self.window_class_input.setText(window_filter.get("class", ""))
                    match_mode = window_filter.get("match_mode", "contains")
                    if match_mode == "exact":
                        self.match_mode_combo.setCurrentIndex(1)
                    else:
                        self.match_mode_combo.setCurrentIndex(0)
                else:
                    self._clear_window_filter_fields()
            else:
                self._clear_window_filter_fields()
        else:
            self.category_combo.setCurrentText(
                self._format_category_path(self._item_path(item))
            )
            self.abbreviation_input.clear()
            self.text_input.clear()
            self._clear_window_filter_fields()
            self.original_abbr = None
            self.original_category_path = None

        self.statusBar().clearMessage()

    def _clear_window_filter_fields(self):
        """Очищает поля фильтра окна."""
        self.window_title_input.clear()
        self.window_class_input.clear()
        self.match_mode_combo.setCurrentIndex(0)

    def _capture_current_window(self):
        """Запускает обратный отсчёт для захвата окна - даёт время переключиться на нужное окно."""
        self.capture_window_button.setEnabled(False)
        self._capture_countdown = 3
        self._update_capture_countdown()

    def _update_capture_countdown(self):
        """Обновляет обратный отсчёт и захватывает окно по истечении времени."""
        if self._capture_countdown > 0:
            self.capture_window_button.setText(
                f"Захват через {self._capture_countdown}..."
            )
            self.statusBar().showMessage(
                "Переключитесь на нужное окно! "
                f"Захват через {self._capture_countdown} сек...",
                1500,
            )
            self._capture_countdown -= 1
            QTimer.singleShot(1000, self._update_capture_countdown)
        else:
            # Захватываем информацию об активном окне
            title = get_active_window_title()
            window_class = get_active_window_class()

            if title:
                self.window_title_input.setText(title)
            if window_class:
                self.window_class_input.setText(window_class)

            self.capture_window_button.setText("Захватить текущее окно")
            self.capture_window_button.setEnabled(True)
            self.statusBar().showMessage(
                f"Захвачено: '{title or 'Н/Д'}' (класс: {window_class or 'Н/Д'})",
                3000,
            )
            # Возвращаем фокус на приложение
            self.activateWindow()
            self.raise_()

    def _save_snippet(self):
        category_text = self.category_combo.currentText().strip()
        abbr = self.abbreviation_input.text().strip()
        text = self.text_input.toPlainText().strip()

        if not category_text:
            QMessageBox.warning(
                self,
                "Выберите категорию",
                "Выберите категорию перед сохранением сниппета.",
            )
            return

        if not abbr or not text:
            if not self.original_abbr and not abbr and not text:
                QMessageBox.information(
                    self,
                    "Нечего сохранять",
                    "Изменения категорий сохраняются автоматически. Выберите или "
                    "создайте сниппет и заполните оба поля перед сохранением.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Заполните обязательные поля",
                    "Укажите и аббревиатуру, и текст перед сохранением сниппета.",
                )
            return

        category_path = self.category_combo_paths.get(category_text)
        if not category_path:
            category_path = self._parse_category_path(category_text)

        if not category_path:
            QMessageBox.warning(
                self,
                "Неизвестная категория",
                "Не удалось разобрать путь категории; выберите существующую категорию.",
            )
            return

        snippet_enabled = True
        if self.original_abbr and self.original_category_path:
            original_payload = self._get_category_payload(self.original_category_path)
            original_snippets = (
                original_payload.get("snippets", {}) if original_payload else {}
            )
            original_entry = (
                original_snippets.get(self.original_abbr) if original_snippets else None
            )
            if original_entry:
                snippet_enabled = original_entry.get("enabled", True)
                del original_snippets[self.original_abbr]
                if original_payload:
                    if self._category_is_empty(original_payload):
                        parent_container = self._get_category_children(
                            self.original_category_path[:-1], create=False
                        )
                        if self.original_category_path and parent_container is not None:
                            parent_container.pop(
                                self.original_category_path[-1], None
                            )
                        self._sync_parent_payload_flags(
                            self.original_category_path[:-1]
                        )
                    else:
                        original_payload["enabled"] = self._are_all_snippets_enabled(
                            original_payload
                        )
                        self._sync_parent_payload_flags(self.original_category_path)

        category_payload = self._get_category_payload(category_path, create=True)

        # Формируем window_filter если указаны данные
        window_filter = None
        window_title = self.window_title_input.text().strip()
        window_class = self.window_class_input.text().strip()
        if window_title or window_class:
            match_mode = (
                "exact" if self.match_mode_combo.currentIndex() == 1 else "contains"
            )
            window_filter = {
                "title": window_title,
                "class": window_class,
                "match_mode": match_mode,
            }

        snippet_data = {
            "text": text,
            "enabled": snippet_enabled,
        }
        if window_filter:
            snippet_data["window_filter"] = window_filter

        print(f"[DEBUG] Сохранение сниппета '{abbr}' с данными: {snippet_data}")

        category_payload["snippets"][abbr] = snippet_data
        category_payload["enabled"] = self._are_all_snippets_enabled(category_payload)
        self._sync_parent_payload_flags(category_path)

        print(
            f"[DEBUG] Данные категории для '{abbr}': "
            f"{category_payload['snippets'].get(abbr)}"
        )

        self._save_snippets_to_file()
        self._load_snippets()

        reloaded_payload = self._get_category_payload(category_path)
        if reloaded_payload:
            print(
                f"[DEBUG] После перезагрузки - данные сниппета: "
                f"{reloaded_payload.get('snippets', {}).get(abbr)}"
            )

        # Автоматически применяем изменения
        self.reload_listener_snippets()

        self.statusBar().showMessage("Сниппет сохранен и применен!", 3000)
        self._select_snippet_in_tree(category_path, abbr)

    def _expand_category_branch(self, path):
        branch = ()
        for name in tuple(path or ()):
            branch += (name,)
            item = self._find_category_item(branch)
            if item:
                self.snippet_tree_widget.expandItem(item)
            else:
                break

    def _select_category_in_tree(self, category_path):
        category_path = tuple(category_path or ())
        if not category_path:
            return False
        self._expand_category_branch(category_path)
        category_item = self._find_category_item(category_path)
        if not category_item:
            return False
        self.snippet_tree_widget.setCurrentItem(category_item)
        self.category_combo.setCurrentText(self._format_category_path(category_path))
        return True

    def _select_snippet_in_tree(self, category_path, abbr):
        """Выбирает сниппет в дереве по категории и сокращению."""
        category_path = tuple(category_path or ())
        if not category_path:
            return False
        self._expand_category_branch(category_path)
        category_item = self._find_category_item(category_path)
        if not category_item:
            return False
        for j in range(category_item.childCount()):
            snip_item = category_item.child(j)
            if (
                snip_item.data(0, ITEM_KIND_ROLE) == SNIPPET_ITEM_KIND
                and snip_item.text(0) == abbr
            ):
                self.snippet_tree_widget.setCurrentItem(snip_item)
                self.category_combo.setCurrentText(
                    self._format_category_path(category_path)
                )
                return True
        return False

    def _clear_fields_for_new_snippet(self):
        current_item = self.snippet_tree_widget.currentItem()
        category_path_to_select = ()
        if current_item:
            if self._is_category_tree_item(current_item):
                category_path_to_select = self._item_path(current_item)
            else:
                category_path_to_select = self._item_path(current_item)

        self.snippet_tree_widget.setCurrentItem(None)
        self.abbreviation_input.clear()
        self.text_input.clear()
        self._clear_window_filter_fields()
        self.abbreviation_input.setEnabled(True)
        self.text_input.setEnabled(True)
        self.original_abbr = None
        self.original_category_path = None

        if category_path_to_select:
            self.category_combo.setCurrentText(
                self._format_category_path(category_path_to_select)
            )
        elif self.category_combo.count() > 0:
            self.category_combo.setCurrentIndex(0)

        self.abbreviation_input.setFocus()

    def _add_new_category(self):
        text, ok = QInputDialog.getText(
            self, "Новая категория", "Введите имя новой категории:"
        )
        if not ok:
            return

        new_name = text.strip()
        if not new_name:
            return

        current_item = self.snippet_tree_widget.currentItem()
        parent_path = ()

        if current_item:
            msg = QMessageBox(self)
            msg.setWindowTitle("Место создания")
            msg.setText(f"Где создать категорию '{new_name}'?")
            msg.setStyleSheet("QPushButton { min-width: 140px; padding: 5px; }")

            btn_sub = None
            if self._is_category_tree_item(current_item):
                btn_sub = msg.addButton(
                    "Подкатегория", QMessageBox.ButtonRole.ActionRole
                )

            btn_sibling = msg.addButton(
                "На этом уровне", QMessageBox.ButtonRole.ActionRole
            )
            btn_root = msg.addButton("В корне", QMessageBox.ButtonRole.ActionRole)
            btn_cancel = msg.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)

            msg.exec()

            clicked = msg.clickedButton()
            if clicked == btn_cancel:
                return
            elif clicked == btn_sub:
                parent_path = self._item_path(current_item)
            elif clicked == btn_sibling:
                path = self._item_path(current_item)
                if path:
                    parent_path = path[:-1]
                else:
                    parent_path = ()
            elif clicked == btn_root:
                parent_path = ()
            else:
                return

        container = self._get_category_children(parent_path, create=True)
        if container is None:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Не удалось найти родительскую категорию.",
            )
            return

        if new_name in container:
            QMessageBox.warning(
                self, "Дубликат", "Категория с таким именем уже существует."
            )
            return

        container[new_name] = self._new_category_payload()
        self._save_snippets_to_file()
        self._load_snippets()

    def _rename_item(self):
        item = self.snippet_tree_widget.currentItem()
        if not item:
            return

        old_name = item.text(0)
        is_category = self._is_category_tree_item(item)
        title = "Переименовать категорию" if is_category else "Переименовать сниппет"
        new_name, ok = QInputDialog.getText(
            self, title, "Введите новое имя:", text=old_name
        )
        new_name = new_name.strip() if new_name else new_name

        if not ok or not new_name or new_name == old_name:
            return

        if is_category:
            path = self._item_path(item)
            if not path:
                return
            parent_path = path[:-1]
            container = self._get_category_children(parent_path, create=False)
            if container is None:
                return
            if new_name in container:
                QMessageBox.warning(
                    self, "Дубликат", "Категория с таким именем уже существует."
                )
                return
            container[new_name] = container.pop(path[-1])
        else:
            category_path = self._item_path(item)
            payload = self._get_category_payload(category_path)
            if not payload:
                return
            snippets_bucket = payload.get("snippets", {})
            if new_name in snippets_bucket:
                QMessageBox.warning(
                    self, "Дубликат", "Сниппет с таким именем уже существует."
                )
                return
            if old_name in snippets_bucket:
                snippets_bucket[new_name] = snippets_bucket.pop(old_name)

        self._save_snippets_to_file()
        self._load_snippets()

    def _delete_item(self):
        item = self.snippet_tree_widget.currentItem()
        if not item:
            return

        is_category = self._is_category_tree_item(item)
        name = item.text(0)

        reply = QMessageBox.StandardButton.No
        if is_category:
            path = self._item_path(item)
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Вы уверены, что хотите удалить категорию '{name}' и все сниппеты в ней?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes and path:
                parent_path = path[:-1]
                container = self._get_category_children(parent_path, create=False)
                if container and path[-1] in container:
                    del container[path[-1]]
                    self._sync_parent_payload_flags(parent_path)
        else:
            category_path = self._item_path(item)
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Вы уверены, что хотите удалить сниппет '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                payload = self._get_category_payload(category_path)
                if payload:
                    snippets_bucket = payload.get("snippets", {})
                    if name in snippets_bucket:
                        del snippets_bucket[name]
                        if self._category_is_empty(payload):
                            parent_container = self._get_category_children(
                                category_path[:-1], create=False
                            )
                            if category_path and parent_container is not None:
                                parent_container.pop(category_path[-1], None)
                            self._sync_parent_payload_flags(category_path[:-1])
                        else:
                            payload["enabled"] = self._are_all_snippets_enabled(payload)
                            self._sync_parent_payload_flags(category_path)

        if reply == QMessageBox.StandardButton.Yes:
            self._save_snippets_to_file()
            self._load_snippets()
            self.statusBar().showMessage(f"Элемент '{name}' удален.", 4000)

    def _move_category_between_categories(self, source_path, target_path):
        """Перемещает категорию под нового родителя, выбранного через drag-and-drop."""
        source_path = tuple(source_path or ())
        target_path = tuple(target_path or ())
        if not source_path:
            return

        if target_path[: len(source_path)] == source_path:
            QMessageBox.warning(
                self,
                "Перемещение запрещено",
                "Категорию нельзя переместить внутрь неё самой или её дочерних элементов.",
            )
            return

        if source_path[:-1] == target_path:
            return

        source_parent_path = source_path[:-1]
        source_container = self._get_category_children(source_parent_path, create=False)
        if source_container is None:
            self.statusBar().showMessage(
                "Не удалось переместить: исходная категория не найдена.", 4000
            )
            return

        original_name = source_path[-1]
        moving_payload = source_container.get(original_name)
        if moving_payload is None:
            self.statusBar().showMessage(
                "Не удалось переместить: выбранная категория больше не существует.",
                4000,
            )
            return

        target_container = self._get_category_children(target_path, create=True)
        if target_container is None:
            QMessageBox.warning(
                self,
                "Сбой перемещения",
                "Не удалось создать целевую категорию.",
            )
            return

        category_name = original_name
        if category_name in target_container:
            category_name = self._prompt_new_category_name_for_move(
                category_name, target_path, target_container
            )
            if not category_name:
                return

        target_container[category_name] = moving_payload
        del source_container[original_name]

        self._sync_parent_payload_flags(source_parent_path)
        new_path = target_path + (category_name,)
        self._sync_parent_payload_flags(new_path)

        self._save_snippets_to_file()
        self._schedule_tree_refresh(
            focus_category_path=new_path,
            expand_category_path=target_path if target_path else None,
        )
        self.reload_listener_snippets()

        dest_label = self._format_category_path(target_path) or "корневой уровень"
        if category_name != original_name:
            info = (
                f"Категория '{original_name}' перенесена в '{dest_label}' "
                f"под именем '{category_name}'."
            )
        else:
            info = f"Категория '{category_name}' перенесена в '{dest_label}'."
        self.statusBar().showMessage(info, 4000)

    def _prompt_new_category_name_for_move(
        self, base_name, target_path, target_container
    ):
        """Запрашивает у пользователя уникальное имя при перемещении в категорию с конфликтом имен."""
        if target_container is None:
            return None

        def _suggestion():
            suffix = 2
            candidate = base_name
            while candidate in target_container:
                candidate = f"{base_name} ({suffix})"
                suffix += 1
            return candidate

        dest_label = self._format_category_path(target_path) or "корневой уровень"
        prompt_text = (
            f"Категория '{dest_label}' уже содержит подкатегорию "
            f"с именем '{base_name}'.\nВведите новое имя для перемещаемой категории."
        )
        suggested = _suggestion()

        while True:
            new_name, accepted = QInputDialog.getText(
                self,
                "Имя уже используется",
                prompt_text,
                text=suggested,
            )
            if not accepted:
                return None
            new_name = (new_name or "").strip()
            if not new_name:
                continue
            if new_name in target_container:
                QMessageBox.warning(
                    self,
                    "Конфликт имён",
                    "Выбранное имя уже занято в целевой категории.",
                )
                continue
            return new_name

    def _move_snippet_between_categories(self, source_path, abbr, target_path):
        """Переносит сниппет между категориями после перетаскивания."""
        source_payload = self._get_category_payload(source_path)
        source_snippets = source_payload.get("snippets", {}) if source_payload else {}
        snippet_entry = source_snippets.get(abbr)
        if snippet_entry is None:
            self.statusBar().showMessage("Ошибка: сниппет не найден для переноса.", 4000)
            return

        target_payload = self._get_category_payload(target_path, create=True)
        target_bucket = target_payload.setdefault("snippets", {})
        if abbr in target_bucket:
            QMessageBox.warning(
                self,
                "Предупреждение",
                f"В категории '{self._format_category_path(target_path)}' "
                f"уже есть сниппет '{abbr}'.",
            )
            return

        target_bucket[abbr] = snippet_entry
        del source_snippets[abbr]
        if source_payload:
            if self._category_is_empty(source_payload):
                parent_container = self._get_category_children(
                    source_path[:-1], create=False
                )
                if source_path and parent_container is not None:
                    parent_container.pop(source_path[-1], None)
                self._sync_parent_payload_flags(source_path[:-1])
            else:
                source_payload["enabled"] = self._are_all_snippets_enabled(source_payload)
                self._sync_parent_payload_flags(source_path)
        target_payload["enabled"] = self._are_all_snippets_enabled(target_payload)
        self._sync_parent_payload_flags(target_path)

        self._save_snippets_to_file()
        self._schedule_tree_refresh(
            focus_category_path=target_path, focus_snippet=abbr
        )
        self.reload_listener_snippets()
        self.statusBar().showMessage(
            f"Сниппет '{abbr}' перенесён в категорию "
            f"'{self._format_category_path(target_path)}'.",
            4000,
        )
